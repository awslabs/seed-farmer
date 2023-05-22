import logging
import threading
from abc import abstractmethod, abstractproperty
from threading import Thread
from time import sleep
from typing import Any, Dict, List, Optional, Tuple

from boto3 import Session

import seedfarmer.errors
from seedfarmer.services import boto3_client, create_new_session, create_new_session_with_creds, get_account_id

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
        profile: Optional[str] = None,
        enable_reaper: bool = False,
        **kwargs: Optional[Any],
    ) -> Any:
        ...

    @abstractproperty
    def toolchain_session(self) -> Session:
        ...

    @abstractmethod
    def get_deployment_session(self, account_id: str, region_name: str) -> Session:
        ...


class SessionManager(ISessionManager, metaclass=SingletonMeta):
    TOOLCHAIN_KEY: str = "toolchain"
    SESSION: str = "session"
    ROLE: str = "role"
    sessions: Dict[Any, Any] = {}

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
            self.config = {**self.config, **kwargs}
            self.toolchain_role_name = f"seedfarmer-{project_name}-toolchain-role"

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
        return self.sessions[self.TOOLCHAIN_KEY][self.SESSION]

    def get_deployment_session(self, account_id: str, region_name: str) -> Session:
        session_key = f"{account_id}-{region_name}"
        project_name = self.config["project_name"]
        if not self.created:
            raise seedfarmer.errors.InvalidConfigurationError("The SessionManager object was never properly created...")
        if session_key not in self.sessions.keys():
            _logger.info(f"Creating Session for {session_key}")
            self._check_for_toolchain()
            toolchain_role = self.sessions[self.TOOLCHAIN_KEY][self.ROLE]
            deployment_role_arn = f"arn:aws:iam::{account_id}:role/seedfarmer-{project_name}-deployment-role"
            # the boto sessions are not thread safe, so create a new one for the toolchain role every time to be sure
            sts_toolchain_client = boto3_client(
                service_name="sts",
                aws_access_key_id=toolchain_role["Credentials"]["AccessKeyId"],
                aws_secret_access_key=toolchain_role["Credentials"]["SecretAccessKey"],
                aws_session_token=toolchain_role["Credentials"]["SessionToken"],
            )
            deployment_role = sts_toolchain_client.assume_role(
                RoleArn=deployment_role_arn,
                RoleSessionName="deployment_role",
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
            return self.sessions[session_key][self.SESSION]

    # These methods below should not be called outside of this class

    def _check_for_toolchain(self) -> None:
        if self.TOOLCHAIN_KEY not in self.sessions.keys():
            _logger.info("Creating toolchain session")
            session, role = self._get_toolchain()
            self.sessions = {self.TOOLCHAIN_KEY: {self.SESSION: session, self.ROLE: role}}

    def _get_toolchain(self) -> Tuple[Session, Dict[Any, Any]]:
        region_name = self.config.get("region_name")
        profile_name = self.config.get("profile")
        toolchain_region = self.config.get("toolchain_region")
        _logger.debug("Getting toolchain role")
        user_session = create_new_session(region_name=region_name, profile=profile_name)
        user_client = boto3_client(service_name="sts", session=user_session)
        toolchain_account_id = get_account_id(user_session)

        toolchain_role_arn = f"arn:aws:iam::{toolchain_account_id}:role/{self.toolchain_role_name}"
        toolchain_role = user_client.assume_role(
            RoleArn=toolchain_role_arn,
            RoleSessionName="toolchainrole",
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
