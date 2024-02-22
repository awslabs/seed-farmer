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
from typing import Any, Dict, Optional, Tuple, cast

import boto3
import botocore.exceptions
from boto3 import Session

import seedfarmer
import seedfarmer.errors

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
        proxies=setup_proxies(),
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


def boto3_client(
    service_name: str,
    session: Optional[Session] = None,
    region_name: Optional[str] = None,
    profile: Optional[str] = None,
    aws_access_key_id: Optional[str] = None,
    aws_secret_access_key: Optional[str] = None,
    aws_session_token: Optional[str] = None,
) -> boto3.client:
    if aws_access_key_id and aws_secret_access_key and aws_session_token:
        return create_new_session_with_creds(
            aws_access_key_id, aws_secret_access_key, aws_session_token, region_name
        ).client(service_name=service_name, use_ssl=True, config=get_botocore_config())
    elif not session:
        return create_new_session(region_name, profile).client(
            service_name=service_name, use_ssl=True, config=get_botocore_config()
        )
    else:
        return session.client(service_name=service_name, use_ssl=True, config=get_botocore_config())


def boto3_resource(
    service_name: str,
    session: Optional[Session] = None,
    region_name: Optional[str] = None,
    profile: Optional[str] = None,
) -> boto3.client:
    if not session:
        return create_new_session(region_name=region_name, profile=profile).resource(
            service_name=service_name, use_ssl=True, config=get_botocore_config()
        )
    else:
        return session.resource(service_name=service_name, use_ssl=True, config=get_botocore_config())


def get_region(session: Optional[Session] = None, profile: Optional[str] = None) -> str:
    sess = session if session else create_new_session(profile=profile)
    if sess.region_name is None:
        raise seedfarmer.errors.InvalidConfigurationError(
            "It is not possible to infer AWS REGION from your environment."
        )
    return str(sess.region_name)


def _call_sts(session: Optional[Session] = None, profile: Optional[str] = None) -> Dict[str, Any]:
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


def get_sts_identity_info(session: Optional[Session] = None, profile: Optional[str] = None) -> Tuple[str, str, str]:
    sts_info = _call_sts(session=session, profile=profile)
    return cast(
        Tuple[str, str, str], (sts_info.get("Account"), sts_info.get("Arn"), str(sts_info.get("Arn")).split(":")[1])
    )
