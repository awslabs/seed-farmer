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

import concurrent.futures
import logging
import os
import threading
from typing import Optional, cast

import yaml

import seedfarmer.errors
from seedfarmer import config
from seedfarmer.commands._parameter_commands import load_parameter_values
from seedfarmer.deployment.deploy_local import DeployLocalModule
from seedfarmer.mgmt.module_info import (
    get_deployspec_path,
)
from seedfarmer.models import DeploySpec
from seedfarmer.models.deploy_responses import ModuleDeploymentResponse
from seedfarmer.models.manifests import DeploymentManifest, ModuleManifest
from seedfarmer.models.transfer import ModuleDeployObject
from seedfarmer.output_utils import (
    print_errored_modules_build_info,
    print_modules_build_info,
)
from seedfarmer.services._service_utils import get_region, get_sts_identity_info
from seedfarmer.services.session_manager import SessionManagerLocal
from seedfarmer.utils import delete_all_output_dir

_logger: logging.Logger = logging.getLogger(__name__)


def apply_local(
    deployment_manifest_path: str,
    profile: Optional[str] = None,
    region_name: Optional[str] = None,
    dryrun: bool = False,
) -> None:
    SessionManagerLocal().get_or_create(
        profile=profile,
        region_name=region_name,
    )

    manifest_path = os.path.join(config.OPS_ROOT, deployment_manifest_path)
    with open(manifest_path) as manifest_file:
        deployment_manifest = DeploymentManifest(**yaml.safe_load(manifest_file))

    for module_group in deployment_manifest.groups:
        if module_group.path and module_group.modules:
            _logger.debug("module_group: %s", module_group)
            raise seedfarmer.errors.InvalidConfigurationError(
                "Only one of the `path` or `modules` attributes can be defined on a Group"
            )
        if not module_group.path and not module_group.modules:
            _logger.debug("module_group: %s", module_group)
            raise seedfarmer.errors.InvalidConfigurationError(
                "One of the `path` or `modules` attributes must be defined on a Group"
            )
        if module_group.path:
            try:
                with open(os.path.join(config.OPS_ROOT, module_group.path)) as manifest_file:
                    module_group.modules = [ModuleManifest(**m) for m in yaml.safe_load_all(manifest_file)]
            except FileNotFoundError as fe:
                _logger.error(fe)
                _logger.error(f"Cannot parse a file at {os.path.join(config.OPS_ROOT, module_group.path)}")
                _logger.error("Verify (in deployment manifest) that relative path to the module manifest is correct")
                raise seedfarmer.errors.InvalidPathError(f"Cannot parse manifest file path at {module_group.path}")
            except Exception as e:
                _logger.error(e)
                _logger.error("Verify that elements are filled out and yaml compliant")
                raise seedfarmer.errors.InvalidManifestError("Cannot parse manifest properly")

    deployment_manifest.validate_and_set_module_defaults()

    # add in the deployspec
    for group in deployment_manifest.groups:
        for module in group.modules:
            deployspec_path = get_deployspec_path(str(module.get_local_path()))
            with open(deployspec_path) as module_spec_file:
                module.deploy_spec = DeploySpec(**yaml.safe_load(module_spec_file))

    def _execute_deploy_local(mdo: ModuleDeployObject) -> ModuleDeploymentResponse:
        module_manifest = cast(
            ModuleManifest, mdo.deployment_manifest.get_module(str(mdo.group_name), str(mdo.module_name))
        )
        session_manager = SessionManagerLocal()
        session = session_manager.get_or_create().get_deployment_session(account_id="NotUsed", region_name="NotUsed")
        region = get_region(session)
        account_id, _, _ = get_sts_identity_info(session)
        module_manifest.set_target_account_id(account_id)
        module_manifest.target_region = region
        mdo.parameters = load_parameter_values(
            deployment_name=cast(str, mdo.deployment_manifest.name),
            parameters=module_manifest.parameters,
            deployment_manifest=mdo.deployment_manifest,
            target_account=account_id,
            target_region=region,
            session_manager=session_manager,
        )

        if module_manifest.deploy_spec is None:
            raise seedfarmer.errors.InvalidManifestError(
                f"""Invalid value for ModuleManifest.deploy_spec in group {mdo.group_name}
                and module : {mdo.module_name}"""
            )
        print(mdo.module_name)
        dep = DeployLocalModule(mdo)
        return dep.deploy_module()

    delete_all_output_dir(".seedfarmerlocal")

    for _group in deployment_manifest.groups:
        if len(_group.modules) > 0:
            threads = _group.concurrency if _group.concurrency else len(_group.modules)
            with concurrent.futures.ThreadPoolExecutor(max_workers=threads, thread_name_prefix="Deploy") as workers:

                def _exec_deploy_local(mdo: ModuleDeployObject) -> ModuleDeploymentResponse:
                    threading.current_thread().name = (
                        f"{threading.current_thread().name}-{mdo.group_name}_{mdo.module_name}"
                    ).replace("_", "-")
                    return _execute_deploy_local(mdo)

                mdos = []
                for _module in _group.modules:
                    if _module and _module.deploy_spec:
                        mdo = ModuleDeployObject(
                            deployment_manifest=deployment_manifest,
                            group_name=_group.name,
                            module_name=_module.name,
                        )
                        mdos.append(mdo)
                deploy_response = list(workers.map(_exec_deploy_local, mdos))
                _logger.debug(deploy_response)
                (
                    print_modules_build_info("Build Info Debug Data", deploy_response)  # type: ignore
                    if _logger.isEnabledFor(logging.DEBUG)
                    else None
                )
                for dep_resp_object in deploy_response:
                    if dep_resp_object.status in ["ERROR", "error", "Error"]:
                        _logger.error("At least one module failed to deploy...exiting deployment")
                        print_errored_modules_build_info(
                            "These modules had errors deploying",
                            deploy_response,  # type: ignore
                        )
                        raise seedfarmer.errors.ModuleDeploymentError(
                            error_message="At least one module failed to deploy...exiting deployment"
                        )
                    else:
                        print(dep_resp_object)
