#    Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
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
from typing import Dict, Optional, cast

from boto3 import Session

import seedfarmer
import seedfarmer.mgmt.bundle_support as bundle_support
from seedfarmer import config
from seedfarmer.models.deploy_responses import ModuleDeploymentResponse
from seedfarmer.models.manifests import ModuleManifest
from seedfarmer.models.transfer import ModuleDeployObject
from seedfarmer.services.session_manager import SessionManager
from seedfarmer.types.parameter_types import EnvVar
from seedfarmer.utils import generate_session_hash

_logger: logging.Logger = logging.getLogger(__name__)


class DeployModule:
    def __init__(self, mdo: ModuleDeployObject):
        self.mdo = mdo
        self.module_manifest = cast(
            ModuleManifest, mdo.deployment_manifest.get_module(str(mdo.group_name), str(mdo.module_name))
        )

    @staticmethod
    def seedfarmer_param(
        key: str, project_name: Optional[str] = None, use_project_prefix: Optional[bool] = True
    ) -> str:
        project_name = project_name if project_name else seedfarmer.config.PROJECT
        # use_project_prefix is driven by the publishGenericEnvVariables in the deployspec
        # should always be TRUE for new modules...but we are supporting legacy code
        #
        p = project_name.upper().replace("-", "_") if use_project_prefix else "SEEDFARMER"
        return f"{p}_{key}"

    def deploy_module(self) -> ModuleDeploymentResponse:
        raise NotImplementedError("Subclasses must implement 'deploy_module'")

    def destroy_module(self) -> ModuleDeploymentResponse:
        raise NotImplementedError("Subclasses must implement 'deploy_module'")

    def _prebuilt_bundle_check(self) -> Optional[str]:
        if self.mdo.seedfarmer_bucket:
            module_manifest = self.module_manifest
            account_id = str(module_manifest.get_target_account_id())
            region = str(module_manifest.target_region)
            deployment = str(self.mdo.deployment_manifest.name)
            group = self.mdo.group_name
            module = self.mdo.module_name
            bucket = self.mdo.seedfarmer_bucket
            session = SessionManager().get_or_create().get_deployment_session(account_id=account_id, region_name=region)
            if bundle_support.check_bundle_exists_in_sf(deployment, str(group), str(module), bucket, session):
                return bundle_support.get_bundle_sf_path(deployment, str(group), str(module), bucket)
            else:
                return None
        else:
            return None

    def _env_vars(self, session: Optional[Session] = None) -> Dict[str, str]:
        use_project_prefix = not self.module_manifest.deploy_spec.publish_generic_env_variables  # type: ignore [union-attr]
        pypi_mirror_secret = (
            self.module_manifest.pypi_mirror_secret
            if self.module_manifest.pypi_mirror_secret
            else self.mdo.pypi_mirror_secret
        )
        npm_mirror_secret = (
            self.module_manifest.npm_mirror_secret
            if self.module_manifest.npm_mirror_secret
            else self.mdo.npm_mirror_secret
        )

        env_vars = (
            {
                f"{DeployModule.seedfarmer_param('PARAMETER', None, use_project_prefix)}_{p.upper_snake_case}": (
                    p.value if isinstance(p.value, str) or isinstance(p.value, EnvVar) else json.dumps(p.value)
                )
                for p in self.mdo.parameters
            }
            if self.mdo.parameters
            else {}
        )
        _logger.debug(f"use_project_prefix: {use_project_prefix}")
        _logger.debug(f"env_vars: {env_vars}")

        env_vars[DeployModule.seedfarmer_param("PROJECT_NAME", None, use_project_prefix)] = config.PROJECT
        env_vars[DeployModule.seedfarmer_param("DEPLOYMENT_NAME", None, use_project_prefix)] = str(
            self.mdo.deployment_manifest.name
        )
        env_vars[DeployModule.seedfarmer_param("MODULE_METADATA", None, use_project_prefix)] = (
            self.mdo.module_metadata if self.mdo.module_metadata is not None else ""
        )
        env_vars[DeployModule.seedfarmer_param("MODULE_NAME", None, use_project_prefix)] = (
            f"{self.mdo.group_name}-{self.module_manifest.name}"
        )
        env_vars[DeployModule.seedfarmer_param("HASH", None, use_project_prefix)] = generate_session_hash(
            session=session
        )
        if self.mdo.permissions_boundary_arn:
            env_vars[DeployModule.seedfarmer_param("PERMISSIONS_BOUNDARY_ARN", None, use_project_prefix)] = (
                self.mdo.permissions_boundary_arn
            )
        if self.mdo.docker_credentials_secret:
            env_vars["AWS_CODESEEDER_DOCKER_SECRET"] = self.mdo.docker_credentials_secret  # (LEGACY)
            env_vars["SEEDFARMER_DOCKER_SECRET"] = self.mdo.docker_credentials_secret
        if self.mdo.pypi_mirror_secret is not None:
            env_vars["AWS_CODESEEDER_PYPI_MIRROR_SECRET"] = str(pypi_mirror_secret)  # (LEGACY)
            env_vars["SEEDFARMER_PYPI_MIRROR_SECRET"] = str(pypi_mirror_secret)
        if self.mdo.npm_mirror_secret is not None:
            env_vars["AWS_CODESEEDER_NPM_MIRROR_SECRET"] = str(npm_mirror_secret)  # (LEGACY)
            env_vars["SEEDFARMER_NPM_MIRROR_SECRET"] = str(npm_mirror_secret)
        # Add the partition to env for ease of fetching
        env_vars["AWS_PARTITION"] = str(self.mdo.deployment_manifest._partition)
        env_vars["SEEDFARMER_VERSION"] = seedfarmer.__version__
        # return env_vars
        return {k: v if isinstance(v, str) else v.value for k, v in env_vars.items()}
