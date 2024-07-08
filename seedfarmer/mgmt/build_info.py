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
from collections import ChainMap
from typing import Any, Dict, List, Optional

from boto3 import Session

import seedfarmer.errors
from seedfarmer.models.manifests._deployment_manifest import DeploymentManifest
from seedfarmer.models.manifests._module_manifest import ModuleManifest
from seedfarmer.services import _codebuild as codebuild

_logger: logging.Logger = logging.getLogger(__name__)


def get_build_env_params(build_ids: List[str], session: Optional[Session] = None) -> Optional[Dict[str, Any]]:
    response = codebuild.get_build_data(build_ids=build_ids, session=session)
    env_params = (
        response["builds"][0]["environment"]["environmentVariables"]
        if (
            response
            and response.get("builds")
            and response["builds"][0].get("environment")
            and response["builds"][0]["environment"].get("environmentVariables")
        )
        else None
    )
    list_of_envs = [{entry_dict["name"]: entry_dict["value"]} for entry_dict in env_params] if env_params else None
    return dict(ChainMap(*list_of_envs)) if list_of_envs else None


def get_manifest_schema(type: str) -> Dict[str, Any]:
    if "deployment" == type.lower():
        return DeploymentManifest.model_json_schema()
    elif "module" == type.lower():
        return ModuleManifest.model_json_schema()
    else:
        raise seedfarmer.errors.SeedFarmerException("Schema type selection not in [deployment, module]")
