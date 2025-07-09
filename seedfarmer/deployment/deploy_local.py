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
from seedfarmer.utils import LiteralStr, apply_literalstr, create_output_dir, register_literal_str


class DeployLocalModule(DeployModule):
    def _codebuild_install_commands(
        self,
        account_id: str,
        region: str,
        ca_domain: Optional[str] = None,
        ca_repository: Optional[str] = None,
        runtimes: Optional[Dict[str, str]] = None,
    ) -> List[Union[str, LiteralStr]]:
        python_version = runtimes.get("python", "3.11") if runtimes else "3.11"
        install = []
        uv_install = apply_literalstr("""if curl -s --head https://astral.sh | grep '200' > /dev/null; then
        curl -Ls https://astral.sh/uv/install.sh | sh
    else
        pip install uv
    fi
    """)
        install.append(apply_literalstr(uv_install))
        install.append(apply_literalstr("export PATH=$PATH:/root/.local/bin"))
        install.append(apply_literalstr(f"uv venv ~/.venv --python {python_version} --seed"))
        install.append(apply_literalstr(". ~/.venv/bin/activate"))

        if ca_domain and ca_repository:
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
            install.append(apply_literalstr("export UV_INDEX_CODEARTIFACT_USERNAME=aws"))
            install.append(apply_literalstr('export UV_INDEX_CODEARTIFACT_PASSWORD="$CODEARTIFACT_AUTH_TOKEN"'))

        # needed to make sure both the tool and lib are accessible in the venv
        install.append(apply_literalstr("uv pip install pip"))
        install.append(apply_literalstr(f"uv tool install seed-farmer=={seedfarmer.__version__}"))

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

        # docker_network="pypi-net"
        # local_pypi_endpoint="http://pypiserver:8080/simple"

        bundle_id = f"{self.mdo.deployment_manifest.name}-{self.mdo.group_name}-{module_manifest.name}"
        output_override = f".seedfarmerlocal-{bundle_id}"

        local_path = create_output_dir(f"{bundle_id}", output_override)
        bundle.generate_bundle(dirs=dirs_tuples, files=files_tuples, bundle_id=bundle_id, path_override=output_override)
        stack_outputs = deployment_manifest.get_region_seedfarmer_metadata(account_id=account_id, region=region)
        ca_domain = (
            stack_outputs["CodeArtifactDomain"] if stack_outputs and "CodeArtifactDomain" in stack_outputs else None
        )
        ca_repository = (
            stack_outputs["CodeArtifactRepository"]
            if stack_outputs and "CodeArtifactRepository" in stack_outputs
            else None
        )

        runtime_versions = get_runtimes(codebuild_image=codebuild_image, runtime_overrides=self.mdo.runtime_overrides)
        install_commands = self._codebuild_install_commands(
            account_id, region, ca_domain, ca_repository, runtime_versions
        )

        buildspec = codebuild.generate_spec(
            cmds_install=install_commands
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

        build_info = codebuild_local.run(local_path, env_vars, codebuild_image)

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
        ca_domain = (
            stack_outputs["CodeArtifactDomain"] if stack_outputs and "CodeArtifactDomain" in stack_outputs else None
        )
        ca_repository = (
            stack_outputs["CodeArtifactRepository"]
            if stack_outputs and "CodeArtifactRepository" in stack_outputs
            else None
        )

        runtime_versions = get_runtimes(codebuild_image=codebuild_image, runtime_overrides=self.mdo.runtime_overrides)
        install_commands = self._codebuild_install_commands(
            account_id, region, ca_domain, ca_repository, runtime_versions
        )

        buildspec = codebuild.generate_spec(
            cmds_install=install_commands
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

        build_info = codebuild_local.run(local_path, env_vars, codebuild_image)

        return ModuleDeploymentResponse(
            deployment=deployment_name,
            group=group_name,
            module=module_name,
            status=StatusType.SUCCESS.value if build_info.status.value in ["SUCCEEDED"] else StatusType.ERROR.value,
        )
