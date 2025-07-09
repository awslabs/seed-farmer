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


import logging
import os
from typing import Dict, List, Optional, cast

import seedfarmer
import seedfarmer.deployment.codebuild_remote as codebuild_remote
import seedfarmer.errors
import seedfarmer.mgmt.bundle as bundle
import seedfarmer.services._codebuild as codebuild
from seedfarmer import config
from seedfarmer.commands._runtimes import get_runtimes
from seedfarmer.deployment.deploy_base import DeployModule
from seedfarmer.models.deploy_responses import CodeBuildMetadata, ModuleDeploymentResponse, StatusType
from seedfarmer.models.manifests import ModuleManifest
from seedfarmer.services.session_manager import SessionManager
from seedfarmer.types.parameter_types import EnvVar

# import yaml
from seedfarmer.utils import apply_literalstr, create_output_dir, register_literal_str

_logger: logging.Logger = logging.getLogger(__name__)


class DeployRemoteModule(DeployModule):
    def _codebuild_install_commands(
        self,
        module_manifest: ModuleManifest,
        stack_outputs: Optional[Dict[str, str]],
        runtimes: Optional[Dict[str, str]] = None,
    ) -> List[str]:
        npm_mirror = module_manifest.npm_mirror if module_manifest.npm_mirror is not None else self.mdo.npm_mirror
        pypi_mirror = module_manifest.pypi_mirror if module_manifest.pypi_mirror is not None else self.mdo.pypi_mirror
        python_version = runtimes.get("python", "3.11") if runtimes else "3.11"

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
        install.append(f"uv venv ~/.venv --python {python_version} --seed")
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

            install.append(f"aws codeartifact login --tool pip --domain {domain} --repository {repo} --region {region}")
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

        # needed to make sure both the tool and lib are accessible in the venv
        install.append("uv pip install pip")
        install.append(f"uv tool install seed-farmer=={seedfarmer.__version__}")

        return install

    def deploy_module(self) -> ModuleDeploymentResponse:
        deployment_manifest = self.mdo.deployment_manifest
        group = self.mdo.group_name
        module_manifest = cast(
            ModuleManifest, self.mdo.deployment_manifest.get_module(str(self.mdo.group_name), str(self.mdo.module_name))
        )
        # Use this yaml so that the spec is pretty
        yaml = register_literal_str()
        account_id = str(module_manifest.get_target_account_id())
        region = str(module_manifest.target_region)

        stack_outputs = deployment_manifest.get_region_seedfarmer_metadata(account_id=account_id, region=region)

        if module_manifest.deploy_spec is None or module_manifest.deploy_spec.deploy is None:
            raise seedfarmer.errors.InvalidConfigurationError("Missing `deploy` in module's deployspec.yaml")

        use_project_prefix = not module_manifest.deploy_spec.publish_generic_env_variables
        env_vars = self._env_vars()

        env_vars[DeployModule.seedfarmer_param("MODULE_MD5", None, use_project_prefix)] = (
            module_manifest.bundle_md5 if module_manifest.bundle_md5 is not None else ""
        )

        md5_put = [
            (
                f"echo {module_manifest.bundle_md5} | seedfarmer store md5 -d {self.mdo.deployment_manifest.name} "
                f"-g {self.mdo.group_name} -m {module_manifest.name} -t bundle --region {region} --local"
            )
        ]

        metadata_env_var = DeployModule.seedfarmer_param("MODULE_METADATA", None, use_project_prefix)
        sf_version_add = [f"seedfarmer metadata add -k SeedFarmerDeployed -v {seedfarmer.__version__} || true"]
        module_role_name_add = [
            f"seedfarmer metadata add -k ModuleDeploymentRoleName -v {self.mdo.module_role_name} || true"
        ]
        githash_add = (
            [f"seedfarmer metadata add -k SeedFarmerModuleCommitHash -v {module_manifest.commit_hash} || true"]
            if module_manifest.commit_hash
            else []
        )

        logstream = apply_literalstr("""build_id_only=$(echo "$CODEBUILD_BUILD_ID" | cut -d':' -f2)
        project_name=$(echo "$CODEBUILD_PROJECT_ARN" | awk -F'/' '{print $2}')
        log_stream=$(aws logs describe-log-streams \\
        --log-group-name "/aws/codebuild/$project_name" \\
        --output json \\
        --query "logStreams[?contains(logStreamName, \\`$build_id_only\\`)].logStreamName" \\
        | jq -r 'map(select(. != null)) | .[0]') || true
        """)
        add_cb_metadata = [
            "seedfarmer metadata add -k CodeBuildBuildUrl -v $CODEBUILD_BUILD_URL",
            logstream,
            'seedfarmer metadata add -k CloudWatchLogStream -v "/aws/codebuild/$project_name/$log_stream" || true',
        ]

        metadata_put = [
            f"if [[ -f {metadata_env_var} ]]; then export {metadata_env_var}=$(cat {metadata_env_var}); fi",
            (
                f"echo ${metadata_env_var} | seedfarmer store moduledata "
                f"-d {deployment_manifest.name} -g {group} -m {module_manifest.name} --region {region} --local"
            ),
        ]
        store_sf_bundle = [
            (
                f"seedfarmer bundle store -d {deployment_manifest.name} -g {group} -m {module_manifest.name} "
                f"-o $CODEBUILD_SOURCE_REPO_URL -b {self.mdo.seedfarmer_bucket} --region {region} || true"
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
            module_manifest.codebuild_image if module_manifest.codebuild_image is not None else self.mdo.codebuild_image
        )

        bundle_id = f"{self.mdo.deployment_manifest.name}-{self.mdo.group_name}-{module_manifest.name}"
        ## NOTE: stack_outputs is the seedkit outputs

        _logger.debug("Beginning Remote Execution")

        runtime_versions = get_runtimes(codebuild_image=codebuild_image, runtime_overrides=self.mdo.runtime_overrides)
        cmds_install = self._codebuild_install_commands(module_manifest, stack_outputs, runtime_versions)

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
            + sf_version_add
            + module_role_name_add
            + githash_add
            + add_cb_metadata
            + metadata_put
            + store_sf_bundle,
            abort_phases_on_failure=True,
            runtime_versions=runtime_versions,
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
            # file.write(yaml.dump(buildspec))
            yaml.dump(buildspec, file)

        overrides = {}
        if codebuild_image:
            overrides["imageOverride"] = codebuild_image
        if self.mdo.module_role_arn:
            overrides["serviceRoleOverride"] = self.mdo.module_role_arn
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
            timeout=120,
            overrides=overrides,
            codebuild_log_callback=None,
            session=SessionManager().get_or_create().get_deployment_session(account_id=account_id, region_name=region),
            bundle_id=bundle_id,
            prebuilt_bundle=None,  # NEVER CHECK FOR THIS BUNDLE ON DEPLOY
            yaml_dumper=yaml,
        )

        bi = cast(codebuild.BuildInfo, build_info)
        deploy_info = {
            "aws_region": region,
            "aws_account_id": account_id,
            "aws_partition": str(self.mdo.deployment_manifest._partition),
            "codebuild_build_id": bi.build_id,
        }
        if bi.logs and bi.logs.group_name and bi.logs.stream_name:
            deploy_info["codebuild_log_path"] = f"{bi.logs.group_name}/{bi.logs.stream_name}"

        return ModuleDeploymentResponse(
            deployment=self.mdo.deployment_manifest.name,
            group=self.mdo.group_name,
            module=module_manifest.name,
            status=StatusType.SUCCESS.value if bi.status.value in ["SUCCEEDED"] else StatusType.ERROR.value,
            codebuild_metadata=CodeBuildMetadata(**deploy_info),
        )

    def destroy_module(self) -> ModuleDeploymentResponse:
        import yaml

        destroy_manifest = self.mdo.deployment_manifest
        module_manifest = cast(
            ModuleManifest, self.mdo.deployment_manifest.get_module(str(self.mdo.group_name), str(self.mdo.module_name))
        )
        account_id = str(module_manifest.get_target_account_id())
        region = str(module_manifest.target_region)
        deployment_name = self.mdo.deployment_manifest.name

        stack_outputs = destroy_manifest.get_region_seedfarmer_metadata(account_id=account_id, region=region)

        if module_manifest.deploy_spec is None or module_manifest.deploy_spec.destroy is None:
            raise seedfarmer.errors.InvalidConfigurationError(
                f"Missing `destroy` in module: {module_manifest.name} with deployspec.yaml"
            )

        env_vars = self._env_vars()
        remove_ssm = [
            (
                f"seedfarmer remove moduledata "
                f"-d {deployment_name} -g {self.mdo.group_name} -m {module_manifest.name} --region {region} --local"
            )
        ]

        remove_sf_bundle = [
            (
                f"seedfarmer bundle delete -d {self.mdo.deployment_manifest.name} -g {self.mdo.group_name} "
                f"-m {module_manifest.name} -b {self.mdo.seedfarmer_bucket} --region {region} || true"
            )
        ]

        export_info = [
            f"export DEPLOYMENT={self.mdo.deployment_manifest.name}",
            f"export GROUP={self.mdo.group_name}",
            f"export MODULE={module_manifest.name}",
        ]

        _phases = module_manifest.deploy_spec.destroy.phases
        bundle_id = f"{self.mdo.deployment_manifest.name}-{self.mdo.group_name}-{module_manifest.name}"
        prebuilt_bundle = self._prebuilt_bundle_check()
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
            module_manifest.codebuild_image if module_manifest.codebuild_image is not None else self.mdo.codebuild_image
        )

        runtime_versions = get_runtimes(codebuild_image=codebuild_image, runtime_overrides=self.mdo.runtime_overrides)
        cmds_install = self._codebuild_install_commands(module_manifest, stack_outputs, runtime_versions)

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
            runtime_versions=runtime_versions,
        )

        buildspec_dir = create_output_dir(f"{bundle_id}/buildspec") if bundle_id else create_output_dir("buildspec")
        with open(os.path.join(buildspec_dir, "buildspec.yaml"), "w") as file:
            file.write(yaml.dump(buildspec))

        overrides = {}
        if codebuild_image:
            overrides["imageOverride"] = codebuild_image
        if self.mdo.module_role_arn:
            overrides["serviceRoleOverride"] = self.mdo.module_role_arn
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
            "aws_partition": str(self.mdo.deployment_manifest._partition),
            "codebuild_build_id": bi.build_id,
        }
        if bi.logs and bi.logs.group_name and bi.logs.stream_name:
            deploy_info["cloudwatch_log_stream"] = f"{bi.logs.group_name}/{bi.logs.stream_name}"

        return ModuleDeploymentResponse(
            deployment=self.mdo.deployment_manifest.name,
            group=self.mdo.group_name,
            module=module_manifest.name,
            status=StatusType.SUCCESS.value if bi.status.value in ["SUCCEEDED"] else StatusType.ERROR.value,
            codebuild_metadata=CodeBuildMetadata(**deploy_info),
        )
