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

import glob
import hashlib
import logging
import os
import re
import shutil
from typing import Any, Dict, List, Optional, Union

import humps
import yaml
from boto3 import Session
from dotenv import dotenv_values, load_dotenv
from ruamel.yaml import YAML
from ruamel.yaml.scalarstring import PreservedScalarString

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


class LiteralStr(PreservedScalarString):
    """A string subclass that forces block style (|) YAML formatting."""

    pass


def register_literal_str() -> YAML:
    yaml = YAML()
    yaml.preserve_quotes = True
    yaml.indent(mapping=2, sequence=4, offset=2)
    yaml.block_seq_indent = 2

    def literal_str_representer(dumper, data):  # type: ignore [no-untyped-def]
        kwargs = {"style": "|"}
        return dumper.represent_scalar("tag:yaml.org,2002:str", data, **kwargs)

    yaml.representer.add_representer(LiteralStr, literal_str_representer)
    return yaml


def apply_literalstr(s: str) -> Union[str, LiteralStr]:
    return LiteralStr(s) if "\n" in s else s


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
    return (hashlib.sha1(string.encode("UTF-8"), usedforsecurity=False).hexdigest())[:length]


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
            codebuild-id/build/codebuild-id:3413241234/?region-us-east-1 (LEGACY)
        if in a differing partition (ex.aws-cn) the url looks like:
            https://cn-north-1.console.amazonaws.cn/codesuite/codebuild/123456789012/projects/
            codeseeder-idf/build/codeseeder-id:3413241234/?region=cn-north-1 (LEGACY)
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
    partition: str,
    toolchain_account_id: str,
    project_name: str,
    qualifier: Optional[str] = None,
    role_prefix: Optional[str] = None,
) -> str:
    role_prefix = role_prefix if role_prefix else "/"
    return (
        f"arn:{partition}:iam::{toolchain_account_id}:role{role_prefix}"
        f"{get_toolchain_role_name(project_name, qualifier)}"
    )


def get_deployment_role_name(project_name: str, qualifier: Optional[str] = None) -> str:
    name = f"seedfarmer-{project_name}-deployment-role"
    return f"{name}-{qualifier}" if qualifier else name


def get_deployment_role_arn(
    partition: str,
    deployment_account_id: str,
    project_name: str,
    qualifier: Optional[str] = None,
    role_prefix: Optional[str] = None,
) -> str:
    role_prefix = role_prefix if role_prefix else "/"
    return (
        f"arn:{partition}:iam::{deployment_account_id}:role{role_prefix}"
        f"{get_deployment_role_name(project_name, qualifier)}"
    )


def get_generic_module_deployment_role_name(
    project_name: str,
    deployment_name: str,
    region: str,
) -> str:
    resource_name = f"{project_name}-{deployment_name}-{region}"
    resource_hash = generate_hash(string=resource_name, length=4)

    # Max length of IAM role name is 64 chars, "-deployment-role" is 16 chars, resource_hash plus "-" is 5 chars.
    # If the resource_name, and "-deployment-role" is too long, truncate and use resource_hash for uniqueness.
    return (
        f"{resource_name[: 64 - 16 - 5]}-deployment-role-{resource_hash}"
        if len(resource_name) > (64 - 16)
        else f"{resource_name}-deployment-role"
    )


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
        try:
            return re.sub(
                pattern=pattern,
                repl=lambda m: os.environ[m.group(1).strip()],
                string=value,
            )
        except KeyError as e:
            raise seedfarmer.errors.InvalidManifestError(f"The environment variable is not available: {e}")

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
        if not working_element.get("disableEnvVarResolution"):
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


def create_output_dir(name: str, path_override: Optional[str] = None) -> str:
    """Helper function for creating or clearing a .seedfarmer.out output directory by default

    Parameters
    ----------
    name : str
        Name of the directory to create in  the .seedfarmer.out directory

    path_override: Optional[str]
        If you want to override the name .seedfarmer.out use this (beware of what you are doing)

    Returns
    -------
    str
        Full path of the created directory
    """
    local_path = path_override if path_override else ".seedfarmer.out"
    out_dir = os.path.join(os.getcwd(), local_path, name)
    try:
        shutil.rmtree(out_dir)
    except FileNotFoundError:
        pass
    # except PermissionError:
    #     pass
    os.makedirs(out_dir, exist_ok=True)
    return out_dir


def delete_all_output_dir(name: str = ".seedfarmerlocal-") -> None:
    pattern = os.path.join(os.getcwd(), f"{name}-*")
    for path in glob.glob(pattern):
        if os.path.isdir(path):
            shutil.rmtree(path)
