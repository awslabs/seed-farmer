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
import hashlib
import json
import logging
import os
from typing import Any, Dict, List, Optional, cast

import checksumdir
import yaml

import seedfarmer.mgmt.deploy_utils as du
from seedfarmer import commands, config
from seedfarmer.commands._parameter_commands import load_parameter_values
from seedfarmer.mgmt.module_info import (
    _get_deployspec_path,
    _get_modulestack_path,
    get_module_metadata,
    remove_deployed_deployment_manifest,
    remove_deployment_manifest,
    write_deployment_manifest,
)
from seedfarmer.models.deploy_responses import ModuleDeploymentResponse, StatusType
from seedfarmer.models.manifests import DeploymentManifest, DeploySpec, ModuleManifest, ModulesManifest
from seedfarmer.output_utils import (
    _print_modules,
    print_bolded,
    print_errored_modules,
    print_manifest_inventory,
    print_manifest_json,
)
from seedfarmer.services.session_manager import SessionManager

_logger: logging.Logger = logging.getLogger(__name__)


def _execute_deploy(
    d_name: str,
    g_name: str,
    m: ModuleManifest,
    deployment_manifest: DeploymentManifest,
    d_secret: Optional[str] = None,
    permission_boundary_arn: Optional[str] = None,
) -> ModuleDeploymentResponse:
    parameters = load_parameter_values(
        deployment_name=d_name, parameters=m.parameters, deployment_manifest=deployment_manifest
    )

    target_account_id = cast(str, m.get_target_account_id())
    target_region = cast(str, m.target_region)
    # Deploys the IAM role per module
    commands.deploy_module_stack(
        _get_modulestack_path(m.path),
        d_name,
        g_name,
        m.name,
        target_account_id,
        target_region,
        parameters,
        docker_credentials_secret=d_secret,
        permission_boundary_arn=permission_boundary_arn,
    )

    #   Get the current module's SSM if it was alreadly loaded...
    session = (
        SessionManager().get_or_create().get_deployment_session(account_id=target_account_id, region_name=target_region)
    )
    module_metadata = json.dumps(get_module_metadata(d_name, g_name, m.name, session=session))

    if m.deploy_spec is None:
        raise ValueError(f"Invalid value for ModuleManifest.deploy_spec in group {g_name} and module : {m.name}")

    return commands.deploy_module(
        deployment_name=d_name,
        group_name=g_name,
        module_path=os.path.join(config.OPS_ROOT, m.path),
        module_deploy_spec=m.deploy_spec,
        module_manifest_name=m.name,
        account_id=target_account_id,
        region=target_region,
        parameters=parameters,
        module_metadata=module_metadata,
        module_bundle_md5=m.bundle_md5,
        docker_credentials_secret=d_secret,
        permission_boundary_arn=permission_boundary_arn,
    )


def _execute_destroy(
    d_name: str,
    g_name: str,
    m: ModuleManifest,
    deployment_manifest: DeploymentManifest,
    d_secret: Optional[str] = None,
) -> Optional[ModuleDeploymentResponse]:
    if m.deploy_spec is None:
        raise ValueError(f"Invalid value for ModuleManifest.deploy_spec in group {g_name} and module : {m.name}")

    resp = commands.destroy_module(
        deployment_name=d_name,
        group_name=g_name,
        module_path=m.path,
        module_deploy_spec=m.deploy_spec,
        module_manifest_name=m.name,
        account_id=cast(str, m.get_target_account_id()),
        region=cast(str, m.target_region),
        parameters=load_parameter_values(
            deployment_name=d_name, parameters=m.parameters, deployment_manifest=deployment_manifest
        ),
        module_metadata=None,
    )

    if resp.status == StatusType.SUCCESS.value:
        commands.destroy_module_stack(
            d_name,
            g_name,
            m.name,
            account_id=cast(str, m.get_target_account_id()),
            region=cast(str, m.target_region),
            docker_credentials_secret=d_secret,
        )

    # TODO: Confirm whether this is needed, commenting for now
    # if not get_deployed_modules(deployment=d_name, group=g_name):
    #     remove_group_info(d_name, g_name)
    return resp


def _deploy_deployment_is_not_dry_run(
    deployment_manifest: DeploymentManifest,
    deployment_manifest_wip: DeploymentManifest,
    deployment_name: str,
    groups_to_deploy: List[ModulesManifest],
) -> None:
    if groups_to_deploy:
        deployment_manifest_wip.groups = groups_to_deploy
        print_manifest_inventory(
            f"Modules scheduled to be deployed (created or updated): {deployment_manifest_wip.name}",
            deployment_manifest_wip,
            True,
        )
        if _logger.isEnabledFor(logging.DEBUG):
            _logger.debug(
                "DeploymentManifest for deploy after filter =  %s", json.dumps(deployment_manifest_wip.dict())
            )
        for _group in deployment_manifest_wip.groups:
            if len(_group.modules) > 0:
                threads = _group.concurrency if _group.concurrency else len(_group.modules)
                with concurrent.futures.ThreadPoolExecutor(max_workers=threads) as workers:

                    def _exec_deploy(args: Dict[str, Any]) -> ModuleDeploymentResponse:
                        return _execute_deploy(
                            args["d_name"],
                            args["g"],
                            args["m"],
                            deployment_manifest,
                            args["d_secret"],
                            args["permission_boundary_arn"],
                        )

                    params = [
                        {
                            "d_name": deployment_name,
                            "g": _group.name,
                            "m": _module,
                            "d_secret": deployment_manifest_wip.get_parameter_value(
                                "dockerCredentialsSecret",
                                account_alias=_module.target_account,
                                region=_module.target_region,
                            ),
                            "permission_boundary_arn": deployment_manifest_wip.get_parameter_value(
                                "permissionBoundaryArn",
                                account_alias=_module.target_account,
                                region=_module.target_region,
                            ),
                        }
                        for _module in _group.modules
                        if _module and _module.deploy_spec
                    ]
                    deploy_response = list(workers.map(_exec_deploy, params))
                    _logger.debug(deploy_response)
                    for dep_resp_object in deploy_response:
                        if dep_resp_object.status in ["ERROR", "error", "Error"]:
                            _logger.error("At least one module failed to deploy...exiting deployment")
                            print_errored_modules("These modules had errors deploying", deploy_response)  # type: ignore
                            exit(0)

        print_manifest_inventory(f"Modules Deployed: {deployment_manifest_wip.name}", deployment_manifest_wip, False)
    else:
        _logger.info(" All modules in %s up to date", deployment_manifest_wip.name)
    # Write the deployment manifest once completed to preserve group order
    du.write_deployed_deployment_manifest(deployment_manifest=deployment_manifest)


def _deploy_deployment_is_dry_run(groups_to_deploy: List[ModulesManifest], deployment_name: str) -> None:
    mods_would_deploy = []
    if groups_to_deploy:
        for _group in groups_to_deploy:
            for _module in _group.modules:
                mods_would_deploy.append([deployment_name, _group.name, _module.name])
    _print_modules(f"Modules scheduled to be deployed (created or updated): {deployment_name}", mods_would_deploy)


def prime_target_accounts(deployment_manifest: DeploymentManifest) -> None:
    # TODO: Include output on Target accounts and regions to be primed
    # TODO: Investigate whether we need to validate the requested mappings against previously deployed mappings
    # TODO: multi-thread this for reach Target account/region for better performance

    for target_account_region in deployment_manifest.target_accounts_regions:
        commands.deploy_seedkit(account_id=target_account_region["account_id"], region=target_account_region["region"])
        commands.deploy_managed_policy_stack(
            deployment_name=deployment_manifest.name,
            deployment_manifest=deployment_manifest,
            account_id=target_account_region["account_id"],
            region=target_account_region["region"],
        )


def tear_down_target_accounts(deployment_manifest: DeploymentManifest, retain_seedkit: bool = False) -> None:
    # TODO: Include output on Target accounts and regions to be primed
    # TODO: Investigate whether we need to validate the requested mappings against previously deployed mappings
    # TODO: multi-thread this for reach Target account/region for better performance

    for target_account_region in deployment_manifest.target_accounts_regions:
        commands.destroy_managed_policy_stack(
            account_id=target_account_region["account_id"],
            region=target_account_region["region"],
        )
        if not retain_seedkit:
            commands.destroy_seedkit(
                account_id=target_account_region["account_id"], region=target_account_region["region"]
            )


def destroy_deployment(
    destroy_manifest: DeploymentManifest,
    remove_deploy_manifest: bool = False,
    dryrun: bool = False,
    show_manifest: bool = False,
) -> None:
    """
    destroy_deployment
        Execute the destroy of a deployment based on a DeploymentManifest

    Parameters
    ----------
    deployment_manifest : DeploymentManifest
        The DeploymentManifest objec of all modules to destroy
    remove_deploy_manifest : bool, optional
        This flag indicates whether the project resource policy should be deleted.
        If there are ANY modules deployed, this should not be set to True.  This is only
        used when the entire deployment is destroyed
    dryrun : bool, optional
        This flag indicates that the DeploymentManifest object should be consumed but DOES NOT
        enact any deployment changes.

        By default False
    show_manifest : bool, optional
        This flag indicates to print out the DeploymentManifest object as s dictionary.

        By default False
    """
    if not destroy_manifest.groups:
        print_bolded("Nothing to destroy", "white")
        return
    print_manifest_inventory(f"Modules removed from manifest: {destroy_manifest.name}", destroy_manifest, False, "red")

    deployment_name = destroy_manifest.name

    print_manifest_inventory(
        f"Modules scheduled to be destroyed for: {destroy_manifest.name}", destroy_manifest, False, "red"
    )
    if not dryrun:
        for _group in reversed(destroy_manifest.groups):
            if len(_group.modules) > 0:
                threads = _group.concurrency if _group.concurrency else len(_group.modules)
                with concurrent.futures.ThreadPoolExecutor(max_workers=threads) as workers:

                    def _exec_destroy(args: Dict[str, Any]) -> Optional[ModuleDeploymentResponse]:
                        return _execute_destroy(
                            args["d"],
                            args["g"],
                            args["m"],
                            destroy_manifest,
                            args["d_secret"],
                        )

                    params = [
                        {
                            "d": deployment_name,
                            "g": _group.name,
                            "m": _module,
                            "d_secret": destroy_manifest.get_parameter_value(
                                "dockerCredentialsSecret",
                                account_alias=_module.target_account,
                                region=_module.target_region,
                            ),
                        }
                        for _module in _group.modules
                        if _module and _module.deploy_spec
                    ]
                    destroy_response = list(workers.map(_exec_destroy, params))
                    _logger.debug(destroy_response)
                    for dep_resp_object in destroy_response:
                        if dep_resp_object and dep_resp_object.status in ["ERROR", "error", "Error"]:
                            _logger.error("At least one module failed to destroy...exiting deployment")
                            print_errored_modules("The following modules had errors destroying ", destroy_response)
                            exit(0)

        print_manifest_inventory(f"Modules Destroyed: {deployment_name}", destroy_manifest, False, "red")
        if remove_deploy_manifest:
            session = SessionManager().get_or_create().toolchain_session
            remove_deployment_manifest(deployment_name, session=session)
            remove_deployed_deployment_manifest(deployment_name, session=session)
    if show_manifest:
        print_manifest_json(destroy_manifest)


def deploy_deployment(
    deployment_manifest: DeploymentManifest,
    module_info_index: du.ModuleInfoIndex,
    dryrun: bool = False,
    show_manifest: bool = False,
) -> None:
    """
    deploy_deployment
        This function takes a populated DeploymentManifest object and deploys all modules in it.
        It evaluates whether the modules have bee previously deployed and if anything has changed
        since the last deployment - ignoring if there are no changes.

    Parameters
    ----------
    deployment_manifest : DeploymentManifest
        The DeploymentManifest objec of all modules to deploy
    module_info_index:ModuleInfoIndex
        An index of all Module Info stored in SSM across all target accounts and regions
    dryrun : bool, optional
        This flag indicates that the DeploymentManifest object should be consumed but DOES NOT
        enact any deployment changes.
        By default False
    show_manifest : bool, optional
        This flag indicates to print out the DeploymentManifest object as s dictionary.

        By default False
    """
    deployment_manifest_wip = deployment_manifest.copy()
    deployment_name = deployment_manifest_wip.name
    _logger.debug("Setting up deployment for %s", deployment_name)

    print_manifest_inventory(
        f"Modules added to manifest: {deployment_manifest_wip.name}", deployment_manifest_wip, True
    )

    groups_to_deploy = []
    unchanged_modules = []
    for group in deployment_manifest_wip.groups:
        # working_group = group.copy()
        group_name = group.name
        # TODO: Investigate whether we need the group manifest, for now commenting
        # du.write_group_manifest(deployment_name=deployment_name, group_manifest=working_group)
        modules_to_deploy = []
        _logger.info(" Verifying all modules in %s for deploy ", group.name)
        for module in group.modules:
            _logger.debug("Working on -- %s", module)
            if not module.path:
                raise ValueError("Unable to parse module manifest, `path` not specified")

            # This checks if the modulestack file exists, else fail fast
            # TODO: Uncomment this if it's needed, but this isn't actually doing anything
            # _ = _get_modulestack_path(module.path)

            deployspec_path = _get_deployspec_path(module.path)
            with open(deployspec_path) as module_spec_file:
                module.deploy_spec = DeploySpec(**yaml.safe_load(module_spec_file))

            # This MD5 is generated from the module manifest content before setting the generated values
            # of `bundle_md5` and `deploy_spec` below
            module_manifest_md5 = hashlib.md5(json.dumps(module.dict(), sort_keys=True).encode("utf-8")).hexdigest()

            module.bundle_md5 = checksumdir.dirhash(os.path.join(config.OPS_ROOT, module.path))
            module_deployspec_md5 = hashlib.md5(open(deployspec_path, "rb").read()).hexdigest()

            _build_module = du.need_to_build(
                deployment_name=deployment_name,
                group_name=group_name,
                module_manifest=module,
                module_deployspec=module.deploy_spec,
                module_deployspec_md5=module_deployspec_md5,
                module_manifest_md5=module_manifest_md5,
                dryrun=dryrun,
                deployment_params_cache=module_info_index.get_module_info(
                    group=group_name,
                    account_id=cast(str, module.get_target_account_id()),
                    region=cast(str, module.target_region),
                    module_name=module.name,
                ),
            )
            if not _build_module:
                unchanged_modules.append([deployment_name, group_name, module.name])
            else:
                modules_to_deploy.append(module)

        if modules_to_deploy:
            groups_to_deploy.append(
                ModulesManifest(
                    name=group.name, path=group.path, concurrency=group.concurrency, modules=modules_to_deploy
                )
            )
    if unchanged_modules:
        _print_modules(
            f"Modules deployed that are up to date (will not be changed): {deployment_name} ", unchanged_modules
        )
    if not dryrun:
        _deploy_deployment_is_not_dry_run(
            deployment_manifest=deployment_manifest,
            deployment_manifest_wip=deployment_manifest_wip,
            deployment_name=deployment_name,
            groups_to_deploy=groups_to_deploy,
        )
    else:
        _deploy_deployment_is_dry_run(groups_to_deploy=groups_to_deploy, deployment_name=deployment_name)

    print_bolded(f"To see all deployed modules, run seedfarmer list modules -d {deployment_name}")

    if show_manifest:
        print_manifest_json(deployment_manifest)


def apply(deployment_manifest_path: str, dryrun: bool = False, show_manifest: bool = False) -> None:
    """
    apply
        This function takes the relative path of a deployment manifest and
        generates a DeploymentManifest object necessary for deploying.  It also
        compares what is currently deployed and generates a DeploymentManifest used for destroying
        modules and groups based on what is missing from the manifest.

    Parameters
    ----------
    deployment_manifest_path : str
        Relative path to the deployment manifest
    dryrun : bool, optional
        This flag indicates that the deployment manifest should be consumed and a
        DeploymentManifest object be created (for both apply and destroy) but DOES NOT
        enact any deployment changes.

        By default False
    show_manifest : bool, optional
        This flag indicates to print out the DeploymentManifest object as s dictionary.

        By default False

    Raises
    ------
    Exception
        If the relative `path' value is missing
    Exception
        If the relative `path' value is a list
    """

    manifest_path = os.path.join(config.OPS_ROOT, deployment_manifest_path)
    with open(manifest_path) as manifest_file:
        deployment_manifest = DeploymentManifest(**yaml.safe_load(manifest_file))
    _logger.debug(deployment_manifest.dict())

    # Initialize the SessionManager for the entire project
    session_manager = SessionManager().get_or_create(project_name=config.PROJECT)
    if not dryrun:
        write_deployment_manifest(
            deployment_manifest.name, deployment_manifest.dict(), session=session_manager.toolchain_session
        )

    for module_group in deployment_manifest.groups:
        if module_group.path and module_group.modules:
            _logger.debug("module_group: %s", module_group)
            raise Exception("Only one of the `path` or `modules` attributes can be defined on a Group")
        if not module_group.path and not module_group.modules:
            _logger.debug("module_group: %s", module_group)
            raise Exception("One of the `path` or `modules` attributes must be defined on a Group")
        if module_group.path:
            with open(os.path.join(config.OPS_ROOT, module_group.path)) as manifest_file:
                module_group.modules = [ModuleManifest(**m) for m in yaml.safe_load_all(manifest_file)]
    deployment_manifest.validate_and_set_module_defaults()

    prime_target_accounts(deployment_manifest=deployment_manifest)

    module_info_index = du.populate_module_info_index(deployment_manifest=deployment_manifest)
    destroy_manifest = du.filter_deploy_destroy(deployment_manifest, module_info_index)

    destroy_deployment(
        destroy_manifest=destroy_manifest,
        remove_deploy_manifest=False,
        dryrun=dryrun,
        show_manifest=show_manifest,
    )
    deploy_deployment(
        deployment_manifest=deployment_manifest,
        module_info_index=module_info_index,
        dryrun=dryrun,
        show_manifest=show_manifest,
    )


def destroy(
    deployment_name: str, dryrun: bool = False, show_manifest: bool = False, retain_seedkit: bool = False
) -> None:
    """
    destroy
        This function takes the name of a deployment and destroy all artifacts related.

    Parameters
    ----------
    deployment_name : str
        The name of the deployment to destroy
    dryrun : bool, optional
        This flag indicates that the deployment WILL NOT
        enact any deployment changes.

        By default False
    show_manifest : bool, optional
        This flag indicates to print out the DeploymentManifest object as s dictionary.

        By default False

    """
    _logger.debug("Preparing to destroy %s", deployment_name)
    destroy_manifest = du.generate_deployed_manifest(deployment_name=deployment_name, skip_deploy_spec=False)
    if destroy_manifest:
        destroy_manifest.validate_and_set_module_defaults()
        destroy_deployment(
            destroy_manifest,
            remove_deploy_manifest=True,
            dryrun=dryrun,
            show_manifest=show_manifest,
        )

    else:
        _logger.info("Deployment %s was not found, ignoring... ", deployment_name)
