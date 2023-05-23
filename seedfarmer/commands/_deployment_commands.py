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
from typing import Any, Dict, List, Optional, Tuple, cast
from urllib.parse import parse_qs

import yaml
from git import Repo  # type: ignore

import seedfarmer.checksum as checksum
import seedfarmer.errors
import seedfarmer.mgmt.deploy_utils as du
import seedfarmer.mgmt.module_info as mi
from seedfarmer import commands, config
from seedfarmer.commands._parameter_commands import load_parameter_values
from seedfarmer.mgmt.module_info import (
    get_deployspec_path,
    get_module_metadata,
    get_modulestack_path,
    remove_deployed_deployment_manifest,
    remove_deployment_manifest,
    write_deployment_manifest,
)
from seedfarmer.models import DeploySpec
from seedfarmer.models.deploy_responses import ModuleDeploymentResponse, StatusType
from seedfarmer.models.manifests import DataFile, DeploymentManifest, ModuleManifest, ModulesManifest, NetworkMapping
from seedfarmer.output_utils import (
    _print_modules,
    print_bolded,
    print_dependency_error_list,
    print_errored_modules_build_info,
    print_manifest_inventory,
    print_manifest_json,
    print_modules_build_info,
)
from seedfarmer.services.session_manager import SessionManager

_logger: logging.Logger = logging.getLogger(__name__)


def _clone_module_repo(git_path: str) -> Tuple[str, str]:
    """Clone a git repo and return directory it is cloned into

    Rather than reinventing the wheel, we implement the Generic Git Repository functionality introduced by
    Terraform. Full documentation on the Git URL definition can be found at:
    https://www.terraform.io/language/modules/sources#generic-git-repository

    Parameters
    ----------
    git_path : str
        The Git URL specified in the Module Manifest. Full example:
        https://example.com/network.git//modules/vpc?ref=v1.2.0&depth=1

    Returns
    -------
    str
        The local directory within the codeseeder.out/ where the repository was cloned
    """
    # gitpython library has started blocking non https and ssh protocols by default
    # codecommit is not _actually_ unsafe
    allow_unsafe_protocols = git_path.startswith("git::codecommit")

    git_path = git_path.replace("git::", "")
    ref: Optional[str] = None
    depth: Optional[int] = None
    module_directory = ""

    if "?" in git_path:
        git_path, query = git_path.split("?")
        query_params = parse_qs(query)
        ref = query_params.get("ref", [None])[0]  # type: ignore
        if "depth" in query_params and query_params["depth"][0].isnumeric():
            depth = int(query_params["depth"][0])

    if ".git//" in git_path:
        git_path, module_directory = git_path.split(".git//")

    repo_directory = git_path.replace("https://", "").replace("git@", "").replace("/", "_").replace(":", "_")

    working_dir = os.path.join(
        config.OPS_ROOT, "seedfarmer.gitmodules", f"{repo_directory}_{ref.replace('/', '_')}" if ref else repo_directory
    )
    os.makedirs(working_dir, exist_ok=True)
    if not os.listdir(working_dir):
        _logger.debug("Cloning %s into %s: ref=%s depth=%s", git_path, working_dir, ref, depth)
        Repo.clone_from(git_path, working_dir, branch=ref, depth=depth, allow_unsafe_protocols=allow_unsafe_protocols)
    else:
        _logger.debug("Pulling existing repo %s at %s: ref=%s", git_path, working_dir, ref)
        Repo(working_dir).remotes["origin"].pull(allow_unsafe_protocols=allow_unsafe_protocols)

    return (working_dir, module_directory)


def _process_module_path(module: ModuleManifest) -> None:
    working_dir, module_directory = _clone_module_repo(module.path)
    module.set_local_path(os.path.join(working_dir, module_directory))


def _process_data_files(data_files: List[DataFile], module_name: str, group_name: str) -> None:
    for data_file in data_files:
        if data_file.file_path.startswith("git::"):
            working_dir, module_directory = _clone_module_repo(data_file.file_path)
            data_file.set_local_file_path(os.path.join(working_dir, module_directory))
            data_file.set_bundle_path(module_directory)
        else:
            data_file.set_local_file_path(os.path.join(config.OPS_ROOT, data_file.file_path))
    missing_files = du.validate_data_files(data_files)
    if len(missing_files) > 0:
        print(f"The following data files cannot be fetched for module {group_name}-{module_name}:")
        for missing_file in missing_files:
            print(f"  {missing_file}")
        print_bolded(message="Exiting Deployment", color="red")
        raise seedfarmer.errors.InvalidPathError("Missing DataFiles - cannot process")


def _execute_deploy(
    group_name: str,
    module_manifest: ModuleManifest,
    deployment_manifest: DeploymentManifest,
    docker_credentials_secret: Optional[str] = None,
    permissions_boundary_arn: Optional[str] = None,
    codebuild_image: Optional[str] = None,
) -> ModuleDeploymentResponse:

    parameters = load_parameter_values(
        deployment_name=cast(str, deployment_manifest.name),
        parameters=module_manifest.parameters,
        deployment_manifest=deployment_manifest,
        target_account=module_manifest.target_account,
        target_region=module_manifest.target_region,
    )

    target_account_id = cast(str, module_manifest.get_target_account_id())
    target_region = cast(str, module_manifest.target_region)
    # Deploys the IAM role per module
    module_stack_name, module_role_name = commands.deploy_module_stack(
        get_modulestack_path(module_manifest.path),
        cast(str, deployment_manifest.name),
        group_name,
        module_manifest.name,
        target_account_id,
        target_region,
        parameters,
        docker_credentials_secret=docker_credentials_secret,
        permissions_boundary_arn=permissions_boundary_arn,
    )

    #   Get the current module's SSM if it was alreadly loaded...
    session = (
        SessionManager().get_or_create().get_deployment_session(account_id=target_account_id, region_name=target_region)
    )
    module_metadata = json.dumps(
        get_module_metadata(cast(str, deployment_manifest.name), group_name, module_manifest.name, session=session)
    )

    if module_manifest.deploy_spec is None:
        raise seedfarmer.errors.InvalidManifestError(
            f"Invalid value for ModuleManifest.deploy_spec in group {group_name} and module : {module_manifest.name}"
        )

    du.prepare_ssm_for_deploy(
        deployment_name=deployment_manifest.name,
        group_name=group_name,
        module_manifest=module_manifest,
        account_id=target_account_id,
        region=target_region,
    ) if deployment_manifest.name else None

    return commands.deploy_module(
        deployment_name=cast(str, deployment_manifest.name),
        group_name=group_name,
        module_manifest=module_manifest,
        account_id=target_account_id,
        region=target_region,
        parameters=parameters,
        module_metadata=module_metadata,
        docker_credentials_secret=docker_credentials_secret,
        permissions_boundary_arn=permissions_boundary_arn,
        module_role_name=module_role_name,
        codebuild_image=codebuild_image,
    )


def _execute_destroy(
    group_name: str,
    module_manifest: ModuleManifest,
    module_path: str,
    deployment_manifest: DeploymentManifest,
    docker_credentials_secret: Optional[str] = None,
    codebuild_image: Optional[str] = None,
) -> Optional[ModuleDeploymentResponse]:
    if module_manifest.deploy_spec is None:
        raise seedfarmer.errors.InvalidManifestError(
            f"Invalid value for ModuleManifest.deploy_spec in group {group_name} and module : {module_manifest.name}"
        )

    target_account_id = cast(str, module_manifest.get_target_account_id())
    target_region = cast(str, module_manifest.target_region)
    session = (
        SessionManager().get_or_create().get_deployment_session(account_id=target_account_id, region_name=target_region)
    )
    module_metadata = json.dumps(
        get_module_metadata(cast(str, deployment_manifest.name), group_name, module_manifest.name, session=session)
    )

    module_stack_name, module_role_name = commands.get_module_stack_info(
        deployment_name=cast(str, deployment_manifest.name),
        group_name=group_name,
        module_name=module_manifest.name,
        account_id=target_account_id,
        region=target_region,
    )

    resp = commands.destroy_module(
        deployment_name=cast(str, deployment_manifest.name),
        group_name=group_name,
        module_path=module_path,
        module_manifest=module_manifest,
        account_id=target_account_id,
        region=target_region,
        parameters=load_parameter_values(
            deployment_name=cast(str, deployment_manifest.name),
            parameters=module_manifest.parameters,
            deployment_manifest=deployment_manifest,
            target_account=module_manifest.target_account,
            target_region=module_manifest.target_region,
        ),
        module_metadata=module_metadata,
        module_role_name=module_role_name,
        codebuild_image=codebuild_image,
    )

    if resp.status == StatusType.SUCCESS.value:
        commands.destroy_module_stack(
            cast(str, deployment_manifest.name),
            group_name,
            module_manifest.name,
            account_id=cast(str, module_manifest.get_target_account_id()),
            region=cast(str, module_manifest.target_region),
            docker_credentials_secret=docker_credentials_secret,
        )

    return resp


def _deploy_validated_deployment(
    deployment_manifest: DeploymentManifest,
    deployment_manifest_wip: DeploymentManifest,
    groups_to_deploy: List[ModulesManifest],
    dryrun: bool,
) -> None:
    if groups_to_deploy:
        if dryrun:
            mods_would_deploy = [
                (_module.target_account, _module.target_region, deployment_manifest.name, _group.name, _module.name)
                for _group in groups_to_deploy
                for _module in _group.modules
            ]
            _print_modules(
                f"Modules scheduled to be deployed (created or updated): {deployment_manifest.name}", mods_would_deploy
            )
            return
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
                        return _execute_deploy(**args)

                    def _render_permissions_boundary_arn(
                        account_id: Optional[str], permissions_boundary_name: Optional[str]
                    ) -> Optional[str]:
                        return (
                            f"arn:aws:iam::{account_id}:policy/{permissions_boundary_name}"
                            if permissions_boundary_name is not None
                            else None
                        )

                    params = [
                        {
                            "group_name": _group.name,
                            "module_manifest": _module,
                            "deployment_manifest": deployment_manifest,
                            "docker_credentials_secret": deployment_manifest_wip.get_parameter_value(
                                "dockerCredentialsSecret",
                                account_alias=_module.target_account,
                                region=_module.target_region,
                            ),
                            "permissions_boundary_arn": _render_permissions_boundary_arn(
                                account_id=_module.get_target_account_id(),
                                permissions_boundary_name=deployment_manifest_wip.get_parameter_value(
                                    "permissionsBoundaryName",
                                    account_alias=_module.target_account,
                                    region=_module.target_region,
                                ),
                            ),
                            "codebuild_image": deployment_manifest_wip.get_region_codebuild_image(
                                account_alias=_module.target_account, region=_module.target_region
                            ),
                        }
                        for _module in _group.modules
                        if _module and _module.deploy_spec
                    ]
                    deploy_response = list(workers.map(_exec_deploy, params))
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
                                "These modules had errors deploying", deploy_response  # type: ignore
                            )
                            raise seedfarmer.errors.ModuleDeploymentError(
                                error_message="At least one module failed to deploy...exiting deployment"
                            )

        print_manifest_inventory(f"Modules Deployed: {deployment_manifest_wip.name}", deployment_manifest_wip, False)
    else:
        _logger.info(" All modules in %s up to date", deployment_manifest_wip.name)
    # Write the deployment manifest once completed to preserve group order
    du.write_deployed_deployment_manifest(deployment_manifest=deployment_manifest)


def prime_target_accounts(deployment_manifest: DeploymentManifest) -> None:
    # TODO: Investigate whether we need to validate the requested mappings against previously deployed mappings

    _logger.info("Priming Accounts")
    with concurrent.futures.ThreadPoolExecutor(max_workers=len(deployment_manifest.target_accounts_regions)) as workers:

        def _prime_accounts(args: Dict[str, Any]) -> None:
            _logger.info("Priming Acccount %s in %s", args["account_id"], args["region"])
            commands.deploy_seedkit(**args)
            commands.deploy_managed_policy_stack(deployment_manifest=deployment_manifest, **args)

        params = []
        for target_account_region in deployment_manifest.target_accounts_regions:

            param_d = {"account_id": target_account_region["account_id"], "region": target_account_region["region"]}
            if target_account_region["network"] is not None:
                network = commands.load_network_values(
                    cast(NetworkMapping, target_account_region["network"]),
                    cast(Dict[str, Any], target_account_region["parameters_regional"]),
                    target_account_region["account_id"],
                    target_account_region["region"],
                )
                param_d["vpc_id"] = network.vpc_id  # type: ignore
                param_d["private_subnet_ids"] = network.private_subnet_ids  # type: ignore
                param_d["security_group_ids"] = network.security_group_ids  # type: ignore

            params.append(param_d)

        _ = list(workers.map(_prime_accounts, params))


def tear_down_target_accounts(deployment_manifest: DeploymentManifest, retain_seedkit: bool = False) -> None:
    # TODO: Investigate whether we need to validate the requested mappings against previously deployed mappings
    _logger.info("Tearing Down Accounts")
    with concurrent.futures.ThreadPoolExecutor(max_workers=len(deployment_manifest.target_accounts_regions)) as workers:

        def _teardown_accounts(args: Dict[str, Any]) -> None:
            _logger.info("Tearing Down Acccount %s in %s", args["account_id"], args["region"])
            commands.destroy_managed_policy_stack(**args)
            if not retain_seedkit:
                commands.destroy_seedkit(**args)

        params = [
            {"account_id": target_account_region["account_id"], "region": target_account_region["region"]}
            for target_account_region in deployment_manifest.target_accounts_regions
        ]
        _ = list(workers.map(_teardown_accounts, params))


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

    deployment_name = cast(str, destroy_manifest.name)

    print_manifest_inventory(
        f"Modules scheduled to be destroyed for: {destroy_manifest.name}", destroy_manifest, False, "red"
    )
    if not dryrun:
        for _group in reversed(destroy_manifest.groups):
            if len(_group.modules) > 0:
                threads = _group.concurrency if _group.concurrency else len(_group.modules)
                with concurrent.futures.ThreadPoolExecutor(max_workers=threads) as workers:

                    def _exec_destroy(args: Dict[str, Any]) -> Optional[ModuleDeploymentResponse]:
                        return _execute_destroy(**args)

                    for _module in _group.modules:
                        _process_module_path(module=_module) if _module.path.startswith("git::") else None

                        _process_data_files(
                            data_files=_module.data_files, module_name=_module.name, group_name=_group.name
                        ) if _module.data_files is not None else None

                        if _module and _module.deploy_spec:
                            params = [
                                {
                                    "group_name": _group.name,
                                    "module_manifest": _module,
                                    "module_path": str(_module.get_local_path()),
                                    "deployment_manifest": destroy_manifest,
                                    "docker_credentials_secret": destroy_manifest.get_parameter_value(
                                        "dockerCredentialsSecret",
                                        account_alias=_module.target_account,
                                        region=_module.target_region,
                                    ),
                                    "codebuild_image": destroy_manifest.get_region_codebuild_image(
                                        account_alias=_module.target_account, region=_module.target_region
                                    ),
                                }
                                for _module in _group.modules
                            ]
                    destroy_response = list(workers.map(_exec_destroy, params))
                    _logger.debug(destroy_response)
                    print_modules_build_info("Build Info Debug Data", destroy_response) if _logger.isEnabledFor(
                        logging.DEBUG
                    ) else None
                    for dep_resp_object in destroy_response:
                        if dep_resp_object and dep_resp_object.status in ["ERROR", "error", "Error"]:
                            _logger.error("At least one module failed to destroy...exiting deployment")
                            print_errored_modules_build_info(
                                "The following modules had errors destroying ", destroy_response
                            )
                            raise seedfarmer.errors.ModuleDeploymentError(
                                error_message="At least one module failed to destroy...exiting deployment"
                            )

        print_manifest_inventory(f"Modules Destroyed: {deployment_name}", destroy_manifest, False, "red")
        if remove_deploy_manifest:
            session = SessionManager().get_or_create().toolchain_session
            remove_deployment_manifest(deployment_name, session=session)
            remove_deployed_deployment_manifest(deployment_name, session=session)
            tear_down_target_accounts(deployment_manifest=destroy_manifest, retain_seedkit=True)
    if show_manifest:
        print_manifest_json(destroy_manifest)


def deploy_deployment(
    deployment_manifest: DeploymentManifest,
    module_info_index: du.ModuleInfoIndex,
    module_upstream_dep: Dict[str, List[str]],
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
    module_upstream_dep: Dict[str, List[str]]
        A dict containing all the upstream dependencies of a module.  Each key in the dict is a module name
        with the format <group_name>-<module_name> and the value is a list of modules, each with the format
        of <group_name>-<module_name>
    dryrun : bool, optional
        This flag indicates that the DeploymentManifest object should be consumed but DOES NOT
        enact any deployment changes.
        By default False
    show_manifest : bool, optional
        This flag indicates to print out the DeploymentManifest object as s dictionary.

        By default False
    """
    deployment_manifest_wip = deployment_manifest.copy()
    deployment_name = cast(str, deployment_manifest_wip.name)
    _logger.debug("Setting up deployment for %s", deployment_name)

    print_manifest_inventory(
        f"Modules added to manifest: {deployment_manifest_wip.name}", deployment_manifest_wip, True
    )

    if deployment_manifest.force_dependency_redeploy:
        _logger.warn("You have configured your deployment to FORCE all dependent modules to redeploy")
        _logger.debug(f"Upstream Module Dependencies : {json.dumps(module_upstream_dep, indent=4)}")

    groups_to_deploy = []
    unchanged_modules = []
    _group_mod_to_deploy: List[str] = []
    for group in deployment_manifest_wip.groups:
        modules_to_deploy = []
        _logger.info(" Verifying all modules in %s for deploy ", group.name)
        du.validate_group_parameters(group=group)
        for module in group.modules:
            _logger.debug("Working on -- %s", module)
            if not module.path:
                raise seedfarmer.errors.InvalidManifestError("Unable to parse module manifest, `path` not specified")

            _process_module_path(module=module) if module.path.startswith("git::") else None

            _process_data_files(
                data_files=module.data_files, module_name=module.name, group_name=group.name
            ) if module.data_files is not None else None

            deployspec_path = get_deployspec_path(str(module.get_local_path()))
            with open(deployspec_path) as module_spec_file:
                module.deploy_spec = DeploySpec(**yaml.safe_load(module_spec_file))

            md5_excluded_module_files = [
                "README.md",
                "modulestack.template",
                "setup.cfg",
                "requirements-dev.txt",
                "requirements-dev.in",
                ".gitignore",
            ]

            module.bundle_md5 = checksum.get_module_md5(
                project_path=config.OPS_ROOT,
                module_path=str(module.get_local_path()),
                data_files=module.data_files,
                excluded_files=md5_excluded_module_files,
            )

            for param in module.parameters:
                if param.value_from and param.value_from.parameter_store:
                    if ":" in param.value_from.parameter_store:
                        raise seedfarmer.errors.InvalidConfigurationError(
                            f"CodeBuild does not support Versioned SSM Parameters -- see {group.name}-{module.name}"
                        )
                    param.version = mi.get_ssm_parameter_version(
                        ssm_parameter_name=param.value_from.parameter_store,
                        session=SessionManager()
                        .get_or_create()
                        .get_deployment_session(
                            account_id=cast(str, module.get_target_account_id()),
                            region_name=cast(str, module.target_region),
                        ),
                    )

                elif param.value_from and param.value_from.secrets_manager:
                    param_name = param.value_from.secrets_manager
                    version_ref = None
                    if ":" in param_name:
                        parsed = param_name.split(":")
                        param_name = parsed[0]
                        version_ref = parsed[2] if len(parsed) == 3 else None

                    param.version = mi.get_secrets_version(
                        secret_name=param_name,
                        version_ref=version_ref,
                        session=SessionManager()
                        .get_or_create()
                        .get_deployment_session(
                            account_id=cast(str, module.get_target_account_id()),
                            region_name=cast(str, module.target_region),
                        ),
                    )

            module.manifest_md5 = hashlib.md5(json.dumps(module.dict(), sort_keys=True).encode("utf-8")).hexdigest()
            module.deployspec_md5 = hashlib.md5(open(deployspec_path, "rb").read()).hexdigest()

            _build_module = du.need_to_build(
                deployment_name=deployment_name,
                group_name=group.name,
                module_manifest=module,
                active_modules=_group_mod_to_deploy,
                module_upstream_dep=module_upstream_dep,
                force_redeploy_flag=cast(bool, deployment_manifest.force_dependency_redeploy),
                deployment_params_cache=module_info_index.get_module_info(
                    group=group.name,
                    account_id=cast(str, module.get_target_account_id()),
                    region=cast(str, module.target_region),
                    module_name=module.name,
                ),
            )
            if not _build_module:
                unchanged_modules.append(
                    [module.target_account, module.target_region, deployment_name, group.name, module.name]
                )
            else:
                modules_to_deploy.append(module)
                _group_mod_to_deploy.append(f"{group.name}-{module.name}")

        if modules_to_deploy:
            groups_to_deploy.append(
                ModulesManifest(
                    name=group.name, path=group.path, concurrency=group.concurrency, modules=modules_to_deploy
                )
            )
    _print_modules(
        f"Modules deployed that are up to date (will not be changed): {deployment_name} ", unchanged_modules
    ) if unchanged_modules else None
    _deploy_validated_deployment(
        deployment_manifest=deployment_manifest,
        deployment_manifest_wip=deployment_manifest_wip,
        groups_to_deploy=groups_to_deploy,
        dryrun=dryrun,
    )
    print_bolded(f"To see all deployed modules, run seedfarmer list modules -d {deployment_name}")
    print_manifest_json(deployment_manifest) if show_manifest else None


def apply(
    deployment_manifest_path: str,
    profile: Optional[str] = None,
    region_name: Optional[str] = None,
    dryrun: bool = False,
    show_manifest: bool = False,
    enable_session_timeout: bool = False,
    session_timeout_interval: int = 900,
) -> None:
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
    profile : str
        If using an AWS Profile for deployment use it here
    region_name : str
        The name of the AWS region the deployment is based in for the toolchain
    dryrun : bool, optional
        This flag indicates that the deployment manifest should be consumed and a
        DeploymentManifest object be created (for both apply and destroy) but DOES NOT
        enact any deployment changes.

        By default False
    show_manifest : bool, optional
        This flag indicates to print out the DeploymentManifest object as s dictionary.

        By default False
    enable_session_timeout: bool
        If enabled, boto3 Sessions will be reset on the timeout interval
    session_timeout_interval: int
        The interval, in seconds, to reset boto3 Sessions

    Raises
    ------
    InvalidConfigurationError
        seedfarmer.errors.seedfarmer_errors.InvalidConfigurationError
    InvalidPathError
        seedfarmer.errors.seedfarmer_errors.InvalidPathError
    ModuleDeploymentError
        seedfarmer.errors.seedfarmer_errors.ModuleDeploymentError
    """

    manifest_path = os.path.join(config.OPS_ROOT, deployment_manifest_path)
    with open(manifest_path) as manifest_file:
        deployment_manifest = DeploymentManifest(**yaml.safe_load(manifest_file))
    _logger.debug(deployment_manifest.dict())

    # Initialize the SessionManager for the entire project
    session_manager = SessionManager().get_or_create(
        project_name=config.PROJECT,
        profile=profile,
        toolchain_region=deployment_manifest.toolchain_region,
        region_name=region_name,
        enable_reaper=enable_session_timeout,
        reaper_interval=session_timeout_interval,
    )
    if not dryrun:
        write_deployment_manifest(
            cast(str, deployment_manifest.name), deployment_manifest.dict(), session=session_manager.toolchain_session
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
        if module_group.path:
            try:
                with open(os.path.join(config.OPS_ROOT, module_group.path)) as manifest_file:
                    module_group.modules = [ModuleManifest(**m) for m in yaml.safe_load_all(manifest_file)]
            except Exception as e:
                _logger.error(e)
                _logger.error(f"Cannot parse a file at {os.path.join(config.OPS_ROOT, module_group.path)}")
                _logger.error("Verify that elements are filled out and yaml compliant")
                raise seedfarmer.errors.InvalidPathError("Cannot parse manifest file path")
    deployment_manifest.validate_and_set_module_defaults()

    prime_target_accounts(deployment_manifest=deployment_manifest)

    module_info_index = du.populate_module_info_index(deployment_manifest=deployment_manifest)
    destroy_manifest = du.filter_deploy_destroy(deployment_manifest, module_info_index)

    module_depends_on_dict, module_dependencies_dict = du.generate_dependency_maps(manifest=deployment_manifest)
    _logger.debug("module_depends_on_dict: %s", json.dumps(module_depends_on_dict))
    _logger.debug("module_dependencies_dict: %s", json.dumps(module_dependencies_dict))
    violations = du.validate_module_dependencies(module_dependencies_dict, destroy_manifest)
    if violations:
        print_dependency_error_list(
            header_message="The following modules requested for destroy have dependencies that prevent destruction:",
            errored_list=violations,
        )
        raise seedfarmer.errors.InvalidConfigurationError("Modules cannot be destroyed due to dependencies")

    destroy_deployment(
        destroy_manifest=destroy_manifest,
        remove_deploy_manifest=False,
        dryrun=dryrun,
        show_manifest=show_manifest,
    )
    deploy_deployment(
        deployment_manifest=deployment_manifest,
        module_info_index=module_info_index,
        module_upstream_dep=module_depends_on_dict,
        dryrun=dryrun,
        show_manifest=show_manifest,
    )


def destroy(
    deployment_name: str,
    profile: Optional[str] = None,
    region_name: Optional[str] = None,
    dryrun: bool = False,
    show_manifest: bool = False,
    retain_seedkit: bool = False,
    enable_session_timeout: bool = False,
    session_timeout_interval: int = 900,
) -> None:
    """
    destroy
        This function takes the name of a deployment and destroy all artifacts related.

    Parameters
    ----------
    deployment_name : str
        The name of the deployment to destroy
    profile : str
        If using an AWS Profile for deployment use it here
    region_name : str
        The name of the AWS region the deployment is based in for the toolchain
    dryrun : bool, optional
        This flag indicates that the deployment WILL NOT
        enact any deployment changes.

        By default False
    show_manifest : bool, optional
        This flag indicates to print out the DeploymentManifest object as s dictionary.

        By default False
    enable_session_timeout: bool
        If enabled, boto3 Sessions will be reset on the timeout interval
    session_timeout_interval: int
        The interval, in seconds, to reset boto3 Sessions

    Raises
    ------
    InvalidConfigurationError
        seedfarmer.errors.seedfarmer_errors.InvalidConfigurationError
    InvalidPathError
        seedfarmer.errors.seedfarmer_errors.InvalidPathError
    ModuleDeploymentError
        seedfarmer.errors.seedfarmer_errors.ModuleDeploymentError
    """
    project = config.PROJECT
    _logger.debug("Preparing to destroy %s", deployment_name)
    SessionManager().get_or_create(
        project_name=project,
        profile=profile,
        region_name=region_name,
        enable_reaper=enable_session_timeout,
        reaper_interval=session_timeout_interval,
    )
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
