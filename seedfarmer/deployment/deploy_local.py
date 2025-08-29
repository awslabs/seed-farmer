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


import os
from typing import Dict, List, Optional, Union, cast

import seedfarmer
import seedfarmer.deployment.codebuild_local as codebuild_local
import seedfarmer.mgmt.bundle as bundle
import seedfarmer.services._codebuild as codebuild
from seedfarmer import config
from seedfarmer.commands._runtimes import get_runtimes
from seedfarmer.deployment.deploy_base import DeployModule
from seedfarmer.errors import InvalidConfigurationError
from seedfarmer.models.deploy_responses import ModuleDeploymentResponse, StatusType
from seedfarmer.models.manifests import ModuleManifest
from seedfarmer.types.parameter_types import EnvVar
from seedfarmer.utils import LiteralStr, apply_literalstr, create_output_dir, register_literal_str


class DeployLocalModule(DeployModule):
    def _codebuild_install_commands(
        self,
        module_manifest: ModuleManifest,
        stack_outputs: Optional[Dict[str, str]],
        runtimes: Optional[Dict[str, str]] = None,
    ) -> List[Union[str, LiteralStr]]:
        python_version = runtimes.get("python", "3.11") if runtimes else "3.11"
        npm_mirror = module_manifest.npm_mirror if module_manifest.npm_mirror is not None else self.mdo.npm_mirror
        pypi_mirror = module_manifest.pypi_mirror if module_manifest.pypi_mirror is not None else self.mdo.pypi_mirror

        install = []
        install.append("mkdir -p /var/scripts/")
        install.append(
            "mv $CODEBUILD_SRC_DIR/bundle/retrieve_docker_creds.py /var/scripts/retrieve_docker_creds.py || true"
        )
        install.append(
            "/var/scripts/retrieve_docker_creds.py && echo 'Docker logins successful' || echo 'Docker logins failed'"
        )

        if pypi_mirror is not None:
            install.append("mv $CODEBUILD_SRC_DIR/bundle/pypi_mirror_support.py /var/scripts/pypi_mirror_support.py")
            install.append(f"/var/scripts/pypi_mirror_support.py {pypi_mirror} && echo 'Pypi Mirror Set'")

        if npm_mirror:
            install.append("mv $CODEBUILD_SRC_DIR/bundle/npm_mirror_support.py /var/scripts/npm_mirror_support.py")
            install.append(f"/var/scripts/npm_mirror_support.py {npm_mirror} && echo 'NPM Mirror Set'")

        if stack_outputs and "CodeArtifactDomain" in stack_outputs and "CodeArtifactRepository" in stack_outputs:
            ca_domain = stack_outputs["CodeArtifactDomain"]
            ca_repository = stack_outputs["CodeArtifactRepository"]
            region = str(module_manifest.target_region)
            account_id = str(module_manifest.get_target_account_id())
            install.append("mkdir -p ~/.config/uv")
            install.append(
                apply_literalstr(
                    "cat <<EOF > ~/.config/uv/uv.toml\n"
                    "[[index]]\n"
                    'name = "codeartifact"\n'
                    f'url = "https://{ca_domain}-{account_id}.d.codeartifact.{region}.amazonaws.com/pypi/{ca_repository}/simple/"\n'
                    "EOF"
                )
            )

            install.append(
                apply_literalstr(
                    (
                        f"aws codeartifact login --tool pip --domain {ca_domain} "
                        f"--repository {ca_repository} --region {region}"
                    )
                )
            )
            install.append(
                apply_literalstr(
                    "export CODEARTIFACT_AUTH_TOKEN=$(aws codeartifact get-authorization-token "
                    f"--domain {ca_domain} "
                    f"--domain-owner {account_id} "
                    f"--region {region} "
                    "--query authorizationToken "
                    "--output text)"
                )
            )
            install.append("export UV_INDEX_CODEARTIFACT_USERNAME=aws")
            install.append('export UV_INDEX_CODEARTIFACT_PASSWORD="$CODEARTIFACT_AUTH_TOKEN"')

        # needed to make sure both the tool and lib are accessible in the venv
        install.append("pip install uv --disable-pip-version-check --quiet --root-user-action=ignore")
        install.append("export PATH=$PATH:/root/.local/bin")
        install.append(f"uv venv ~/.venv --python {python_version} --seed --quiet")
        install.append(f"uv tool install seed-farmer=={seedfarmer.__version__} --quiet")

        return install

    def deploy_module(self) -> ModuleDeploymentResponse:
        deployment_manifest = self.mdo.deployment_manifest
        group = self.mdo.group_name
        deployment_manifest = self.mdo.deployment_manifest
        module_manifest = cast(
            ModuleManifest, self.mdo.deployment_manifest.get_module(str(self.mdo.group_name), str(self.mdo.module_name))
        )
        use_project_prefix = not module_manifest.deploy_spec.publish_generic_env_variables  # type: ignore [union-attr]
        yaml = register_literal_str()

        if module_manifest.deploy_spec is None or module_manifest.deploy_spec.deploy is None:
            raise InvalidConfigurationError("Missing `deploy` in module's deployspec.yaml")

        account_id = str(module_manifest.get_target_account_id())
        region = str(module_manifest.target_region)
        env_vars = self._env_vars()

        metadata_env_var = DeployModule.seedfarmer_param("MODULE_METADATA", None, use_project_prefix)

        metadata_put = [
            f"if [[ -f {metadata_env_var} ]]; then export {metadata_env_var}=$(cat {metadata_env_var}); fi",
            (
                f"echo ${metadata_env_var} | seedfarmer store moduledata "
                f"-d {deployment_manifest.name} -g {group} -m {module_manifest.name} --region {region} --local"
            ),
        ]

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

        extra_file_bundle = {config.CONFIG_FILE: os.path.join(config.OPS_ROOT, config.CONFIG_FILE)}
        module_path = os.path.join(config.OPS_ROOT, str(module_manifest.get_local_path()))
        dirs = {"module": module_path}
        dirs_tuples = [(v, k) for k, v in dirs.items()]

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
        codebuild_image = (
            codebuild_image if codebuild_image else "public.ecr.aws/codebuild/amazonlinux2-x86_64-standard:5.0"
        )

        if codebuild_image.startswith("aws/codebuild/"):
            codebuild_image = f"public.ecr.{codebuild_image}"

        bundle_id = f"{self.mdo.deployment_manifest.name}-{self.mdo.group_name}-{module_manifest.name}"
        output_override = f".seedfarmerlocal-{bundle_id}"

        local_path = create_output_dir(f"{bundle_id}", output_override)
        bundle.generate_bundle(dirs=dirs_tuples, files=files_tuples, bundle_id=bundle_id, path_override=output_override)
        stack_outputs = deployment_manifest.get_region_seedfarmer_metadata(account_id=account_id, region=region)

        runtime_versions = get_runtimes(codebuild_image=codebuild_image, runtime_overrides=self.mdo.runtime_overrides)
        install_commands = self._codebuild_install_commands(module_manifest, stack_outputs, runtime_versions)

        buildspec = codebuild.generate_spec(
            cmds_install=install_commands
            + [". ~/.venv/bin/activate"]
            + ["cd ${CODEBUILD_SRC_DIR}/bundle"]
            + ["cd module/"]
            + _phases.install.commands,
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
            + metadata_put
            + ["cd ${CODEBUILD_SRC_DIR}"]
            + ["chmod -R 777 ${CODEBUILD_SRC_DIR}"],  # makes sure output isn't locked
            abort_phases_on_failure=True,
            runtime_versions=runtime_versions,
        )

        buildspec_dir = create_output_dir(f"{bundle_id}/buildspec", output_override)
        with open(os.path.join(buildspec_dir, "buildspec.yaml"), "w") as file:
            # file.write(yaml.dump(buildspec))
            yaml.dump(buildspec, file)

        build_info = codebuild_local.run(
            local_path, {k: v.value if isinstance(v, EnvVar) else v for k, v in env_vars.items()}, codebuild_image
        )

        return ModuleDeploymentResponse(
            deployment=self.mdo.deployment_manifest.name,
            group=self.mdo.group_name,
            module=module_manifest.name,
            status=StatusType.SUCCESS.value if build_info.status.value in ["SUCCEEDED"] else StatusType.ERROR.value,
        )

    def destroy_module(self) -> ModuleDeploymentResponse:
        deployment_name = self.mdo.deployment_manifest.name
        group_name = self.mdo.group_name
        module_name = self.mdo.module_name

        module_manifest = cast(
            ModuleManifest, self.mdo.deployment_manifest.get_module(str(group_name), str(module_name))
        )
        use_project_prefix = not module_manifest.deploy_spec.publish_generic_env_variables  # type: ignore [union-attr]
        yaml = register_literal_str()

        if module_manifest.deploy_spec is None or module_manifest.deploy_spec.destroy is None:
            raise seedfarmer.errors.InvalidConfigurationError(
                f"Missing `destroy` in module: {module_manifest.name} with deployspec.yaml"
            )

        account_id = str(module_manifest.get_target_account_id())
        region = str(module_manifest.target_region)
        env_vars = self._env_vars()

        metadata_env_var = DeployModule.seedfarmer_param("MODULE_METADATA", None, use_project_prefix)

        metadata_put = [
            f"if [[ -f {metadata_env_var} ]]; then export {metadata_env_var}=$(cat {metadata_env_var}); fi",
        ]
        remove_ssm = [
            (
                f"seedfarmer remove moduledata "
                f"-d {deployment_name} -g {group_name} -m {module_manifest.name} --region {region} --local"
            )
        ]
        export_info = [
            f"export DEPLOYMENT={self.mdo.deployment_manifest.name}",
            f"export GROUP={self.mdo.group_name}",
            f"export MODULE={module_manifest.name}",
        ]

        extra_file_bundle = {config.CONFIG_FILE: os.path.join(config.OPS_ROOT, config.CONFIG_FILE)}
        module_path = os.path.join(config.OPS_ROOT, str(module_manifest.get_local_path()))
        dirs = {"module": module_path}
        dirs_tuples = [(v, k) for k, v in dirs.items()]
        extra_files = {}
        if module_manifest.data_files is not None:
            extra_files = {
                f"module/{data_file.get_bundle_path()}": data_file.get_local_file_path()
                for data_file in module_manifest.data_files
            }
        if extra_files is not None:
            extra_file_bundle.update(extra_files)  # type: ignore [arg-type]
        files_tuples = [(v, f"{k}") for k, v in extra_file_bundle.items()]

        codebuild_image = (
            module_manifest.codebuild_image if module_manifest.codebuild_image is not None else self.mdo.codebuild_image
        )
        codebuild_image = (
            codebuild_image if codebuild_image else "public.ecr.aws/codebuild/amazonlinux2-x86_64-standard:5.0"
        )

        if codebuild_image.startswith("aws/codebuild/"):
            codebuild_image = f"public.ecr.{codebuild_image}"

        bundle_id = f"{deployment_name}-{group_name}-{module_name}"
        output_override = f".seedfarmerlocal-{bundle_id}"

        local_path = create_output_dir(f"{bundle_id}", output_override)
        bundle.generate_bundle(dirs=dirs_tuples, files=files_tuples, bundle_id=bundle_id, path_override=output_override)

        _phases = module_manifest.deploy_spec.destroy.phases
        stack_outputs = self.mdo.deployment_manifest.get_region_seedfarmer_metadata(
            account_id=account_id, region=region
        )

        runtime_versions = get_runtimes(codebuild_image=codebuild_image, runtime_overrides=self.mdo.runtime_overrides)
        install_commands = self._codebuild_install_commands(module_manifest, stack_outputs, runtime_versions)

        buildspec = codebuild.generate_spec(
            cmds_install=install_commands
            + [". ~/.venv/bin/activate"]
            + ["cd ${CODEBUILD_SRC_DIR}/bundle"]
            + ["cd module/"]
            + _phases.install.commands,
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
            + metadata_put
            + remove_ssm
            + ["cd ${CODEBUILD_SRC_DIR}"]
            + ["chmod -R 777 ${CODEBUILD_SRC_DIR}"],  # makes sure output isn't locked
            abort_phases_on_failure=True,
            runtime_versions=runtime_versions,
        )

        buildspec_dir = create_output_dir(f"{bundle_id}/buildspec", output_override)
        with open(os.path.join(buildspec_dir, "buildspec.yaml"), "w") as file:
            yaml.dump(buildspec, file)

        build_info = codebuild_local.run(
            local_path, {k: v.value if isinstance(v, EnvVar) else v for k, v in env_vars.items()}, codebuild_image
        )

        return ModuleDeploymentResponse(
            deployment=deployment_name,
            group=group_name,
            module=module_name,
            status=StatusType.SUCCESS.value if build_info.status.value in ["SUCCEEDED"] else StatusType.ERROR.value,
        )
