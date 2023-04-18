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

import json
from typing import Any, Dict, List, Optional, cast

from boto3 import Session

from seedfarmer.services._service_utils import boto3_client, get_account_id, get_region


def get_secrets_manager_value(name: str, session: Optional[Session] = None) -> Dict[str, Any]:
    client = boto3_client(service_name="secretsmanager", session=session)
    secret_arn = f"arn:aws:secretsmanager:{get_region(session=session)}:{get_account_id(session=session)}:secret:{name}"
    json_str: str = client.get_secret_value(SecretId=secret_arn).get("SecretString")
    return cast(Dict[str, Any], json.loads(json_str))


def list_secret_version_ids(name: str, session: Optional[Session] = None) -> Optional[List[Any]]:
    client = boto3_client(service_name="secretsmanager", session=session)
    secret_arn = f"arn:aws:secretsmanager:{get_region(session=session)}:{get_account_id(session=session)}:secret:{name}"
    resp = client.list_secret_version_ids(SecretId=secret_arn)
    return client.list_secret_version_ids(SecretId=secret_arn)["Versions"] if resp else None
