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
import logging
import time
from typing import Any, Dict, List, Optional, cast

from seedfarmer.services._service_utils import boto3_client

_logger: logging.Logger = logging.getLogger(__name__)


def put_parameter(name: str, obj: Dict[str, Any]) -> None:
    client = boto3_client(service_name="ssm")
    retries = 3
    while retries > 0:
        try:
            client.put_parameter(
                Name=name,
                Value=str(json.dumps(obj=obj, sort_keys=True)),
                Overwrite=True,
                Tier="Intelligent-Tiering",
                Type="String",
            )
            break
        except client.exceptions.TooManyUpdates as err:
            if retries < 3:
                _logger.warning("An error occurred (TooManyUpdates) when calling the PutParameter operation. Retrying")
                retries -= 1
                time.sleep(2 ** (4 - retries))

            if retries == 0:
                raise Exception(err)


def get_parameter(name: str) -> Dict[str, Any]:
    client = boto3_client(service_name="ssm")
    json_str: str = client.get_parameter(Name=name)["Parameter"]["Value"]
    return cast(Dict[str, Any], json.loads(json_str))


def get_parameter_if_exists(name: str) -> Optional[Dict[str, Any]]:
    client = boto3_client(service_name="ssm")
    try:
        json_str: str = client.get_parameter(Name=name)["Parameter"]["Value"]
    except client.exceptions.ParameterNotFound:
        return None
    return cast(Dict[str, Any], json.loads(json_str))


def does_parameter_exist(name: str) -> bool:
    client = boto3_client(service_name="ssm")
    try:
        client.get_parameter(Name=name)
        return True
    except client.exceptions.ParameterNotFound:
        return False


def list_parameters(prefix: str) -> List[str]:
    client = boto3_client(service_name="ssm")
    paginator = client.get_paginator("describe_parameters")
    response_iterator = paginator.paginate(
        ParameterFilters=[
            {
                "Key": "Type",
                "Option": "Equals",
                "Values": [
                    "String",
                ],
            },
            {"Key": "Name", "Option": "BeginsWith", "Values": [prefix]},
        ],
    )
    ret: List[str] = []
    for page in response_iterator:
        for par in page.get("Parameters"):
            ret.append(par["Name"])
    return ret


def list_parameters_with_filter(prefix: str, contains_string: str) -> List[str]:
    client = boto3_client(service_name="ssm")
    paginator = client.get_paginator("describe_parameters")

    response_iterator = paginator.paginate(
        ParameterFilters=[
            {
                "Key": "Type",
                "Option": "Equals",
                "Values": [
                    "String",
                ],
            },
            {"Key": "Name", "Option": "Contains", "Values": [contains_string]},
        ],
    )
    ret: List[str] = []
    for page in response_iterator:
        for par in page.get("Parameters"):
            if str(par["Name"]).startswith(f"{prefix}"):
                ret.append(par["Name"])
    return ret


def get_all_parameter_data_by_path(prefix: str) -> Dict[str, Any]:
    client = boto3_client(service_name="ssm")
    paginator = client.get_paginator("get_parameters_by_path")
    response_iterator = paginator.paginate(
        Path=prefix,
        Recursive=True,
        ParameterFilters=[
            {
                "Key": "Type",
                "Option": "Equals",
                "Values": [
                    "String",
                ],
            },
        ],
    )
    ret: Dict[str, Dict[str, Any]] = {}
    for page in response_iterator:
        for par in page.get("Parameters"):
            ret[par["Name"]] = json.loads(par["Value"])
    return ret


def delete_parameters(parameters: List[str]) -> None:
    if parameters:
        if len(parameters) < 10:
            client = boto3_client(service_name="ssm")
            client.delete_parameters(Names=parameters)
        else:
            delete_parameters(parameters[0:9])
            delete_parameters(parameters[9 : len(parameters)])
