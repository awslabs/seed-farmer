import logging
import threading
from abc import abstractmethod, abstractproperty
from threading import Thread
from time import sleep
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Tuple, cast

import botocore.exceptions
from boto3 import Session
from botocore.credentials import Credentials

import seedfarmer.errors
from seedfarmer.services import boto3_client, create_new_session, create_new_session_with_creds, get_sts_identity_info
from seedfarmer.utils import get_deployment_role_arn, get_toolchain_role_arn, get_toolchain_role_name

if TYPE_CHECKING:
    from mypy_boto3_sts.type_defs import AssumeRoleResponseTypeDef

_logger: logging.Logger = logging.getLogger(__name__)


class SingletonMeta(type):
    """
    This is a thread-safe implementation of Singleton.
    """

    _instances: Dict[Any, Any] = {}

    _lock: threading.Lock = threading.Lock()

    def __call__(cls, *args: List[Any], **kwargs: Dict[Any, Any]) -> Any:
        """
        Possible changes to the value of the `__init__` argument do not affect
        the returned instance.
        """
        with cls._lock:
            if cls not in cls._instances:
                instance = super().__call__(*args, **kwargs)
                cls._instances[cls] = instance
        return cls._instances[cls]


class ISessionManager(object):
    @abstractmethod
    def get_or_create(
        self,
        *,
        project_name: Optional[str] = None,
        region_name: Optional[str] = None,
        toolchain_region: Optional[str] = None,
        qualifier: Optional[str] = None,
        profile: Optional[str] = None,
        enable_reaper: bool = False,
        **kwargs: Optional[Any],
    ) -> Any: ...

    @abstractproperty
    def toolchain_session(self) -> Session: ...

    @abstractmethod
    def get_deployment_session(self, account_id: str, region_name: str) -> Session: ...

    @abstractmethod
    def get_toolchain_credentials(self) -> Credentials: ...


class SessionManager(ISessionManager, metaclass=SingletonMeta):
    TOOLCHAIN_KEY: str = "toolchain"
    SESSION: str = "session"
    ROLE: str = "role"
    sessions: Dict[str, Dict[str, Any]] = {}

    config: Dict[Any, Any] = {}
    created: bool = False
    reaper: Thread = None  # type: ignore
    reaper_interval: int = 900  # every 15 minutes

    def __init__(self) -> None:
        super().__init__()

    def get_or_create(
        self,
        *,
        project_name: Optional[str] = None,
        region_name: Optional[str] = None,
        profile: Optional[str] = None,
        toolchain_region: Optional[str] = None,
        qualifier: Optional[str] = None,
        reaper_interval: Optional[int] = None,
        enable_reaper: bool = False,
        **kwargs: Optional[Any],
    ) -> ISessionManager:
        if not self.created:
            if project_name is None:
                raise seedfarmer.errors.InvalidConfigurationError(
                    "A 'project_name' is required for first time initialization of the SessionManager"
                )
            self.config["project_name"] = project_name
            self.config["region_name"] = region_name
            self.config["profile"] = profile
            self.config["toolchain_region"] = toolchain_region
            self.config["qualifier"] = qualifier if qualifier else None
            self.config = {**self.config, **kwargs}
            self.toolchain_role_name = get_toolchain_role_name(project_name, cast(str, qualifier))

            if reaper_interval is not None:
                self.reaper_interval = reaper_interval

            if enable_reaper and (not self.reaper or not self.reaper.is_alive()):
                self._setup_reaper()

            self._check_for_toolchain()
            self.created = True
        return self

    @property
    def toolchain_session(self) -> Session:
        if not self.created:
            raise seedfarmer.errors.InvalidConfigurationError(
                "The SessionManager object was never properly created...)"
            )
        self._check_for_toolchain()
        return self.sessions[self.TOOLCHAIN_KEY][self.SESSION]  # type: ignore[no-any-return]

    def get_toolchain_credentials(self) -> Credentials:
        if not self.created:
            raise seedfarmer.errors.InvalidConfigurationError(
                "The SessionManager object was never properly created...)"
            )

        toolchain_role = self.sessions[self.TOOLCHAIN_KEY][self.ROLE]
        creds = Credentials(
            access_key=toolchain_role["Credentials"]["AccessKeyId"],
            secret_key=toolchain_role["Credentials"]["SecretAccessKey"],
            token=toolchain_role["Credentials"]["SessionToken"],
        )
        return creds

    def get_deployment_session(self, account_id: str, region_name: str) -> Session:
        session_key = f"{account_id}-{region_name}"
        project_name = self.config["project_name"]
        qualifier = self.config.get("qualifier") if self.config.get("qualifier") else None
        toolchain_region = self.config.get("toolchain_region")
        if not self.created:
            raise seedfarmer.errors.InvalidConfigurationError("The SessionManager object was never properly created...")
        if session_key not in self.sessions.keys():
            _logger.info(f"Creating Session for {session_key}")
            self._check_for_toolchain()
            toolchain_role = self.sessions[self.TOOLCHAIN_KEY][self.ROLE]
            # the boto sessions are not thread safe, so create a new one for the toolchain role every time to be sure
            sts_toolchain_client = boto3_client(
                service_name="sts",
                aws_access_key_id=toolchain_role["Credentials"]["AccessKeyId"],
                aws_secret_access_key=toolchain_role["Credentials"]["SecretAccessKey"],
                aws_session_token=toolchain_role["Credentials"]["SessionToken"],
                region_name=toolchain_region if toolchain_region else region_name,
            )
            partition = sts_toolchain_client.get_caller_identity()["Arn"].split(":")[1]
            deployment_role_arn = get_deployment_role_arn(
                partition=partition,
                deployment_account_id=account_id,
                project_name=project_name,
                qualifier=cast(str, qualifier),
            )
            _logger.debug(
                f"""The assumed toolchain role {toolchain_role['AssumedRoleUser']['Arn']} will
                 try and assume the deployment role: {deployment_role_arn}"""
            )
            try:
                deployment_role = sts_toolchain_client.assume_role(
                    RoleArn=deployment_role_arn,
                    RoleSessionName="deployment_role",
                )
            except botocore.exceptions.ClientError as ce:
                raise seedfarmer.errors.InvalidSessionError(
                    f"""
                {ce}
                The toolchain role cannot assume a deployment role for this account / region mapping.
                Make sure that the toolchain role is in the trust policy of the deployment role...
                   (HINT: if not, your seedfarmer bootstrap is incorrect. Use the SeedFarmer CLI to bootstrap.)
                Make sure that the account id is correct in your targetAccountMappings of the deployment manifest.
                   (HINT: look at the arn of the deployment role...the account id is REALLY important to be correct.
                   This is gotten from the deployment manifest under the targetAccountMappings section.)
                """
                )
            deployment_session = create_new_session_with_creds(
                aws_access_key_id=deployment_role["Credentials"]["AccessKeyId"],
                aws_secret_access_key=deployment_role["Credentials"]["SecretAccessKey"],
                aws_session_token=deployment_role["Credentials"]["SessionToken"],
                region_name=region_name,
            )
            self.sessions[session_key] = {self.SESSION: deployment_session, self.ROLE: deployment_role}
            return deployment_session
        else:
            return self.sessions[session_key][self.SESSION]  # type: ignore[no-any-return]

    # These methods below should not be called outside of this class

    def _check_for_toolchain(self) -> None:
        if self.TOOLCHAIN_KEY not in self.sessions.keys():
            _logger.info("Creating toolchain session")
            session, role = self._get_toolchain()
            self.sessions = {self.TOOLCHAIN_KEY: {self.SESSION: session, self.ROLE: role}}

    def _get_toolchain(self) -> Tuple[Session, "AssumeRoleResponseTypeDef"]:
        region_name = self.config.get("region_name")
        profile_name = self.config.get("profile")
        project_name = self.config.get("project_name")
        qualifier = self.config.get("qualifier") if self.config.get("qualifier") else None
        toolchain_region = self.config.get("toolchain_region")
        _logger.debug(
            f"""Creating a local session with the following info passed in:
                      region_name = {region_name}
                      profile_name = {profile_name}
                      project_name = {project_name}
                      qualifier = {qualifier}

                      NOTE: if not set here, the active environment parameters are used to create a new AWS session
                            much like how the AWS CLI operates.
                      """
        )
        user_session = create_new_session(region_name=region_name, profile=profile_name)
        user_account_id, _, partition = get_sts_identity_info(session=user_session)
        toolchain_role_arn = get_toolchain_role_arn(
            partition=partition,
            toolchain_account_id=user_account_id,
            project_name=cast(str, project_name),
            qualifier=cast(str, qualifier),
        )
        _logger.debug(
            f"""The active user session will assume the toolchain role
                      arn = {toolchain_role_arn}
                      toolchain_region = {toolchain_region}
                      """
        )
        user_client = boto3_client(service_name="sts", session=user_session)
        try:
            toolchain_role = user_client.assume_role(
                RoleArn=toolchain_role_arn,
                RoleSessionName="toolchainrole",
            )
        except botocore.exceptions.ClientError as ce:
            raise seedfarmer.errors.InvalidSessionError(
                f"""
            {ce}
            The session used to call SeedFarmer is not permitted to assume the toolchain role.
            Verify the user tied to your active session is in the trust policy of the toolchain role
            or use a session that DOES have that user.
            """
            )
        toolchain_session = create_new_session_with_creds(
            aws_access_key_id=toolchain_role["Credentials"]["AccessKeyId"],
            aws_secret_access_key=toolchain_role["Credentials"]["SecretAccessKey"],
            aws_session_token=toolchain_role["Credentials"]["SessionToken"],
            region_name=toolchain_region if toolchain_region else region_name,
        )

        return toolchain_session, toolchain_role

    def _setup_reaper(self) -> None:
        _logger.info("Starting Session Reaper")
        t = Thread(target=self._reap_sessions, args=(self.reaper_interval,), daemon=True, name="SessionReaper")
        t.start()
        self.reaper = t

    def _reap_sessions(self, interval: int) -> None:
        _logger.debug("Reaper Is Set")
        while True:
            sleep(interval)
            _logger.info(f"Reaping Sessions - sleeping for {interval} seconds")
            self.sessions = {}
