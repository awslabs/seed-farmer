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
import os
import subprocess
from pathlib import Path
from typing import Any, Dict, Optional, Tuple, cast

import yaml

from seedfarmer import config

# from seedfarmer.deployment.deploy_remote import _param as param
from seedfarmer.deployment.deploy_base import DeployModule
from seedfarmer.mgmt.module_info import get_deployspec_path
from seedfarmer.models._deploy_spec import DeploySpec

_logger: logging.Logger = logging.getLogger(__name__)


class ModuleMetadataSupport:
    use_project_prefix: Optional[bool] = None
    ops_root_path: Optional[str] = None
    project: Optional[str] = None

    def __init__(self) -> None:
        self.project = config.PROJECT
        self.ops_root_path = config.OPS_ROOT
        try:
            with open(get_deployspec_path("module")) as module_spec_file:
                deploy_spec = DeploySpec(**yaml.safe_load(module_spec_file))
            self.use_project_prefix = not deploy_spec.publish_generic_env_variables
        except Exception:
            _logger.warning("Cannot read the deployspec, using project name as prefix (a non-generic module)")
            self.use_project_prefix = True

    def get_ops_root_path(self) -> str:
        return str(self.ops_root_path)

    def metadata_file_name(self) -> str:
        return str(DeployModule.seedfarmer_param("MODULE_METADATA", None, self.use_project_prefix))

    def metadata_fullpath(self) -> str:
        return os.path.join(str(self.ops_root_path), "module", self.metadata_file_name())

    def project_param_name(self) -> str:
        return str(DeployModule.seedfarmer_param("PROJECT_NAME", None, self.use_project_prefix))

    def deployment_param_name(self) -> str:
        return str(DeployModule.seedfarmer_param("DEPLOYMENT_NAME", None, self.use_project_prefix))

    def module_param_name(self) -> str:
        return str(DeployModule.seedfarmer_param("MODULE_NAME", None, self.use_project_prefix))


def _read_metadata_file(mms: ModuleMetadataSupport) -> Dict[str, Any]:
    p = mms.metadata_fullpath()
    if Path(p).is_file():
        _logger.info("Reading metadata file at %s", p)
        try:
            with open(Path(mms.metadata_fullpath()), "r") as metadatafile:
                j = metadatafile.read()
            return cast(Dict[str, Any], json.loads(j))
        except json.decoder.JSONDecodeError:
            _logger.info("Cannot parse the file json")
            return {}
    else:
        _logger.info("Cannot find existing metadata file at %s, moving on", p)
        return {}


def _read_metadata_env_param(mms: ModuleMetadataSupport) -> Dict[str, Any]:
    p = mms.metadata_file_name()
    env_data = os.getenv(p)

    if env_data:
        try:
            return cast(Dict[str, Any], json.loads(env_data))
        except ValueError:
            try:
                return cast(Dict[str, Any], json.loads(env_data.replace("'", '"')))
            except Exception as e:
                _logger.info("Cannot parse env metadata %s after quote fix due to %s", p, e)
                return {}
        except Exception as e:
            _logger.info("Cannot parse env metadata %s due to %s", p, e)
            return {}
    else:
        _logger.info("Cannot find or empty metadata env param at %s, moving on", p)
        return {}


def _mod_dep_key(mms: ModuleMetadataSupport) -> str:
    return (
        f"{os.getenv(mms.project_param_name())}-"
        f"{os.getenv(mms.deployment_param_name())}-"
        f"{os.getenv(mms.module_param_name())}"
    )


def _read_json_file(mms: ModuleMetadataSupport, path: str) -> Tuple[str, Dict[str, Any]]:
    p = os.path.join(mms.get_ops_root_path(), "module", path)
    _logger.info("Reading extra file path located at %s", p)
    if os.path.isfile(p):
        with open(p, "r") as datafile:
            j = datafile.read()
        return p, dict(json.loads(j))
    else:
        return p, {}


def _write_metadata_file(mms: ModuleMetadataSupport, data: Dict[str, Any]) -> None:
    p = mms.metadata_fullpath()
    _logger.info("Writing metadata to %s", p)
    with open(p, "w") as outfile:
        outfile.write(json.dumps(data))


def _clean_jq(jq: str) -> str:
    sep = '"'
    a = [f"{sep}{val}{sep}" if val.find("-") != -1 else val for val in jq.split(".")]
    modified_str = ".".join(a)
    return f".{modified_str}" if not modified_str.startswith(".") else modified_str


def add_json_output(json_string: str) -> None:
    mms = ModuleMetadataSupport()
    json_new = json.loads(json_string)
    file_dict = _read_metadata_file(mms=mms)
    json_new = {**file_dict, **json_new} if file_dict else json_new
    _logger.debug(f"Current Dict {json.dumps(json_new, indent=4)}")
    env_dict = _read_metadata_env_param(mms=mms)
    json_new = {**env_dict, **json_new} if env_dict else json_new
    _logger.debug(f"Current Dict {json.dumps(json_new, indent=4)}")
    _write_metadata_file(mms=mms, data=json_new)


def add_kv_output(key: str, value: str) -> None:
    mms = ModuleMetadataSupport()
    data = {}
    data[key] = value
    file_dict = _read_metadata_file(mms=mms)
    data = {**file_dict, **data} if file_dict else data
    _logger.debug(f"Current Dict {json.dumps(data, indent=4)}")
    env_dict = _read_metadata_env_param(mms=mms)
    data = {**env_dict, **data} if env_dict else data
    _logger.debug(f"Current Dict {json.dumps(data, indent=4)}")
    _write_metadata_file(mms=mms, data=data)


def convert_cdkexports(
    json_file: str,
    jq_path: Optional[str] = None,
) -> None:
    mms = ModuleMetadataSupport()
    cdk_output_path, cdk_output = _read_json_file(mms, json_file)
    data = {}
    if cdk_output:
        if not jq_path:
            out_key = _mod_dep_key(mms)
            _logger.info("Pulling %s from the %s file", out_key, json_file)
            data = cdk_output[out_key]["metadata"]
        else:
            clean_jq_path = _clean_jq(jq_path)
            _logger.info("Pulling with jq path '%s' from %s file", clean_jq_path, json_file)
            with open(cdk_output_path, "r") as infile, open("tmp-metadata", "w") as outfile:
                subprocess.run(["jq", clean_jq_path], stdin=infile, stdout=outfile, shell=False)
            data = json.loads(open("tmp-metadata", "r").read())

    existing_metadata = _read_metadata_file(mms)

    try:
        _write_metadata_file(mms=mms, data={**existing_metadata, **json.loads(data)}) if data else None  # type: ignore[arg-type]
    except json.decoder.JSONDecodeError:
        _logger.info("The CDK Export is not a string that can be converted to a JSON, ignoring this additional data")
        _logger.info("Offending metadata -- %s", data)
        _write_metadata_file(mms=mms, data=existing_metadata) if existing_metadata else None


def get_dep_mod_name() -> str:
    return _mod_dep_key(ModuleMetadataSupport())


def get_parameter_value(parameter_suffix: str) -> Optional[str]:
    mms = ModuleMetadataSupport()
    key = DeployModule.seedfarmer_param(parameter_suffix, None, mms.use_project_prefix)
    try:
        _logger.info("Getting the Env Parameter tied to %s", key)
        return os.getenv(key)
    except Exception:
        _logger.warning("Error looking for %s, returning None", key)
        return None
