import logging
import threading
from threading import Thread
from time import sleep
from typing import Any, Dict, List, Optional, Tuple

import boto3
import botocore
from boto3 import Session

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


class SessionManager(metaclass=SingletonMeta):
    # Example Calling:
    # sm = SessionManager()\
    # .configure(project_name=PROJECT)\
    # .create(profile='myprorilename')

    TOOLCHAIN_KEY: str = "toolchain"
    SESSION: str = "session"
    ROLE: str = "role"
    sessions: Dict[Any, Any] = {}

    config: Dict[Any, Any] = {}
    toolchain_create_params = {}
    created: bool = False
    reaper: Thread = None
    reaperInterval: int = 3000  # every 50 minutes

    def configure(self, project_name: str, **kwargs) -> SingletonMeta:
        self.config["project_name"] = project_name
        self.config = {**self.config, **kwargs}
        return self

    def create(self, region_name: Optional[str] = None, profile: Optional[str] = None) -> SingletonMeta:
        p_name = self.config["project_name"] if self.config.get("project_name") else "sf"
        self.toolchain_create_params = {"region_name": region_name, "profile": profile}
        self.toolchain_role_name = f"seedfarmer-{p_name}-toolchain-role"
        if not self.reaper or not self.reaper.is_alive():
            self._setup_reaper()
        if not self.TOOLCHAIN_KEY in self.sessions.keys():
            session, role = self._get_toolchain(region_name, profile)
            self.sessions = {self.TOOLCHAIN_KEY: {self.SESSION: session, self.ROLE: role}}
            self.created = True
        else:
            _logger.info("Toolchain Already Created")
        return self

    def get_toolchain_session(self) -> Session:
        if not self.sessions or not self.sessions[self.TOOLCHAIN_KEY][self.SESSION]:
            self.create(
                region_name=self.toolchain_create_params["region_name"]
                if self.toolchain_create_params["region_name"]
                else None,
                profile=self.toolchain_create_params["profile"] if self.toolchain_create_params["profile"] else None,
            )
        return self.sessions[self.TOOLCHAIN_KEY][self.SESSION]

    def get_deployment_session(self, account_id: str, region_name: str) -> Session:
        session_key = f"{account_id}-{region_name}"
        p_name = self.config["project_name"] if self.config.get("project_name") else "NA"
        if not self.created:
            raise RuntimeError("The SessionManager object was never properly created...call .create()")
        if not session_key in self.sessions.keys():
            _logger.info(f"Creating Session for {session_key}")
            toolchain_session = self.sessions[self.TOOLCHAIN_KEY][self.SESSION]
            deployment_role_arn = f"arn:aws:iam::{account_id}:role/seedfarmer-{p_name}-deployment-role"
            sts_toolchain_client = toolchain_session.client("sts")
            deployment_role = sts_toolchain_client.assume_role(
                RoleArn=deployment_role_arn,
                RoleSessionName="deployment_role",
            )
            deployment_session = boto3.Session(
                aws_access_key_id=deployment_role["Credentials"]["AccessKeyId"],
                aws_secret_access_key=deployment_role["Credentials"]["SecretAccessKey"],
                aws_session_token=deployment_role["Credentials"]["SessionToken"],
                region_name=region_name,
            )
            self.sessions[session_key] = {self.SESSION: deployment_session, self.ROLE: deployment_role}
            return deployment_session
        else:
            _logger.info(f"Session Found for {session_key}")
            return self.sessions[session_key][self.SESSION]

    # These methods below should not be called outside of this class

    def _get_toolchain(
        self,
        region_name: Optional[str],
        profile_name: Optional[str],
    ) -> Tuple[Session, Dict[Any, Any]]:

        _logger.info("Getting toolchain role")
        user_session = boto3.Session(region_name=region_name, profile_name=profile_name if profile_name else None)
        user_client = user_session.client("sts", use_ssl=True, config=self._get_botocore_config())
        toolchain_account_id = user_client.get_caller_identity().get("Account")

        toolchain_role_arn = f"arn:aws:iam::{toolchain_account_id}:role/{self.toolchain_role_name}"
        toolchain_role = user_client.assume_role(
            RoleArn=toolchain_role_arn,
            RoleSessionName="toolchainrole",
        )
        toolchain_session = boto3.Session(
            aws_access_key_id=toolchain_role["Credentials"]["AccessKeyId"],
            aws_secret_access_key=toolchain_role["Credentials"]["SecretAccessKey"],
            aws_session_token=toolchain_role["Credentials"]["SessionToken"],
            region_name=region_name if region_name else None,
        )

        return toolchain_session, toolchain_role

    def _setup_reaper(self):
        _logger.info("Starting Session Reaper")
        t = Thread(target=self._reap_sessions, args=(self.reaperInterval,), daemon=True, name="SessionReaper")
        t.start()
        self.reaper = t

    def _reap_sessions(self, interval) -> None:
        _logger.info("Reaper Is Set")
        while True:
            sleep(interval)
            _logger.info(f"Reaping Sessions - sleeping for {interval} seconds")
            self.sessions = {}

    def _get_botocore_config(self) -> botocore.config.Config:
        return botocore.config.Config(
            retries={"max_attempts": 5},
            connect_timeout=10,
            max_pool_connections=10,
            # user_agent_extra=f"seedfarmer/{seedfarmer.__version__}",
        )

    def _fetch_session_obj(self):
        return self.sessions

    def _fetch_toolchain_session(self):
        if not self.TOOLCHAIN_KEY in self.sessions.keys():
            _logger.error("The toolchain session is not establshed....go create one")
        else:
            return self.sessions[self.TOOLCHAIN_KEY][self.SESSION]
