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

import hashlib
import logging
from typing import Optional

import humps
import yaml
from boto3 import Session

from seedfarmer.services._service_utils import get_account_id, get_region

_logger: logging.Logger = logging.getLogger(__name__)

NoDatesSafeLoader = yaml.SafeLoader


class CfnSafeYamlLoader(yaml.SafeLoader):
    """
    CfnSafeYamlLoader
    A predefined class loader to support safely reading YAML files

    Parameters
    ----------
    yaml : _type_
    """

    yaml_implicit_resolvers = {
        k: [r for r in v if r[0] != "tag:yaml.org,2002:timestamp"]
        for k, v in NoDatesSafeLoader.yaml_implicit_resolvers.items()
    }


def upper_snake_case(value: str) -> str:
    """
    This will convert strings to a standard format

    Parameters
    ----------
    value : str
        The string you want to convert

    Returns
    -------
    str
        the string standardized
    """
    if humps.is_camelcase(value):  # type: ignore
        return humps.decamelize(value).upper()  # type: ignore
    elif humps.is_pascalcase(value):  # type: ignore
        return humps.depascalize(value).upper()  # type: ignore
    else:
        return value.replace("-", "_").upper()


def generate_hash(string: str, length: int = 8) -> str:
    return (hashlib.sha1(string.encode("UTF-8")).hexdigest())[:length]


def generate_session_hash(session: Optional[Session] = None) -> str:
    """
    Generate a hexdigest hash of the project and the deployment - for use generating unique names

    Returns
    -------
    str
        The resulting hash as a string
    """
    account = get_account_id(session=session)
    region = get_region(session=session)
    concatenated_string = f"{account}-{region}"
    hash_value = generate_hash(string=concatenated_string, length=8)
    _logger.debug("HASH generated is %s", hash_value)
    return hash_value


def generate_codebuild_url(account_id: str, region: str, codebuild_id: str) -> str:
    """
    Generate a standard URL for codebuild build information

    Parameters
    ----------
    account_id : str
        The AWS account id where CodeBuild ran
    region : str
        The AWS region where CodeBuild ran
    codebuild_id : str
        The CodeBuild Build ID

    Returns
    -------
    str
        The standard URL with protocol and query parameters
        ex: https://us-east-1.console.aws.amazon.com/codesuite/codebuild/123456789012/projects/
            codebuild-id/build/codebuild-id:3413241234/?region-us-east-1
    """
    try:
        b_id_enc = codebuild_id.replace(":", "%3A")
        cb_p = codebuild_id.split(":")[0]
        return "".join(
            (
                "https://",
                f"{region}",
                ".console.aws.amazon.com/codesuite/codebuild/",
                f"{account_id}",
                "/projects/",
                f"{cb_p}",
                "/build/",
                f"{b_id_enc}",
                "/?region=",
                f"{region}",
            )
        )
    except Exception as e:
        _logger.error(f"Error...{account_id} - {region} - {codebuild_id} - {e} ")
        return "N/A"
