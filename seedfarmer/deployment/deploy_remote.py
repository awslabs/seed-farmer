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
from typing import Dict, List, Optional, cast

import yaml
from boto3 import Session

import seedfarmer
import seedfarmer.deployment.codebuild_remote as codebuild_remote
import seedfarmer.errors
import seedfarmer.mgmt.bundle as bundle
import seedfarmer.mgmt.bundle_support as bs
import seedfarmer.services._codebuild as codebuild
from seedfarmer import config
from seedfarmer.commands._runtimes import get_runtimes
from seedfarmer.models.deploy_responses import CodeSeederMetadata, ModuleDeploymentResponse, StatusType
from seedfarmer.models.manifests import ModuleManifest, ModuleParameter
from seedfarmer.models.transfer import ModuleDeployObject
from seedfarmer.services.session_manager import SessionManager
from seedfarmer.types.parameter_types import EnvVar
from seedfarmer.utils import create_output_dir, generate_session_hash

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
    env_vars["SEEDFARMER_VERSION"] = seedfarmer.__version__
    # return env_vars
    return {k: v if isinstance(v, str) else v.value for k, v in env_vars.items()}


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


def _codebuild_install_commands(
    mdo: ModuleDeployObject, module_manifest: ModuleManifest, stack_outputs: Optional[Dict[str, str]]
) -> List[str]:
    npm_mirror = module_manifest.npm_mirror if module_manifest.npm_mirror is not None else mdo.npm_mirror
    pypi_mirror = module_manifest.pypi_mirror if module_manifest.pypi_mirror is not None else mdo.pypi_mirror

    install = [
        "mkdir -p /var/scripts/",
        "mv $CODEBUILD_SRC_DIR/bundle/retrieve_docker_creds.py /var/scripts/retrieve_docker_creds.py || true",
        "/var/scripts/retrieve_docker_creds.py && echo 'Docker logins successful' || echo 'Docker logins failed'",
    ]
    if pypi_mirror is not None:
        install.append("mv $CODEBUILD_SRC_DIR/bundle/pypi_mirror_support.py /var/scripts/pypi_mirror_support.py")
        install.append(f"/var/scripts/pypi_mirror_support.py {pypi_mirror} && echo 'Pypi Mirror Set'")

    if npm_mirror:
        install.append("mv $CODEBUILD_SRC_DIR/bundle/npm_mirror_support.py /var/scripts/npm_mirror_support.py")
        install.append(f"/var/scripts/npm_mirror_support.py {npm_mirror} && echo 'NPM Mirror Set'")

    install.append(
        "if curl -s --head https://astral.sh | grep '200' > /dev/null; then\n"
        "  curl -Ls https://astral.sh/uv/install.sh | sh\n"
        "else\n"
        "  pip install uv\n"
        "fi",
    )
    install.append("export PATH=$PATH:/root/.local/bin")
    install.append("uv venv ~/.venv --python 3.11 --seed")  ## DGRABS - Make this configurable
    install.append(". ~/.venv/bin/activate")

    if stack_outputs and "CodeArtifactDomain" in stack_outputs and "CodeArtifactRepository" in stack_outputs:
        domain = stack_outputs["CodeArtifactDomain"]
        repo = stack_outputs["CodeArtifactRepository"]
        region = str(module_manifest.target_region)
        account_id = str(module_manifest.get_target_account_id())
        install.append(
            "cat <<EOF > ~/.config/uv/uv.toml\n"
            "[[index]]\n"
            'name = "codeartifact"\n'
            f'url = "https://{domain}-{account_id}.d.codeartifact.{region}.amazonaws.com/pypi/{repo}/simple/"\n'
            "EOF"
        )

        install.append(f"aws codeartifact login --tool pip --domain {domain} --repository {repo}")
        install.append(
            "export CODEARTIFACT_AUTH_TOKEN=$(aws codeartifact get-authorization-token "
            f"--domain {domain} "
            f"--domain-owner {account_id} "
            f"--region {region} "
            "--query authorizationToken "
            "--output text)"
        )
        install.append("export UV_INDEX_CODEARTIFACT_USERNAME=aws")
        install.append('export UV_INDEX_CODEARTIFACT_PASSWORD="$CODEARTIFACT_AUTH_TOKEN"')

    install.append(f"uv tool install seed-farmer=={seedfarmer.__version__}")

    return install


def deploy_module(mdo: ModuleDeployObject) -> ModuleDeploymentResponse:
    deployment_manifest = mdo.deployment_manifest
    module_manifest = cast(ModuleManifest, mdo.deployment_manifest.get_module(mdo.group_name, mdo.module_name))
    account_id = str(module_manifest.get_target_account_id())
    region = str(module_manifest.target_region)

    stack_outputs = deployment_manifest.get_region_seedfarmer_metadata(account_id=account_id, region=region)

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

    ## Add in the module to the bundle
    module_path = os.path.join(config.OPS_ROOT, str(module_manifest.get_local_path()))
    dirs = {"module": module_path}
    dirs_tuples = [(v, k) for k, v in dirs.items()]

    ## Add all additional file, don't forget seedfarmer.yaml
    extra_file_bundle = {config.CONFIG_FILE: os.path.join(config.OPS_ROOT, config.CONFIG_FILE)}
    extra_files = {}
    if module_manifest.data_files is not None:
        extra_files = {
            f"module/{data_file.get_bundle_path()}": data_file.get_local_file_path()
            for data_file in module_manifest.data_files
        }
    if extra_files is not None:
        extra_file_bundle.update(extra_files)  # type: ignore [arg-type]

    files_tuples = [(v, f"{k}") for k, v in extra_file_bundle.items()]

    _phases = module_manifest.deploy_spec.deploy.phases
    codebuild_image = (
        module_manifest.codebuild_image if module_manifest.codebuild_image is not None else mdo.codebuild_image
    )

    bundle_id = f"{mdo.deployment_manifest.name}-{mdo.group_name}-{module_manifest.name}"
    ## NOTE: stack_outputs is the seedkit outputs

    _logger.debug("Beginning Remote Execution")

    ## The install commands are specific to AWS Codebuild service
    cmds_install = _codebuild_install_commands(mdo, module_manifest, stack_outputs)

    bundle_zip = bundle.generate_bundle(dirs=dirs_tuples, files=files_tuples, bundle_id=bundle_id)
    buildspec = codebuild.generate_spec(
        cmds_install=cmds_install + ["cd ${CODEBUILD_SRC_DIR}/bundle"] + ["cd module/"] + _phases.install.commands,
        cmds_pre=[". ~/.venv/bin/activate"]
        + ["cd ${CODEBUILD_SRC_DIR}/bundle"]
        + ["cd module/"]
        + _phases.pre_build.commands,
        cmds_build=[". ~/.venv/bin/activate"]
        + ["cd ${CODEBUILD_SRC_DIR}/bundle"]
        + ["cd module/"]
        + _phases.build.commands,
        cmds_post=[". ~/.venv/bin/activate"]
        + ["cd ${CODEBUILD_SRC_DIR}/bundle"]
        + ["cd module/"]
        + _phases.post_build.commands
        + md5_put
        + cs_version_add
        + module_role_name_add
        + githash_add
        + metadata_put
        + store_sf_bundle,
        abort_phases_on_failure=True,
        runtime_versions=get_runtimes(codebuild_image),
    )

    ## Try and force the default install to use uv for older modules
    # commands = buildspec["phases"]["install"]["commands"]
    # for i, cmd in enumerate(commands):
    #     if "pip install -r requirements.txt" == cmd:
    #         commands[i] = cmd.replace(
    #             "pip install -r requirements.txt",
    #             "uv pip install -r requirements.txt"
    #         )

    # Write the deployspec, even if we don't use it...for reference
    buildspec_dir = create_output_dir(f"{bundle_id}/buildspec") if bundle_id else create_output_dir("buildspec")
    with open(os.path.join(buildspec_dir, "buildspec.yaml"), "w") as file:
        file.write(yaml.dump(buildspec))

    overrides = {}
    if codebuild_image:
        overrides["imageOverride"] = codebuild_image
    if mdo.module_role_arn:
        overrides["serviceRoleOverride"] = mdo.module_role_arn
    # if codebuild_environment_type:
    #     overrides["environmentTypeOverride"] = codebuild_environment_type
    if module_manifest.deploy_spec.build_type:
        overrides["computeTypeOverride"] = module_manifest.deploy_spec.build_type
    if env_vars:
        overrides["environmentVariablesOverride"] = [  # type: ignore [assignment]
            {
                "name": k,
                "value": v.value if isinstance(v, EnvVar) else v,
                "type": v.type.value if isinstance(v, EnvVar) else "PLAINTEXT",
            }
            for k, v in env_vars.items()
        ]
    build_info = codebuild_remote.run(
        stack_outputs=stack_outputs,  # type: ignore [arg-type]
        bundle_path=bundle_zip,
        buildspec=buildspec,
        timeout=90,
        overrides=overrides,
        codebuild_log_callback=None,
        session=SessionManager().get_or_create().get_deployment_session(account_id=account_id, region_name=region),
        bundle_id=bundle_id,
        prebuilt_bundle=_prebuilt_bundle_check(mdo=mdo),
    )

    bi = cast(codebuild.BuildInfo, build_info)
    deploy_info = {
        "aws_region": region,
        "aws_account_id": account_id,
        "aws_partition": str(mdo.deployment_manifest._partition),
        "codebuild_build_id": bi.build_id,
    }
    if bi.logs and bi.logs.group_name and bi.logs.stream_name:
        deploy_info["codebuild_log_path"] = f"{bi.logs.group_name}/{bi.logs.stream_name}"

    return ModuleDeploymentResponse(
        deployment=mdo.deployment_manifest.name,
        group=mdo.group_name,
        module=module_manifest.name,
        status=StatusType.SUCCESS.value if bi.status.value in ["SUCCEEDED"] else StatusType.ERROR.value,
        codeseeder_metadata=CodeSeederMetadata(**deploy_info),
    )


def destroy_module(mdo: ModuleDeployObject) -> ModuleDeploymentResponse:
    destroy_manifest = mdo.deployment_manifest
    module_manifest = cast(ModuleManifest, mdo.deployment_manifest.get_module(mdo.group_name, mdo.module_name))
    account_id = str(module_manifest.get_target_account_id())
    region = str(module_manifest.target_region)

    stack_outputs = destroy_manifest.get_region_seedfarmer_metadata(account_id=account_id, region=region)

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
    bundle_id = f"{mdo.deployment_manifest.name}-{mdo.group_name}-{module_manifest.name}"
    prebuilt_bundle = _prebuilt_bundle_check(mdo)
    bundle_zip = None
    if not prebuilt_bundle:
        # regenerate everything that is necessary
        module_path = os.path.join(config.OPS_ROOT, str(module_manifest.get_local_path()))
        dirs = {"module": module_path}
        dirs_tuples = [(v, k) for k, v in dirs.items()]
        extra_file_bundle = {config.CONFIG_FILE: os.path.join(config.OPS_ROOT, config.CONFIG_FILE)}
        extra_files = {}
        if module_manifest.data_files is not None:
            extra_files = {
                f"module/{data_file.get_bundle_path()}": data_file.get_local_file_path()
                for data_file in module_manifest.data_files
            }
        module_path = os.path.join(config.OPS_ROOT, str(module_manifest.get_local_path()))
        if extra_files is not None:
            extra_file_bundle.update(extra_files)  # type: ignore [arg-type]
        files_tuples = [(v, f"{k}") for k, v in extra_file_bundle.items()]
        bundle_zip = bundle.generate_bundle(dirs=dirs_tuples, files=files_tuples, bundle_id=bundle_id)

    codebuild_image = (
        module_manifest.codebuild_image if module_manifest.codebuild_image is not None else mdo.codebuild_image
    )

    cmds_install = _codebuild_install_commands(mdo, module_manifest, stack_outputs)

    buildspec = codebuild.generate_spec(
        cmds_install=cmds_install + ["cd ${CODEBUILD_SRC_DIR}/bundle"] + ["cd module/"] + _phases.install.commands,
        cmds_pre=[". ~/.venv/bin/activate"]
        + ["cd ${CODEBUILD_SRC_DIR}/bundle"]
        + ["cd module/"]
        + _phases.pre_build.commands
        + export_info,
        cmds_build=[". ~/.venv/bin/activate"]
        + ["cd ${CODEBUILD_SRC_DIR}/bundle"]
        + ["cd module/"]
        + _phases.build.commands,
        cmds_post=[". ~/.venv/bin/activate"]
        + ["cd ${CODEBUILD_SRC_DIR}/bundle"]
        + ["cd module/"]
        + _phases.post_build.commands
        + remove_ssm
        + remove_sf_bundle,
        abort_phases_on_failure=True,
        runtime_versions=get_runtimes(codebuild_image),
    )

    buildspec_dir = create_output_dir(f"{bundle_id}/buildspec") if bundle_id else create_output_dir("buildspec")
    with open(os.path.join(buildspec_dir, "buildspec.yaml"), "w") as file:
        file.write(yaml.dump(buildspec))

    overrides = {}
    if codebuild_image:
        overrides["imageOverride"] = codebuild_image
    if mdo.module_role_arn:
        overrides["serviceRoleOverride"] = mdo.module_role_arn
    # if codebuild_environment_type:
    #     overrides["environmentTypeOverride"] = codebuild_environment_type
    if module_manifest.deploy_spec.build_type:
        overrides["computeTypeOverride"] = module_manifest.deploy_spec.build_type
    if env_vars:
        overrides["environmentVariablesOverride"] = [  # type: ignore [assignment]
            {
                "name": k,
                "value": v.value if isinstance(v, EnvVar) else v,
                "type": v.type.value if isinstance(v, EnvVar) else "PLAINTEXT",
            }
            for k, v in env_vars.items()
        ]

    build_info = codebuild_remote.run(
        stack_outputs=stack_outputs,  # type: ignore [arg-type]
        bundle_path=str(bundle_zip),
        buildspec=buildspec,
        timeout=90,
        overrides=overrides,
        codebuild_log_callback=None,
        session=SessionManager().get_or_create().get_deployment_session(account_id=account_id, region_name=region),
        bundle_id=bundle_id,
        prebuilt_bundle=prebuilt_bundle,
    )

    bi = cast(codebuild.BuildInfo, build_info)
    deploy_info = {
        "aws_region": region,
        "aws_account_id": account_id,
        "aws_partition": str(mdo.deployment_manifest._partition),
        "codebuild_build_id": bi.build_id,
    }
    if bi.logs and bi.logs.group_name and bi.logs.stream_name:
        deploy_info["cloudwatch_log_stream"] = f"{bi.logs.group_name}/{bi.logs.stream_name}"

    return ModuleDeploymentResponse(
        deployment=mdo.deployment_manifest.name,
        group=mdo.group_name,
        module=module_manifest.name,
        status=StatusType.SUCCESS.value if bi.status.value in ["SUCCEEDED"] else StatusType.ERROR.value,
        codeseeder_metadata=CodeSeederMetadata(**deploy_info),
    )
