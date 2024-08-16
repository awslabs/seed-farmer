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
from typing import Any, Callable, Dict, List, Optional, Tuple, cast

import aws_codeseeder
import botocore.exceptions
from aws_codeseeder import EnvVar, codeseeder
from aws_codeseeder.errors import CodeSeederRuntimeError
from boto3 import Session

import seedfarmer
import seedfarmer.errors
import seedfarmer.mgmt.bundle_support as bs
from seedfarmer import config
from seedfarmer.commands._runtimes import get_runtimes
from seedfarmer.models.deploy_responses import CodeSeederMetadata, ModuleDeploymentResponse, StatusType
from seedfarmer.models.manifests import ModuleManifest, ModuleParameter
from seedfarmer.models.transfer import ModuleDeployObject
from seedfarmer.services.session_manager import SessionManager
from seedfarmer.utils import generate_session_hash

_logger: logging.Logger = logging.getLogger(__name__)


def _param(key: str, use_project_prefix: Optional[bool] = True) -> str:
    p = config.PROJECT.upper().replace("-", "_") if use_project_prefix else "SEEDFARMER"
    return f"{p}_{key}"


def _env_vars(
    deployment_name: str,
    deployment_partition: str,
    group_name: str,
    module_manifest_name: str,
    parameters: Optional[List[ModuleParameter]] = None,
    module_metadata: Optional[str] = None,
    docker_credentials_secret: Optional[str] = None,
    permissions_boundary_arn: Optional[str] = None,
    session: Optional[Session] = None,
    use_project_prefix: Optional[bool] = True,
    pypi_mirror_secret: Optional[str] = None,
    npm_mirror_secret: Optional[str] = None,
) -> Dict[str, str]:
    env_vars = (
        {
            f"{_param('PARAMETER', use_project_prefix)}_{p.upper_snake_case}": (
                p.value if isinstance(p.value, str) or isinstance(p.value, EnvVar) else json.dumps(p.value)
            )
            for p in parameters
        }
        if parameters
        else {}
    )
    _logger.debug(f"use_project_prefix: {use_project_prefix}")
    _logger.debug(f"env_vars: {env_vars}")
    env_vars[_param("PROJECT_NAME", use_project_prefix)] = config.PROJECT
    env_vars[_param("DEPLOYMENT_NAME", use_project_prefix)] = deployment_name
    env_vars[_param("MODULE_METADATA", use_project_prefix)] = module_metadata if module_metadata is not None else ""
    env_vars[_param("MODULE_NAME", use_project_prefix)] = f"{group_name}-{module_manifest_name}"
    env_vars[_param("HASH", use_project_prefix)] = generate_session_hash(session=session)
    if docker_credentials_secret:
        env_vars["AWS_CODESEEDER_DOCKER_SECRET"] = docker_credentials_secret
    if permissions_boundary_arn:
        env_vars[_param("PERMISSIONS_BOUNDARY_ARN", use_project_prefix)] = permissions_boundary_arn
    if pypi_mirror_secret is not None:
        env_vars["AWS_CODESEEDER_PYPI_MIRROR_SECRET"] = pypi_mirror_secret
    if npm_mirror_secret is not None:
        env_vars["AWS_CODESEEDER_NPM_MIRROR_SECRET"] = npm_mirror_secret
    # Add the partition to env for ease of fetching
    env_vars["AWS_PARTITION"] = deployment_partition
    env_vars["AWS_CODESEEDER_VERSION"] = aws_codeseeder.__version__
    env_vars["SEEDFARMER_VERSION"] = seedfarmer.__version__
    return env_vars


def _prebuilt_bundle_check(mdo: ModuleDeployObject) -> Optional[str]:
    if mdo.seedfarmer_bucket:
        module_manifest = cast(ModuleManifest, mdo.deployment_manifest.get_module(mdo.group_name, mdo.module_name))
        account_id = str(module_manifest.get_target_account_id())
        region = str(module_manifest.target_region)
        deployment = str(mdo.deployment_manifest.name)
        group = mdo.group_name
        module = mdo.module_name
        bucket = mdo.seedfarmer_bucket
        session = SessionManager().get_or_create().get_deployment_session(account_id=account_id, region_name=region)
        if bs.check_bundle_exists_in_sf(deployment, group, module, bucket, session):
            return bs.get_bundle_sf_path(deployment, group, module, bucket)
        else:
            return None
    else:
        return None


def deploy_module(mdo: ModuleDeployObject) -> ModuleDeploymentResponse:
    module_manifest = cast(ModuleManifest, mdo.deployment_manifest.get_module(mdo.group_name, mdo.module_name))
    account_id = str(module_manifest.get_target_account_id())
    region = str(module_manifest.target_region)
    if module_manifest.deploy_spec is None or module_manifest.deploy_spec.deploy is None:
        raise seedfarmer.errors.InvalidConfigurationError("Missing `deploy` in module's deployspec.yaml")

    use_project_prefix = not module_manifest.deploy_spec.publish_generic_env_variables
    env_vars = _env_vars(
        deployment_name=str(mdo.deployment_manifest.name),
        deployment_partition=str(mdo.deployment_manifest._partition),
        group_name=mdo.group_name,
        module_manifest_name=module_manifest.name,
        parameters=mdo.parameters,
        module_metadata=mdo.module_metadata,
        docker_credentials_secret=mdo.docker_credentials_secret,
        permissions_boundary_arn=mdo.permissions_boundary_arn,
        session=SessionManager().get_or_create().get_deployment_session(account_id=account_id, region_name=region),
        use_project_prefix=use_project_prefix,
        pypi_mirror_secret=(
            module_manifest.pypi_mirror_secret if module_manifest.pypi_mirror_secret else mdo.pypi_mirror_secret
        ),
        npm_mirror_secret=(
            module_manifest.npm_mirror_secret if module_manifest.npm_mirror_secret else mdo.npm_mirror_secret
        ),
    )
    env_vars[_param("MODULE_MD5", use_project_prefix)] = (
        module_manifest.bundle_md5 if module_manifest.bundle_md5 is not None else ""
    )

    md5_put = [
        (
            f"echo {module_manifest.bundle_md5} | seedfarmer store md5 -d {mdo.deployment_manifest.name} "
            f"-g {mdo.group_name} -m {module_manifest.name} -t bundle --debug ;"
        )
    ]
    metadata_env_variable = _param("MODULE_METADATA", use_project_prefix)
    sf_version__add = [f"seedfarmer metadata add -k AwsCodeSeederDeployed -v {aws_codeseeder.__version__} || true"]
    cs_version_add = [f"seedfarmer metadata add -k SeedFarmerDeployed -v {seedfarmer.__version__} || true"]
    module_role_name_add = [f"seedfarmer metadata add -k ModuleDeploymentRoleName -v {mdo.module_role_name} || true"]
    githash_add = (
        [f"seedfarmer metadata add -k SeedFarmerModuleCommitHash -v {module_manifest.commit_hash} || true"]
        if module_manifest.commit_hash
        else []
    )
    metadata_put = [
        f"if [[ -f {metadata_env_variable} ]]; then export {metadata_env_variable}=$(cat {metadata_env_variable}); fi",
        (
            f"echo ${metadata_env_variable} | seedfarmer store moduledata "
            f"-d {mdo.deployment_manifest.name} -g {mdo.group_name} -m {module_manifest.name} "
        ),
    ]
    store_sf_bundle = [
        (
            f"seedfarmer bundle store -d {mdo.deployment_manifest.name} -g {mdo.group_name} -m {module_manifest.name} "
            f"-o $CODEBUILD_SOURCE_REPO_URL -b {mdo.seedfarmer_bucket} || true"
        )
    ]

    module_path = os.path.join(config.OPS_ROOT, str(module_manifest.get_local_path()))

    extra_files = {}
    if module_manifest.data_files is not None:
        extra_files = {
            f"module/{data_file.get_bundle_path()}": data_file.get_local_file_path()
            for data_file in module_manifest.data_files
        }

    _phases = module_manifest.deploy_spec.deploy.phases
    active_codebuild_image = (
        module_manifest.codebuild_image if module_manifest.codebuild_image is not None else mdo.codebuild_image
    )
    npm_mirror = module_manifest.npm_mirror if module_manifest.npm_mirror is not None else mdo.npm_mirror
    pypi_mirror = module_manifest.pypi_mirror if module_manifest.pypi_mirror is not None else mdo.pypi_mirror
    try:
        resp_dict_str, dict_metadata = _execute_module_commands(
            deployment_name=str(mdo.deployment_manifest.name),
            group_name=mdo.group_name,
            module_manifest_name=module_manifest.name,
            account_id=account_id,
            region=region,
            metadata_env_variable=metadata_env_variable,
            extra_dirs={"module": module_path},
            extra_files=extra_files,
            extra_install_commands=["cd module/"] + _phases.install.commands,
            extra_pre_build_commands=["cd module/"] + _phases.pre_build.commands,
            extra_build_commands=["cd module/"] + _phases.build.commands,
            extra_post_build_commands=["cd module/"]
            + _phases.post_build.commands
            + md5_put
            + sf_version__add
            + cs_version_add
            + module_role_name_add
            + githash_add
            + metadata_put
            + store_sf_bundle,
            extra_env_vars=env_vars,
            codebuild_compute_type=module_manifest.deploy_spec.build_type,
            codebuild_role_name=mdo.module_role_name,
            codebuild_image=active_codebuild_image,
            npm_mirror=npm_mirror,
            pypi_mirror=pypi_mirror,
            runtime_versions=get_runtimes(active_codebuild_image),
        )
        _logger.debug("CodeSeeder Metadata response is %s", dict_metadata)

        resp = ModuleDeploymentResponse(
            deployment=mdo.deployment_manifest.name,
            group=mdo.group_name,
            module=module_manifest.name,
            status=StatusType.SUCCESS.value,
            codeseeder_metadata=CodeSeederMetadata(**json.loads(resp_dict_str)) if resp_dict_str else None,
            codeseeder_output=dict_metadata,
        )
    except CodeSeederRuntimeError as csre:
        _logger.error(f"Error Response from CodeSeeder: {csre} - {csre.error_info}")
        l_case_error = {k.lower(): csre.error_info[k] for k in csre.error_info.keys()}
        resp = ModuleDeploymentResponse(
            deployment=mdo.deployment_manifest.name,
            group=mdo.group_name,
            module=module_manifest.name,
            status=StatusType.ERROR.value,
            codeseeder_metadata=CodeSeederMetadata(**l_case_error),
        )
    return resp


def destroy_module(mdo: ModuleDeployObject) -> ModuleDeploymentResponse:
    module_manifest = cast(ModuleManifest, mdo.deployment_manifest.get_module(mdo.group_name, mdo.module_name))
    account_id = str(module_manifest.get_target_account_id())
    region = str(module_manifest.target_region)
    if module_manifest.deploy_spec is None or module_manifest.deploy_spec.destroy is None:
        raise seedfarmer.errors.InvalidConfigurationError(
            f"Missing `destroy` in module: {module_manifest.name} with deployspec.yaml"
        )
    use_project_prefix = not module_manifest.deploy_spec.publish_generic_env_variables
    env_vars = _env_vars(
        deployment_name=str(mdo.deployment_manifest.name),
        deployment_partition=str(mdo.deployment_manifest._partition),
        group_name=mdo.group_name,
        module_manifest_name=module_manifest.name,
        parameters=mdo.parameters,
        module_metadata=mdo.module_metadata,
        session=SessionManager().get_or_create().get_deployment_session(account_id=account_id, region_name=region),
        use_project_prefix=use_project_prefix,
        pypi_mirror_secret=(
            module_manifest.pypi_mirror_secret if module_manifest.pypi_mirror_secret else mdo.pypi_mirror_secret
        ),
        npm_mirror_secret=(
            module_manifest.npm_mirror_secret if module_manifest.npm_mirror_secret else mdo.npm_mirror_secret
        ),
    )

    remove_ssm = [
        f"seedfarmer remove moduledata -d {mdo.deployment_manifest.name} -g {mdo.group_name} -m {module_manifest.name}"
    ]

    remove_sf_bundle = [
        (
            f"seedfarmer bundle delete -d {mdo.deployment_manifest.name} -g {mdo.group_name} "
            f"-m {module_manifest.name} -b {mdo.seedfarmer_bucket} || true"
        )
    ]

    export_info = [
        f"export DEPLOYMENT={mdo.deployment_manifest.name}",
        f"export GROUP={mdo.group_name}",
        f"export MODULE={module_manifest.name}",
    ]

    _phases = module_manifest.deploy_spec.destroy.phases
    metadata_env_variable = _param("MODULE_METADATA", use_project_prefix)

    extra_files = {}
    if module_manifest.data_files is not None:
        extra_files = {
            f"module/{data_file.get_bundle_path()}": data_file.get_local_file_path()
            for data_file in module_manifest.data_files
        }

    active_codebuild_image = (
        module_manifest.codebuild_image if module_manifest.codebuild_image is not None else mdo.codebuild_image
    )
    npm_mirror = module_manifest.npm_mirror if module_manifest.npm_mirror is not None else mdo.npm_mirror
    pypi_mirror = module_manifest.pypi_mirror if module_manifest.pypi_mirror is not None else mdo.pypi_mirror
    module_path = os.path.join(config.OPS_ROOT, str(module_manifest.get_local_path()))
    prebuilt_bundle = _prebuilt_bundle_check(mdo)
    try:
        resp_dict_str, _ = _execute_module_commands(
            deployment_name=str(mdo.deployment_manifest.name),
            group_name=mdo.group_name,
            module_manifest_name=module_manifest.name,
            account_id=account_id,
            region=region,
            metadata_env_variable=metadata_env_variable,
            extra_dirs={"module": module_path} if not prebuilt_bundle else None,
            extra_files=extra_files,
            extra_install_commands=["cd module/"] + _phases.install.commands,
            extra_pre_build_commands=["cd module/"] + _phases.pre_build.commands + export_info,
            extra_build_commands=["cd module/"] + _phases.build.commands,
            extra_post_build_commands=["cd module/"] + _phases.post_build.commands + remove_ssm + remove_sf_bundle,
            extra_env_vars=env_vars,
            codebuild_compute_type=module_manifest.deploy_spec.build_type,
            codebuild_role_name=mdo.module_role_name,
            codebuild_image=active_codebuild_image,
            npm_mirror=npm_mirror,
            pypi_mirror=pypi_mirror,
            runtime_versions=get_runtimes(active_codebuild_image),
            prebuilt_bundle=prebuilt_bundle,
        )
        resp = ModuleDeploymentResponse(
            deployment=mdo.deployment_manifest.name,
            group=mdo.group_name,
            module=module_manifest.name,
            status=StatusType.SUCCESS.value,
            codeseeder_metadata=CodeSeederMetadata(**json.loads(resp_dict_str)) if resp_dict_str else None,
        )
    except CodeSeederRuntimeError as csre:
        _logger.error(f"Error Response from CodeSeeder: {csre} - {csre.error_info}")
        l_case_error = {k.lower(): csre.error_info[k] for k in csre.error_info.keys()}
        resp = ModuleDeploymentResponse(
            deployment=mdo.deployment_manifest.name,
            group=mdo.group_name,
            module=module_manifest.name,
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
    metadata_env_variable: str,
    extra_dirs: Optional[Dict[str, Any]] = None,
    extra_files: Optional[Dict[str, Any]] = None,
    extra_install_commands: Optional[List[str]] = None,
    extra_pre_build_commands: Optional[List[str]] = None,
    extra_build_commands: Optional[List[str]] = None,
    extra_post_build_commands: Optional[List[str]] = None,
    extra_env_vars: Optional[Dict[str, Any]] = None,
    codebuild_compute_type: Optional[str] = None,
    codebuild_role_name: Optional[str] = None,
    codebuild_image: Optional[str] = None,
    npm_mirror: Optional[str] = None,
    pypi_mirror: Optional[str] = None,
    runtime_versions: Optional[Dict[str, str]] = None,
    prebuilt_bundle: Optional[str] = None,
) -> Tuple[str, Optional[Dict[str, str]]]:
    session_getter: Optional[Callable[[], Session]] = None

    if not codeseeder.EXECUTING_REMOTELY:

        def _session_getter() -> Session:
            return SessionManager().get_or_create().get_deployment_session(account_id=account_id, region_name=region)

        session_getter = _session_getter

    extra_file_bundle = {config.CONFIG_FILE: os.path.join(config.OPS_ROOT, config.CONFIG_FILE)}
    if extra_files is not None:
        extra_file_bundle.update(extra_files)

    @codeseeder.remote_function(
        config.PROJECT.lower(),
        extra_dirs=extra_dirs,
        extra_install_commands=extra_install_commands,
        extra_pre_build_commands=extra_pre_build_commands,
        extra_build_commands=extra_build_commands,
        extra_post_build_commands=extra_post_build_commands,
        extra_env_vars=extra_env_vars,
        extra_exported_env_vars=[metadata_env_variable],
        codebuild_role=codebuild_role_name,
        codebuild_image=codebuild_image,
        npm_mirror=npm_mirror,
        pypi_mirror=pypi_mirror,
        bundle_id=f"{deployment_name}-{group_name}-{module_manifest_name}",
        codebuild_compute_type=codebuild_compute_type,
        extra_files=extra_file_bundle,
        boto3_session=session_getter,
        runtime_versions=runtime_versions,
        prebuilt_bundle=prebuilt_bundle,
    )
    def _execute_module_commands(
        deployment_name: str,
        group_name: str,
        module_manifest_name: str,
        account_id: str,
        region: str,
        metadata_env_variable: str,
        extra_dirs: Optional[Dict[str, Any]] = None,
        extra_files: Optional[Dict[str, Any]] = None,
        extra_install_commands: Optional[List[str]] = None,
        extra_pre_build_commands: Optional[List[str]] = None,
        extra_build_commands: Optional[List[str]] = None,
        extra_post_build_commands: Optional[List[str]] = None,
        extra_env_vars: Optional[Dict[str, Any]] = None,
        codebuild_compute_type: Optional[str] = None,
        runtime_versions: Optional[Dict[str, str]] = None,
    ) -> str:
        deploy_info = {
            "aws_region": os.environ.get("AWS_DEFAULT_REGION"),
            "aws_account_id": os.environ.get("AWS_ACCOUNT_ID"),
            "aws_partition": os.environ.get("AWS_PARTITION"),
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
                    metadata_env_variable=metadata_env_variable,
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
