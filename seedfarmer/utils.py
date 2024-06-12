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
import os
import re
from typing import Any, Dict, List, Optional

import humps
import yaml
from boto3 import Session
from dotenv import dotenv_values, load_dotenv

import seedfarmer.errors
from seedfarmer.services._service_utils import get_region, get_sts_identity_info

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
    if humps.is_camelcase(value):
        return humps.decamelize(value).upper()
    elif humps.is_pascalcase(value):
        return humps.depascalize(value).upper()
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
    account, _, _ = get_sts_identity_info(session=session)
    region = get_region(session=session)
    concatenated_string = f"{account}-{region}"
    hash_value = generate_hash(string=concatenated_string, length=8)
    _logger.debug("HASH generated is %s", hash_value)
    return hash_value


def generate_codebuild_url(account_id: str, region: str, codebuild_id: str, partition: Optional[str] = "aws") -> str:
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
        if in a differeing partion (ex.aws-cn) the url looks like:
            https://cn-north-1.console.amazonaws.cn/codesuite/codebuild/123456789012/projects/
            codeseeder-idf/build/codeseeder-id:3413241234/?region=cn-north-1
    """
    try:
        b_id_enc = codebuild_id.replace(":", "%3A")
        cb_p = codebuild_id.split(":")[0]
        domain_completion = ".console.aws.amazon.com/codesuite/codebuild/"
        if partition == "aws-cn":
            domain_completion = ".console.amazonaws.cn/codesuite/codebuild/"
        return "".join(
            (
                "https://",
                f"{region}",
                f"{domain_completion}",
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


def get_toolchain_role_name(project_name: str, qualifier: Optional[str] = None) -> str:
    name = f"seedfarmer-{project_name}-toolchain-role"
    return f"{name}-{qualifier}" if qualifier else name


def get_toolchain_role_arn(
    partition: str, toolchain_account_id: str, project_name: str, qualifier: Optional[str] = None
) -> str:
    return f"arn:{partition}:iam::{toolchain_account_id}:role/{get_toolchain_role_name(project_name, qualifier)}"


def get_deployment_role_name(project_name: str, qualifier: Optional[str] = None) -> str:
    name = f"seedfarmer-{project_name}-deployment-role"
    return f"{name}-{qualifier}" if qualifier else name


def get_deployment_role_arn(
    partition: str, deployment_account_id: str, project_name: str, qualifier: Optional[str] = None
) -> str:
    return f"arn:{partition}:iam::{deployment_account_id}:role/{get_deployment_role_name(project_name, qualifier)}"


def valid_qualifier(qualifer: str) -> bool:
    return True if ((len(qualifer) <= 6) and qualifer.isalnum()) else False


def load_dotenv_files(root_path: str, env_files: List[str]) -> None:
    """
    Load the environment variables from the .env files

    Parameters
    ----------
    root_path : str
        The path to the root of the project
    env_files : List[str]
        The list of the .env files to load
    """
    loaded_values = {}

    for env_file in env_files:
        _logger.info("Loading environment variables from %s", env_file)
        dotenv_path = os.path.join(root_path, env_file)

        load_dotenv(dotenv_path=dotenv_path, verbose=True, override=True)
        loaded_values.update(dotenv_values(dotenv_path, verbose=True))

    _logger.debug("Loaded environment variables: %s", loaded_values)


def remove_nulls(payload: Dict[str, Any]) -> Dict[str, Any]:
    if isinstance(payload, dict):
        return {k: remove_nulls(v) for k, v in payload.items() if v is not None}
    elif isinstance(payload, list):
        return [remove_nulls(v) for v in payload]
    else:
        return payload


def batch_replace_env(payload: Dict[str, Any]) -> Dict[str, Any]:
    pattern = r"\${(.*?)}"

    def replace_str(value: str) -> str:
        matches = re.findall(pattern, value)
        for match in matches:
            try:
                return value.replace("${" + match + "}", os.environ[match.strip()])
            except KeyError:
                raise seedfarmer.errors.InvalidManifestError(
                    f"The environment variable ({match.strip()}) is not available"
                )
        return value

    def recurse_list(working_list: List[Any]) -> List[Any]:
        for key, value in enumerate(working_list):
            if isinstance(value, str):
                working_list[key] = replace_str(value)
            elif isinstance(value, list):
                recurse_list(value)
            elif isinstance(value, dict):
                recurse_dict(value)
        return working_list

    def recurse_dict(working_element: Dict[str, Any]) -> Dict[str, Any]:
        for key, value in working_element.items():
            if isinstance(value, str):
                working_element[key] = replace_str(value)
            elif isinstance(value, list):
                recurse_list(value)
            elif isinstance(value, dict) and key not in ["deploy_spec"]:
                recurse_dict(value)
        return working_element

    payload = recurse_dict(payload)
    return payload
