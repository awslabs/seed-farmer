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
import os
from typing import Any, Dict, Optional, cast

import yaml

import seedfarmer.errors
import seedfarmer.messages as messages
import seedfarmer.mgmt.deploy_utils as du
from seedfarmer import config
from seedfarmer.commands import deploy_deployment, destroy_deployment, prime_target_accounts
from seedfarmer.mgmt.module_info import (
    get_test_metadata_input,
    remove_test_metadata_input,
    write_deployment_manifest,
    write_test_metadata_input,
)
from seedfarmer.models.manifests import (
    DeploymentManifest,
    ModuleManifest,
)
from seedfarmer.output_utils import print_bolded
from seedfarmer.services import get_sts_identity_info
from seedfarmer.services.session_manager import SessionManager

_logger: logging.Logger = logging.getLogger(__name__)


def single_module_deploy(
    manifest_path: str,
    group_name: str,
    module_name: str,
    test_deployment_name_prefix: Optional[str] = "test",
    module_metadata: Optional[Dict[str, Any]] = None,
    destroy: Optional[bool] = False,
    profile: Optional[str] = None,
    region_name: Optional[str] = None,
) -> None:
    """
    module-deploy

    Parameters
    ----------

    Raises
    ------
    """

    manifest_path = os.path.join(config.OPS_ROOT, manifest_path)
    with open(manifest_path) as manifest_file:
        deployment_manifest = DeploymentManifest(**yaml.safe_load(manifest_file))
    _logger.debug(deployment_manifest.model_dump())

    # Initialize the SessionManager for the entire project
    session_manager = SessionManager().get_or_create(
        project_name=config.PROJECT,
        profile=profile,
        toolchain_region=deployment_manifest.toolchain_region,
        region_name=region_name,
    )
    _, _, deployment_manifest._partition = get_sts_identity_info(session=session_manager.toolchain_session)

    write_deployment_manifest(
        cast(str, deployment_manifest.name),
        deployment_manifest.model_dump(),
        session=session_manager.toolchain_session,
    )

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
        if module_group.path and module_group.name == group_name:
            try:
                with open(os.path.join(config.OPS_ROOT, module_group.path)) as manifest_file:
                    module_group.modules = [
                        ModuleManifest(**m) for m in yaml.safe_load_all(manifest_file) if m["name"] == module_name
                    ]
                    _logger.debug(module_group.modules)
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
    deployment_manifest.name = f"{test_deployment_name_prefix}-{deployment_manifest.name}"

    prime_target_accounts(deployment_manifest=deployment_manifest, update_seedkit=False, update_project_policy=False)
    if destroy:
        destroy_manifest = du.generate_deployed_manifest(
            deployment_name=deployment_manifest.name, skip_deploy_spec=False
        )
        if destroy_manifest:
            _, _, partition = get_sts_identity_info(session=session_manager.toolchain_session)
            destroy_manifest._partition = partition
            destroy_manifest.validate_and_set_module_defaults()
            active_module = deployment_manifest.groups[0].modules[0]
            active_session = (
                SessionManager()
                .get_or_create()
                .get_deployment_session(
                    account_id=active_module.get_target_account_id(),  # type: ignore
                    region_name=active_module.target_region,  # type: ignore
                )
            )
            testmetadata = get_test_metadata_input(
                deployment=deployment_manifest.name,
                group=deployment_manifest.groups[0].name,
                module=active_module.name,
                params_cache=None,
                session=active_session,
            )
            if testmetadata is not None:
                destroy_manifest.groups[0].modules[0].set_test_metadata(testmetadata)

            destroy_deployment(
                destroy_manifest,
                remove_deploy_manifest=True,
                dryrun=False,
                show_manifest=False,
                remove_seedkit=False,
                test_destroy=True,
            )
            ## Now delete the test module metadata
            active_module = deployment_manifest.groups[0].modules[0]
            active_session = (
                SessionManager()
                .get_or_create()
                .get_deployment_session(
                    account_id=active_module.get_target_account_id(),  # type: ignore
                    region_name=active_module.target_region,  # type: ignore
                )
            )
            remove_test_metadata_input(
                deployment=deployment_manifest.name,
                group=deployment_manifest.groups[0].name,
                module=active_module.name,
                session=active_session,
            )

        else:
            account_id, _, _ = get_sts_identity_info(session=session_manager.toolchain_session)
            region = session_manager.toolchain_session.region_name
            _logger.info(
                """Deployment %s was not found in project %s in account %s and region %s
                        """,
                deployment_manifest.name,
                config.PROJECT,
                account_id,
                region,
            )
            print_bolded(message=messages.no_deployment_found(deployment_name=deployment_manifest.name), color="yellow")

    else:
        if module_metadata:
            active_module = deployment_manifest.groups[0].modules[0]
            active_module.set_test_metadata(module_metadata)
            active_session = (
                SessionManager()
                .get_or_create()
                .get_deployment_session(
                    account_id=active_module.get_target_account_id(),  # type: ignore
                    region_name=active_module.target_region,  # type: ignore
                )
            )
            write_test_metadata_input(
                deployment=deployment_manifest.name,
                group=deployment_manifest.groups[0].name,
                module=active_module.name,
                data=module_metadata,
                session=active_session,
            )
            # Inject the test metadata into the ModuleManifest
            deployment_manifest.groups[0].modules[0] = active_module

        deploy_deployment(
            deployment_manifest=deployment_manifest,
            module_upstream_dep={},
            dryrun=False,
            test_deploy=True,
            show_manifest=False,
        )
