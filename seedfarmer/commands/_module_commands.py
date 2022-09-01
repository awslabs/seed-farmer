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
import os
import time
from typing import Any, Dict, List, Optional, Tuple, cast

import botocore.exceptions
from aws_codeseeder import codeseeder
from aws_codeseeder.errors import CodeSeederRuntimeError
from boto3 import Session

from seedfarmer import config
from seedfarmer.models.deploy_responses import CodeSeederMetadata, ModuleDeploymentResponse, StatusType
from seedfarmer.models.manifests import DeploySpec, ModuleParameter
from seedfarmer.services.session_manager import SessionManager
from seedfarmer.utils import generate_hash

_logger: logging.Logger = logging.getLogger(__name__)


def _param(key: str) -> str:
    return f"{config.PROJECT.upper()}_{key}"


def _env_vars(
    deployment_name: str,
    group_name: str,
    module_manifest_name: str,
    parameters: Optional[List[ModuleParameter]] = None,
    module_metadata: Optional[str] = None,
    docker_credentials_secret: Optional[str] = None,
    permission_boundary_arn: Optional[str] = None,
    session: Optional[Session] = None,
) -> Dict[str, str]:
    env_vars = (
        {
            f"{_param('PARAMETER')}_{p.upper_snake_case}": p.value if isinstance(p.value, str) else json.dumps(p.value)
            for p in parameters
        }
        if parameters
        else {}
    )
    env_vars[_param("DEPLOYMENT_NAME")] = deployment_name
    env_vars[_param("MODULE_METADATA")] = module_metadata if module_metadata is not None else ""
    env_vars[_param("MODULE_NAME")] = f"{group_name}-{module_manifest_name}"
    env_vars[_param("HASH")] = generate_hash(session=session)
    if docker_credentials_secret:
        env_vars["AWS_CODESEEDER_DOCKER_SECRET"] = docker_credentials_secret
    if permission_boundary_arn:
        env_vars[_param("PERMISSION_BOUNDARY_ARN")] = permission_boundary_arn
    return env_vars


def deploy_module(
    deployment_name: str,
    group_name: str,
    module_path: str,
    module_deploy_spec: DeploySpec,
    module_manifest_name: str,
    account_id: str,
    region: str,
    parameters: Optional[List[ModuleParameter]] = None,
    module_metadata: Optional[str] = None,
    module_bundle_md5: Optional[str] = None,
    docker_credentials_secret: Optional[str] = None,
    permission_boundary_arn: Optional[str] = None,
) -> ModuleDeploymentResponse:
    env_vars = _env_vars(
        deployment_name=deployment_name,
        group_name=group_name,
        module_manifest_name=module_manifest_name,
        parameters=parameters,
        module_metadata=module_metadata,
        docker_credentials_secret=docker_credentials_secret,
        permission_boundary_arn=permission_boundary_arn,
        session=SessionManager().get_or_create().get_deployment_session(account_id=account_id, region_name=region),
    )
    env_vars[_param("MODULE_MD5")] = module_bundle_md5 if module_bundle_md5 is not None else ""

    md5_put = [
        (
            f"echo {module_bundle_md5} | seedfarmer store md5 -d {deployment_name} "
            f"-g {group_name} -m {module_manifest_name} -t bundle --debug ;"
        )
    ]
    pmd = _param("MODULE_METADATA")
    metadata_put = [
        f"if [[ -f {pmd} ]]; then export {pmd}=$(cat {pmd}); fi",
        (
            f"echo ${pmd} | seedfarmer store moduledata "
            f"-d {deployment_name} -g {group_name} -m {module_manifest_name}"
        ),
    ]

    if module_deploy_spec.deploy is None:
        raise ValueError("Missing `deploy` in module's deployspec.yaml")

    _phases = module_deploy_spec.deploy.phases
    try:
        resp_dict_str, dict_metadata = _execute_module_commands(
            deployment_name=deployment_name,
            group_name=group_name,
            module_manifest_name=module_manifest_name,
            account_id=account_id,
            region=region,
            extra_dirs={"module": module_path},
            extra_install_commands=["cd module/"] + _phases.install.commands,
            extra_pre_build_commands=["cd module/"] + _phases.pre_build.commands,
            extra_build_commands=["cd module/"] + _phases.build.commands,
            extra_post_build_commands=["cd module/"] + _phases.post_build.commands + md5_put + metadata_put,
            extra_env_vars=env_vars,
            codebuild_compute_type=module_deploy_spec.build_type,
        )
        _logger.debug("CodeSeeder Metadata response is %s", dict_metadata)

        resp = ModuleDeploymentResponse(
            deployment=deployment_name,
            group=group_name,
            module=module_manifest_name,
            status=StatusType.SUCCESS.value,
            codeseeder_metadata=CodeSeederMetadata(**json.loads(resp_dict_str)) if resp_dict_str else None,
            codeseeder_output=dict_metadata,
        )
    except CodeSeederRuntimeError as csre:
        _logger.error(f"Error Response from CodeSeeder: {csre} - {csre.error_info}")
        l_case_error = {k.lower(): csre.error_info[k] for k in csre.error_info.keys()}
        resp = ModuleDeploymentResponse(
            deployment=deployment_name,
            group=group_name,
            module=module_manifest_name,
            status=StatusType.ERROR.value,
            codeseeder_metadata=CodeSeederMetadata(**l_case_error),
        )
    return resp


def destroy_module(
    deployment_name: str,
    group_name: str,
    module_path: str,
    module_deploy_spec: DeploySpec,
    module_manifest_name: str,
    account_id: str,
    region: str,
    parameters: Optional[List[ModuleParameter]] = None,
    module_metadata: Optional[str] = None,
) -> ModuleDeploymentResponse:
    env_vars = _env_vars(
        deployment_name=deployment_name,
        group_name=group_name,
        module_manifest_name=module_manifest_name,
        parameters=parameters,
        module_metadata=module_metadata,
        session=SessionManager().get_or_create().get_deployment_session(account_id=account_id, region_name=region),
    )

    remove_ssm = [f"seedfarmer remove moduledata -d {deployment_name} -g {group_name} -m {module_manifest_name}"]

    export_info = [
        f"export DEPLOYEMNT={deployment_name}",
        f"export GROUP={group_name}",
        f"export MODULE={module_manifest_name}",
    ]

    if module_deploy_spec.destroy is None:
        raise ValueError(
            f"Missing `destroy` in module: {module_manifest_name} with {module_deploy_spec.destroy} deployspec.yaml"
        )

    _phases = module_deploy_spec.destroy.phases

    try:
        resp_dict_str, _ = _execute_module_commands(
            deployment_name=deployment_name,
            group_name=group_name,
            module_manifest_name=module_manifest_name,
            account_id=account_id,
            region=region,
            extra_dirs={"module": module_path},
            extra_install_commands=["cd module/"] + _phases.install.commands,
            extra_pre_build_commands=["cd module/"] + _phases.pre_build.commands + export_info,
            extra_build_commands=["cd module/"] + _phases.build.commands,
            extra_post_build_commands=["cd module/"] + _phases.post_build.commands + remove_ssm,
            extra_env_vars=env_vars,
            codebuild_compute_type=module_deploy_spec.build_type,
        )
        resp = ModuleDeploymentResponse(
            deployment=deployment_name,
            group=group_name,
            module=module_manifest_name,
            status=StatusType.SUCCESS.value,
            codeseeder_metadata=CodeSeederMetadata(**json.loads(resp_dict_str)) if resp_dict_str else None,
        )
    except CodeSeederRuntimeError as csre:
        _logger.error(f"Error Response from CodeSeeder: {csre} - {csre.error_info}")
        l_case_error = {k.lower(): csre.error_info[k] for k in csre.error_info.keys()}
        resp = ModuleDeploymentResponse(
            deployment=deployment_name,
            group=group_name,
            module=module_manifest_name,
            status=StatusType.ERROR.value,
            codeseeder_metadata=CodeSeederMetadata(**l_case_error),
        )
    return resp


def _execute_module_commands(
    deployment_name: str,
    group_name: str,
    module_manifest_name: str,
    account_id: str,
    region: str,
    extra_dirs: Optional[Dict[str, Any]] = None,
    extra_install_commands: Optional[List[str]] = None,
    extra_pre_build_commands: Optional[List[str]] = None,
    extra_build_commands: Optional[List[str]] = None,
    extra_post_build_commands: Optional[List[str]] = None,
    extra_env_vars: Optional[Dict[str, Any]] = None,
    codebuild_compute_type: Optional[str] = None,
) -> Tuple[str, Optional[Dict[str, str]]]:
    session: Optional[Session] = None

    if not codeseeder.EXECUTING_REMOTELY:
        session = SessionManager().get_or_create().get_deployment_session(account_id=account_id, region_name=region)

    @codeseeder.remote_function(
        config.PROJECT.lower(),
        extra_dirs=extra_dirs,
        extra_install_commands=extra_install_commands,
        extra_pre_build_commands=extra_pre_build_commands,
        extra_build_commands=extra_build_commands,
        extra_post_build_commands=extra_post_build_commands,
        extra_env_vars=extra_env_vars,
        extra_exported_env_vars=[f"{_param('MODULE_METADATA')}"],
        codebuild_role=(
            f"{config.PROJECT.lower()}-{deployment_name}-{group_name}"
            f"-{module_manifest_name}-{generate_hash(session=session)}"
        ),
        bundle_id=module_manifest_name,
        codebuild_compute_type=codebuild_compute_type,
        extra_files={config.CONFIG_FILE: os.path.join(config.OPS_ROOT, config.CONFIG_FILE)},
        boto3_session=session,
    )
    def _execute_module_commands(
        deployment_name: str,
        group_name: str,
        module_manifest_name: str,
        account_id: str,
        region: str,
        extra_dirs: Optional[Dict[str, Any]] = None,
        extra_install_commands: Optional[List[str]] = None,
        extra_pre_build_commands: Optional[List[str]] = None,
        extra_build_commands: Optional[List[str]] = None,
        extra_post_build_commands: Optional[List[str]] = None,
        extra_env_vars: Optional[Dict[str, Any]] = None,
        codebuild_compute_type: Optional[str] = None,
    ) -> str:
        deploy_info = {
            "aws_region": os.environ.get("AWS_DEFAULT_REGION"),
            "aws_account_id": os.environ.get("AWS_ACCOUNT_ID"),
            "codebuild_build_id": os.environ.get("CODEBUILD_BUILD_ID"),
            "codebuild_log_path": os.environ.get("CODEBUILD_LOG_PATH"),
        }
        return json.dumps(deploy_info)

    count = 0
    while True:
        try:
            count += 1
            return cast(
                Tuple[str, Optional[Dict[str, str]]],
                _execute_module_commands(
                    deployment_name=deployment_name,
                    group_name=group_name,
                    module_manifest_name=module_manifest_name,
                    account_id=account_id,
                    region=region,
                    extra_dirs=extra_dirs,
                    extra_install_commands=extra_install_commands,
                    extra_pre_build_commands=extra_pre_build_commands,
                    extra_build_commands=extra_build_commands,
                    extra_post_build_commands=extra_post_build_commands,
                    extra_env_vars=extra_env_vars,
                    codebuild_compute_type=codebuild_compute_type,
                ),
            )
        except botocore.exceptions.ClientError as ex:
            if (
                count < 3
                and "CodeBuild is not authorized to perform: sts:AssumeRole on" in ex.response["Error"]["Message"]
            ):
                _logger.info("Module IAM Role not yet assumable by CodeBuild, will retry in 5 seconds")
                time.sleep(5)
            else:
                raise ex
