#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License").
#    You may not use this file except in compliance with the License.
#    You may obtain a copy of the License at
#
#        http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS,
#    WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#    See the License for the specific language governing permissions and
#    limitations under the License.

import logging
import os
import random
import time
from typing import TYPE_CHECKING, Any, Callable, Dict, Literal, Optional, Tuple, Union, cast, overload

import boto3
import botocore.config
import botocore.exceptions
from boto3 import Session
from botocore.auth import SigV4Auth
from botocore.awsrequest import AWSRequest
from botocore.credentials import Credentials

import seedfarmer
import seedfarmer.errors

if TYPE_CHECKING:
    from boto3.resources.base import ServiceResource
    from botocore.client import BaseClient
    from mypy_boto3_cloudformation.client import CloudFormationClient
    from mypy_boto3_codebuild import CodeBuildClient
    from mypy_boto3_iam import IAMClient, IAMServiceResource
    from mypy_boto3_logs.client import CloudWatchLogsClient
    from mypy_boto3_s3 import S3Client, S3ServiceResource
    from mypy_boto3_secretsmanager import SecretsManagerClient
    from mypy_boto3_ssm import SSMClient
    from mypy_boto3_sts.client import STSClient

_logger: logging.Logger = logging.getLogger(__name__)


def setup_proxies() -> Dict[str, Optional[str]]:
    proxies = {}
    proxies["http"] = os.getenv("HTTP_PROXY", None)
    proxies["https"] = os.getenv("HTTPS_PROXY", None)
    _logger.debug("Proxies Configured: %s", proxies)
    return proxies


def get_botocore_config() -> botocore.config.Config:
    return botocore.config.Config(
        retries={"max_attempts": 5},
        connect_timeout=10,
        max_pool_connections=10,
        user_agent_extra=f"seedfarmer/{seedfarmer.__version__}",
        proxies=setup_proxies(),  # type: ignore[arg-type]
    )


def create_new_session(region_name: Optional[str] = None, profile: Optional[str] = None) -> Session:
    return Session(region_name=region_name, profile_name=profile)


def create_new_session_with_creds(
    aws_access_key_id: str, aws_secret_access_key: str, aws_session_token: str, region_name: Optional[str] = None
) -> Session:
    return boto3.Session(
        aws_access_key_id=aws_access_key_id,
        aws_secret_access_key=aws_secret_access_key,
        aws_session_token=aws_session_token,
        region_name=region_name,
    )


@overload
def boto3_client(
    service_name: Literal["codebuild"],
    session: Optional[Union[Callable[[], Session], Session]] = ...,
    region_name: Optional[str] = ...,
    profile: Optional[str] = ...,
    aws_access_key_id: Optional[str] = ...,
    aws_secret_access_key: Optional[str] = ...,
    aws_session_token: Optional[str] = ...,
) -> "CodeBuildClient": ...


@overload
def boto3_client(
    service_name: Literal["iam"],
    session: Optional[Union[Callable[[], Session], Session]] = ...,
    region_name: Optional[str] = ...,
    profile: Optional[str] = ...,
    aws_access_key_id: Optional[str] = ...,
    aws_secret_access_key: Optional[str] = ...,
    aws_session_token: Optional[str] = ...,
) -> "IAMClient": ...


@overload
def boto3_client(
    service_name: Literal["s3"],
    session: Optional[Union[Callable[[], Session], Session]] = ...,
    region_name: Optional[str] = ...,
    profile: Optional[str] = ...,
    aws_access_key_id: Optional[str] = ...,
    aws_secret_access_key: Optional[str] = ...,
    aws_session_token: Optional[str] = ...,
) -> "S3Client": ...


@overload
def boto3_client(
    service_name: Literal["secretsmanager"],
    session: Optional[Union[Callable[[], Session], Session]] = ...,
    region_name: Optional[str] = ...,
    profile: Optional[str] = ...,
    aws_access_key_id: Optional[str] = ...,
    aws_secret_access_key: Optional[str] = ...,
    aws_session_token: Optional[str] = ...,
) -> "SecretsManagerClient": ...


@overload
def boto3_client(
    service_name: Literal["ssm"],
    session: Optional[Union[Callable[[], Session], Session]] = ...,
    region_name: Optional[str] = ...,
    profile: Optional[str] = ...,
    aws_access_key_id: Optional[str] = ...,
    aws_secret_access_key: Optional[str] = ...,
    aws_session_token: Optional[str] = ...,
) -> "SSMClient": ...


@overload
def boto3_client(
    service_name: Literal["sts"],
    session: Optional[Union[Callable[[], Session], Session]] = ...,
    region_name: Optional[str] = ...,
    profile: Optional[str] = ...,
    aws_access_key_id: Optional[str] = ...,
    aws_secret_access_key: Optional[str] = ...,
    aws_session_token: Optional[str] = ...,
) -> "STSClient": ...


@overload
def boto3_client(
    service_name: Literal["cloudformation"],
    session: Optional[Union[Callable[[], Session], Session]] = ...,
    region_name: Optional[str] = ...,
    profile: Optional[str] = ...,
    aws_access_key_id: Optional[str] = ...,
    aws_secret_access_key: Optional[str] = ...,
    aws_session_token: Optional[str] = ...,
) -> "CloudFormationClient": ...


@overload
def boto3_client(
    service_name: Literal["logs"],
    session: Optional[Union[Callable[[], Session], Session]] = ...,
    region_name: Optional[str] = ...,
    profile: Optional[str] = ...,
    aws_access_key_id: Optional[str] = ...,
    aws_secret_access_key: Optional[str] = ...,
    aws_session_token: Optional[str] = ...,
) -> "CloudWatchLogsClient": ...


@overload
def boto3_client(
    service_name: str,
    session: Optional[Union[Callable[[], Session], Session]] = ...,
    region_name: Optional[str] = ...,
    profile: Optional[str] = ...,
    aws_access_key_id: Optional[str] = ...,
    aws_secret_access_key: Optional[str] = ...,
    aws_session_token: Optional[str] = ...,
) -> "BaseClient": ...


def boto3_client(
    service_name: str,
    session: Optional[Union[Callable[[], Session], Session]] = None,
    region_name: Optional[str] = None,
    profile: Optional[str] = None,
    aws_access_key_id: Optional[str] = None,
    aws_secret_access_key: Optional[str] = None,
    aws_session_token: Optional[str] = None,
) -> "BaseClient":
    if aws_access_key_id and aws_secret_access_key and aws_session_token:
        return create_new_session_with_creds(  # type: ignore[call-overload,no-any-return]
            aws_access_key_id, aws_secret_access_key, aws_session_token, region_name
        ).client(service_name=service_name, use_ssl=True, config=get_botocore_config())
    elif not session:
        return create_new_session(region_name, profile).client(  # type: ignore[call-overload,no-any-return]
            service_name=service_name, use_ssl=True, config=get_botocore_config()
        )
    else:
        if isinstance(session, Session):
            return session.client(service_name=service_name, use_ssl=True, config=get_botocore_config())  # type: ignore
        else:
            raise TypeError(f"Expected boto3.Session instance, got {type(session)}")


@overload
def boto3_resource(
    service_name: Literal["iam"],
    ssession: Optional[Union[Callable[[], Session], Session]] = ...,
    region_name: Optional[str] = ...,
    profile: Optional[str] = ...,
) -> "IAMServiceResource": ...


@overload
def boto3_resource(
    service_name: Literal["s3"],
    ssession: Optional[Union[Callable[[], Session], Session]] = ...,
    region_name: Optional[str] = ...,
    profile: Optional[str] = ...,
) -> "S3ServiceResource": ...


@overload
def boto3_resource(
    service_name: str,
    session: Optional[Union[Callable[[], Session], Session]] = ...,
    region_name: Optional[str] = ...,
    profile: Optional[str] = ...,
) -> "ServiceResource": ...


def boto3_resource(  # type: ignore[misc]
    service_name: str,
    session: Optional[Union[Callable[[], Session], Session]] = None,
    region_name: Optional[str] = None,
    profile: Optional[str] = None,
) -> "ServiceResource":
    if not session:
        return create_new_session(region_name=region_name, profile=profile).resource(  # type: ignore[no-any-return]
            service_name=service_name, use_ssl=True, config=get_botocore_config()
        )  # type: ignore[call-overload]
    else:
        if callable(session):
            session = session()
        return session.resource(  # type: ignore[no-any-return]
            service_name=service_name,
            use_ssl=True,
            config=get_botocore_config(),
        )  # type: ignore[call-overload]


def get_region(session: Optional[Union[Callable[[], Session], Session]] = None, profile: Optional[str] = None) -> str:
    sess = session() if callable(session) else (session or create_new_session(profile=profile))
    if sess.region_name is None:
        raise seedfarmer.errors.InvalidConfigurationError(
            "It is not possible to infer AWS REGION from your environment."
        )
    return str(sess.region_name)


def _call_sts(
    session: Optional[Union[Callable[[], Session], Session]] = None, profile: Optional[str] = None
) -> Dict[str, Any]:
    try:
        if not session:
            return cast(Dict[str, Any], boto3_client(service_name="sts", profile=profile).get_caller_identity())
        else:
            return cast(Dict[str, Any], boto3_client(service_name="sts", session=session).get_caller_identity())
    except botocore.exceptions.NoCredentialsError as e:
        _logger.error(f"ERROR: {e}")
        from seedfarmer.output_utils import print_bolded

        print_bolded("Please make sure you have valid AWS Credentials", color="red")
        raise e

    except botocore.exceptions.ClientError as e:
        _logger.error(f"ERROR: {e}")
        from seedfarmer.output_utils import print_bolded

        print_bolded("Please make sure you have a valid AWS Session", color="red")
        raise e


def get_sts_identity_info(
    session: Optional[Union[Callable[[], Session], Session]] = None, profile: Optional[str] = None
) -> Tuple[str, str, str]:
    sts_info = _call_sts(session=session, profile=profile)
    return cast(
        Tuple[str, str, str], (sts_info.get("Account"), sts_info.get("Arn"), str(sts_info.get("Arn")).split(":")[1])
    )


def create_signed_request(
    endpoint: str,
    session: Session,
    credentials: Credentials,
    service: str = "s3",
    region: Optional[str] = None,
    method: Optional[str] = "GET",
    params: Optional[Dict[str, Any]] = None,
    headers: Optional[Dict[str, Any]] = None,
) -> AWSRequest:
    region = get_region(session) if not region else region
    auth = SigV4Auth(credentials, service, region)

    request = AWSRequest(method=method, url=endpoint, params=params, data=None, headers=headers)
    auth.add_auth(request)

    return request


def try_it(
    f: Callable[..., Any],
    ex: Any,
    base: float = 1.0,
    max_num_tries: int = 3,
    **kwargs: Any,
) -> Any:
    """Run function with decorrelated Jitter.

    Reference: https://aws.amazon.com/blogs/architecture/exponential-backoff-and-jitter/
    """
    delay: float = base
    for i in range(max_num_tries):
        try:
            return f(**kwargs)
        except ex as exception:
            if i == (max_num_tries - 1):
                raise exception
            delay = random.uniform(base, delay * 3)
            _logger.error(
                "Retrying %s | Fail number %s/%s | Exception: %s",
                f,
                i + 1,
                max_num_tries,
                exception,
            )
            time.sleep(delay)
