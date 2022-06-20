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
from typing import Any, Dict, cast

from seedfarmer.services._service_utils import boto3_client, get_account_id, get_region


def get_secret_secrets_manager(name: str) -> Dict[str, Any]:
    client = boto3_client(service_name="secretsmanager")
    secret_arn = f"arn:aws:secretsmanager:{get_region()}:{get_account_id()}:secret:{name}"
    json_str: str = client.get_secret_value(SecretId=secret_arn).get("SecretString")
    return cast(Dict[str, Any], json.loads(json_str))
