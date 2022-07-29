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
import math
from typing import Any, List, Optional

import boto3
import botocore.exceptions

import seedfarmer

_logger: logging.Logger = logging.getLogger(__name__)


def chunkify(lst: List[Any], num_chunks: int = 1, max_length: Optional[int] = None) -> List[List[Any]]:
    num: int = num_chunks if max_length is None else int(math.ceil((float(len(lst)) / float(max_length))))
    return [lst[i : i + num] for i in range(0, len(lst), num)]  # noqa: E203


def get_botocore_config() -> botocore.config.Config:
    return botocore.config.Config(
        retries={"max_attempts": 5},
        connect_timeout=10,
        max_pool_connections=10,
        user_agent_extra=f"seedfarmer/{seedfarmer.__version__}",
    )


def boto3_client(service_name: str) -> boto3.client:
    return boto3.Session().client(service_name=service_name, use_ssl=True, config=get_botocore_config())


def boto3_resource(service_name: str) -> boto3.client:
    return boto3.Session().resource(service_name=service_name, use_ssl=True, config=get_botocore_config())


def get_region() -> str:
    session = boto3.Session()
    if session.region_name is None:
        raise ValueError("It is not possible to infer AWS REGION from your environment.")
    return str(session.region_name)


def get_account_id() -> str:
    try:
        return str(boto3_client(service_name="sts").get_caller_identity().get("Account"))
    except botocore.exceptions.NoCredentialsError as e:
        _logger.error(f"ERROR: {e}")
        from seedfarmer.output_utils import print_bolded

        print_bolded("Please make sure you have valid AWS Credentials", color="red")
        exit(1)
    except botocore.exceptions.ClientError as e:
        _logger.error(f"ERROR: {e}")
        from seedfarmer.output_utils import print_bolded

        print_bolded("Please make sure you have a valid AWS Session", color="red")
        exit(1)
