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
from threading import Lock
from typing import Any, Dict, List, Optional, Set, Tuple, cast

import yaml
from boto3 import Session

import seedfarmer.errors
import seedfarmer.mgmt.module_info as mi
from seedfarmer.models import DeploySpec
from seedfarmer.models.manifests import DataFile, DeploymentManifest, ModuleManifest, ModulesManifest
from seedfarmer.output_utils import print_bolded
from seedfarmer.services.session_manager import SessionManager

_logger: logging.Logger = logging.getLogger(__name__)


class ModuleInfoIndex(object):
    def __init__(self) -> None:
        super().__init__()
        self._index: Dict[Tuple[str, str, str, str], Dict[str, Any]] = dict()
        self._groups: Set[str] = set()
        self._groups_idx: Dict[str, Set[Tuple[str, str, str, str]]] = dict()
        self._module_names_idx: Dict[Tuple[str, str], Tuple[str, str, str, str]] = dict()
        self._lock = Lock()

    @property
    def groups(self) -> Set[str]:
        return self._groups

    def get_module_info(
        self, *, group: str, account_id: str, region: str, module_name: str
    ) -> Optional[Dict[str, Any]]:
        return self._index.get((group, account_id, region, module_name))

    def index_module_info(
        self, *, group: str, account_id: str, region: str, module_name: str, module_info: Dict[str, Any]
    ) -> None:
        with self._lock:
            module_info_key = (group, account_id, region, module_name)
            current_module_info = self._index.get(module_info_key, {})
            self._index[module_info_key] = {**current_module_info, **module_info}
            self._groups.add(group)
            current_group_keys = self._groups_idx.get(group, set())
            current_group_keys.add(module_info_key)
            self._groups_idx[group] = current_group_keys
            self._module_names_idx[(group, module_name)] = module_info_key

    def get_keys_for_group(self, group: str) -> List[Dict[str, str]]:
        return [
            {"group": m[0], "account_id": m[1], "region": m[2], "module_name": m[3]}
            for m in self._groups_idx.get(group, [])
        ]

    def get_key_for_module_name(self, group: str, module_name: str) -> Dict[str, str]:
        m = self._module_names_idx.get((group, module_name), None)
        if m is not None:
            return {"group": m[0], "account_id": m[1], "region": m[2], "module_name": m[3]}
        else:
            return {"group": "", "account_id": "", "region": "", "module_name": ""}


def populate_module_info_index(deployment_manifest: DeploymentManifest) -> ModuleInfoIndex:
    """
    populate_module_info_index
        Fetch all info for the deployment currently stored, across all Target accounts and regions

    Parameters
    ----------
    deployment_manifest: DeploymentManifest
        The DeploymentManifest, including TargetAccount and Region mappings

    Returns
    -------
    ModuleInfoIndex
        An index of Module info for all Target accounts and regions
    """
    module_info_index = ModuleInfoIndex()

    with concurrent.futures.ThreadPoolExecutor(max_workers=len(deployment_manifest.target_accounts_regions)) as workers:

        def _get_module_info(args: Dict[str, Any]) -> None:
            session = (
                SessionManager()
                .get_or_create()
                .get_deployment_session(account_id=args["account_id"], region_name=args["region"])
            )
            module_info = mi.get_parameter_data_cache(deployment=cast(str, deployment_manifest.name), session=session)
            for key, value in module_info.items():
                key_parts = key.split("/")[1:]
                if len(key_parts) < 4:
                    continue
                group = key_parts[2]
                module_name = key_parts[3]
                module_info_index.index_module_info(
                    group=group, module_name=module_name, module_info={key: value}, **args
                )

        params = [
            {"account_id": target_account_region["account_id"], "region": target_account_region["region"]}
            for target_account_region in deployment_manifest.target_accounts_regions
        ]
        _ = list(workers.map(_get_module_info, params))

    return module_info_index


def validate_data_files(data_files: Optional[List[DataFile]]) -> List[str]:
    """
    validate_data_files
        This will determine if all data files requested are available, and return the files that are not available.

    Parameters
    ----------
    data_files : Optional[List[DataFile]]
        The list of DataFile objects to evaluate

    Returns
    -------
    List[str]
        The list of data file paths not found
    """
    missing_files = []
    if data_files is not None:
        missing_files = [
            data_file.file_path for data_file in data_files if not os.path.isfile(str(data_file.get_local_file_path()))
        ]
    return missing_files


def validate_group_parameters(group: ModulesManifest) -> None:
    """
    validate_group_parameters
        This will verify that there are no intra-group dependencies in the parameter references

    Parameters
    ----------
    group: ModulesManifest
        The ModulesManifest representing a group

    Returns
    -------
    None
    """
    _logger.debug(f"Inspecting group {group.name} for intra-dependencies")
    group_wip = set({})
    for module in group.modules:
        if module.parameters:
            for parameter in module.parameters:
                (
                    group_wip.add(parameter.value_from.module_metadata.group)
                    if parameter.value_from and parameter.value_from.module_metadata
                    else None
                )
    if group.name in group_wip:
        message = f"""
        ERROR!!!  An intra-group dependency for was found in a module reference for group {group.name}
          No module can refer to its own group for parameter lookups!!
        """
        print_bolded(message=message, color="red")
        raise seedfarmer.errors.InvalidConfigurationError(message)


def validate_module_dependencies(
    module_dependencies: Dict[str, List[str]], destroy_manifest: DeploymentManifest
) -> List[Dict[str, List[str]]]:
    """
    This will compare a dictionary of the module dependencies and a destroy manifest object to make sure there
    are no modules scheduled to be destroyed that are referenced by modules that will be / are deployed

    Parameters
    ----------
    module_dependencies : Dict[str,List]
        A dict that is that has the module as the key (in form of `<group>-<module_name>`) and the value is a list
        of modules (in form of `[<group>-<module_name>]`) that are dependent on that module
    destroy_manifest : DeploymentManifest
        The manifest object representing all modules that should be destroyed

    Returns
    -------
    List[Dict[str,List[str]]]
        A list of dictionaries of the modules that have dependencies that are blocking deletion:
        ```
        [
            {<group>-<module_name>:[<group>-<module_name>,<group>-<module_name>]}
        ]
        ```

    """

    def _get_module_list(manifest: DeploymentManifest) -> List[str]:

        module_list = []
        for group in manifest.groups:
            for module in group.modules:
                module_list.append(f"{group.name}-{module.name}")
        return module_list

    volations = []
    module_destroy_list = _get_module_list(destroy_manifest)
    for destroy_mod_candidate in module_destroy_list:
        mod_dep = (
            module_dependencies.get(destroy_mod_candidate) if module_dependencies.get(destroy_mod_candidate) else None
        )
        if mod_dep:
            v = [module for module in mod_dep if module not in module_destroy_list]
            violation = {destroy_mod_candidate: v}
            volations.append(violation)

    return volations


def generate_dependency_maps(manifest: DeploymentManifest) -> Tuple[Dict[str, List[str]], Dict[str, List[str]]]:
    """
    Takes a deployment manifest object and returns two (2) dictionaries that contain:
        1. all the other modules that a given module depends on (module_depends_on)
        2. all the modules that are dependent on a given module (module_dependencies)

    Parameters
    ----------
    manifest : DeploymentManifest
        A fully populated deployment manifest object

    Returns
    -------
    Tuple[Dict[str, List], Dict[str, List]]
        2 Dictionaries:
            1. `module_depends_on` - all the other modules that a given module depends on
            2. `module_dependencies` - all the modules that are dependent on the given module
    """

    def add_to_list(target_dict: Dict[str, Any], key: str, val: str) -> None:
        active_list = target_dict.get(key) if target_dict.get(key) else []
        active_list.append(val) if val not in active_list else None  # type: ignore
        target_dict[key] = active_list

    module_depends_on: Dict[str, Any] = {}
    module_dependencies: Dict[str, Any] = {}
    for group in manifest.groups:
        for module in group.modules:
            group_module_name = f"{group.name}-{module.name}"
            for parameter in module.parameters:
                if parameter.value_from and parameter.value_from.module_metadata:
                    parameter_module_reference = (
                        f"{parameter.value_from.module_metadata.group}-{parameter.value_from.module_metadata.name}"
                    )
                    add_to_list(module_depends_on, group_module_name, parameter_module_reference)
                    add_to_list(module_dependencies, parameter_module_reference, group_module_name)
    return module_depends_on, module_dependencies


def prepare_ssm_for_deploy(
    deployment_name: str, group_name: str, module_manifest: ModuleManifest, account_id: str, region: str
) -> None:
    """
    prepare_ssm_for_deploy
        This method takes the populated ModuleManifest and updates SSM to prepare for deployment

    Parameters
    ----------
    deployment_name : str
        The deployment name
    group_name : str
        The group name
    module_manifest : ModuleManifest
        The Module Manifect opject
    account_id : str
        The Account Id of where this module is to be deployed
    region : str
        The Region of where this module is to be deployed
    """

    # Remove the deployspec before writing...remove bloat as we write deployspec separately
    session = SessionManager().get_or_create().get_deployment_session(account_id=account_id, region_name=region)
    module_manifest_wip = module_manifest.copy()
    module_manifest_wip.deploy_spec = None
    mi.write_module_manifest(
        deployment=deployment_name,
        group=group_name,
        module=module_manifest.name,
        data=module_manifest_wip.dict(),
        session=session,
    )
    mi.write_deployspec(
        deployment=deployment_name,
        group=group_name,
        module=module_manifest.name,
        data=module_manifest.deploy_spec.dict(),
        session=session,
    ) if module_manifest.deploy_spec else None
    mi.write_module_md5(
        deployment=deployment_name,
        group=group_name,
        module=module_manifest.name,
        hash=module_manifest.deployspec_md5,
        type=mi.ModuleConst.DEPLOYSPEC,
        session=session,
    ) if module_manifest.deployspec_md5 else None
    mi.write_module_md5(
        deployment=deployment_name,
        group=group_name,
        module=module_manifest.name,
        hash=module_manifest.manifest_md5,
        type=mi.ModuleConst.MANIFEST,
        session=session,
    ) if module_manifest.manifest_md5 else None
    mi.remove_module_md5(
        deployment=deployment_name,
        group=group_name,
        module=module_manifest.name,
        type=mi.ModuleConst.BUNDLE,
        session=session,
    )


def write_deployed_deployment_manifest(deployment_manifest: DeploymentManifest) -> None:
    """
    write_deployed_deployment_manifest
        Write the deployment manifest to the store

    Parameters
    ----------
    deployment_manifest : DeploymentManifest
        The deployment manifest ojject to store
    """
    deployment_name = cast(str, deployment_manifest.name)
    for group in deployment_manifest.groups:
        delattr(group, "modules")
    session = SessionManager().get_or_create().toolchain_session
    mi.write_deployed_deployment_manifest(deployment=deployment_name, data=deployment_manifest.dict(), session=session)


def generate_deployed_manifest(
    deployment_name: str,
    skip_deploy_spec: bool = False,
    ignore_deployed: Optional[bool] = False,
) -> Optional[DeploymentManifest]:
    """
    Generate a DeploymentManifest object from based off deployed modules in a deployment

    Parameters
    ----------
    deployment_name : str
        The name of the deployment the manifest is generated for
    skip_deploy_spec : bool, optional
        Skip populating each module deployspec - handy for getting the list of deployed modules quickly
    ignore_deployed : Optional[bool]
        When fetching the deployment manifest stored, ignore the successfully deployed modules,
        forcing a fetch of the last requested deployment (to include modules that failed to deploy)

    Returns
    -------
    Optional[DeploymentManifest]
        The hydrated DeploymentManifest object of deployed modules
    """
    session_manager = SessionManager().get_or_create()
    dep_manifest_dict = mi.get_deployed_deployment_manifest(deployment_name, session=session_manager.toolchain_session)
    if dep_manifest_dict is None or ignore_deployed:
        # No successful deployments, just use what was last requested
        dep_manifest_dict = mi.get_deployment_manifest(deployment_name, session=session_manager.toolchain_session)
    deployed_manifest = None
    if dep_manifest_dict:
        deployed_manifest = DeploymentManifest(**dep_manifest_dict)
        module_info_index = populate_module_info_index(deployment_manifest=deployed_manifest)
        for module_group in dep_manifest_dict["groups"] if dep_manifest_dict["groups"] else []:
            group_name = module_group["name"]
            module_group["modules"] = _populate_group_modules_from_index(
                deployment_name=deployment_name,
                group_name=group_name,
                module_info_index=module_info_index,
                skip_deploy_spec=skip_deploy_spec,
            )
        deployed_manifest.groups = [ModulesManifest(**group) for group in dep_manifest_dict["groups"]]
    return deployed_manifest


def get_deployed_group_ordering(deployment_name: str) -> Dict[str, int]:
    """
    This generates a dict of the groups deployed and the index representing the proper deployment ordering

    Parameters
    ----------
    deployment_name : str
        The name of the deployment

    Returns
    -------
    Dict[str, int]
        A dict with the name of the group as the key and an int as the value of the index
    """
    session_manager = SessionManager().get_or_create()
    dep_manifest_dict = mi.get_deployed_deployment_manifest(deployment_name, session=session_manager.toolchain_session)
    if dep_manifest_dict is None:
        # No successful deployments, just use what was last requested
        dep_manifest_dict = mi.get_deployment_manifest(deployment_name, session=session_manager.toolchain_session)
    ordering = {}
    for idx, val in enumerate(dep_manifest_dict["groups"]):  # type: ignore
        ordering[val["name"]] = idx
    return ordering


def force_redeploy(
    group_name: str, module_name: str, active_modules: List[str], module_upstream_dep: Dict[str, List[str]]
) -> bool:
    """
    force_redeploy
    This indicates whether a module needs to redeployed based on a list of other modules that have been scheduled
    to be redeployed.

    Parameters
    ----------
    group_name : str
        The name of the group the module belongs to
    module_name : str
        The name of the modules
    active_modules : List[str]
        A list of modules already scheduled to be deployed.  The have the naming format of <group_name>-<module_name>
    module_upstream_dep : Dict[str, List[str]]
        A dict containing all the upstream dependencies of a module.  Each key in the dict is a module name
        with the format <group_name>-<module_name> and the value is a list of modules, each with the format
        of <group_name>-<module_name>
    Returns
    -------
    bool
        Indicator whether or not the module needs to be force-redeployed.
    """
    if module_upstream_dep.get(f"{group_name}-{module_name}"):
        return (
            True
            if (len((set(active_modules)).intersection(set(module_upstream_dep[f"{group_name}-{module_name}"]))) > 0)
            else False
        )
    else:
        return False


def need_to_build(
    deployment_name: str,
    group_name: str,
    module_manifest: ModuleManifest,
    active_modules: List[str] = [],
    module_upstream_dep: Dict[str, List[str]] = {},
    force_redeploy_flag: bool = False,
    deployment_params_cache: Optional[Dict[str, Any]] = None,
) -> bool:
    """
    This will indicated whether a module needs to be rebuilt based on
    the manifests, deployspec, and code of the groups and modules.  It will also
    record this info if the module does need to be rebuilt.

    Parameters
    ----------
    deployment_name : str
        The name of the deployment
    group_name : str
        A name of the corresponding group
    module_manifest : ModuleManifest
        The populated ModuleManifest Object
    active_modules : List[str]
        A list of modules already scheduled to be deployed.  The have the naming format of <group_name>-<module_name>
    module_upstream_dep : Dict[str, List[str]]
        A dict containing all the upstream dependencies of a module.  Each key in the dict is a module name
        with the format <group_name>-<module_name> and the value is a list of modules, each with the format
        of <group_name>-<module_name>
    force_redeploy_flag: bool
        A bool indicating whether the deployment is set to force-redeploy
        Defaults to False
    deployment_params_cache: Dict[str, Any]
        A cache of deployment commands

    Returns
    -------
    bool
        Indicator whether the module needs to be build or not.
        True - yes, built it
        False - no, do not build it
    """
    if force_redeploy_flag and (
        force_redeploy(
            group_name=group_name,
            module_name=module_manifest.name,
            active_modules=active_modules,
            module_upstream_dep=module_upstream_dep,
        )
    ):
        return True

    session = (
        SessionManager()
        .get_or_create()
        .get_deployment_session(
            account_id=cast(str, module_manifest.get_target_account_id()),
            region_name=cast(str, module_manifest.target_region),
        )
    )
    if (
        mi.does_md5_match(
            deployment_name,
            group_name,
            module_manifest.name,
            module_manifest.bundle_md5,  # type: ignore
            mi.ModuleConst.BUNDLE,
            deployment_params_cache,
            session=session,
        )
        and mi.does_md5_match(
            deployment_name,
            group_name,
            module_manifest.name,
            module_manifest.deployspec_md5,  # type: ignore
            mi.ModuleConst.DEPLOYSPEC,
            deployment_params_cache,
            session=session,
        )
        and mi.does_md5_match(
            deployment_name,
            group_name,
            module_manifest.name,
            module_manifest.manifest_md5,  # type: ignore
            mi.ModuleConst.MANIFEST,
            deployment_params_cache,
            session=session,
        )
    ):
        return False
    else:
        return True


def write_group_manifest(deployment_name: str, group_manifest: ModulesManifest) -> None:
    """
    write_group_manifest
        Persist the group from a MOdulesManifest object

    Parameters
    ----------
    deployment_name : str
        The name of the deployment
    group_manifest : ModulesManifest
        The ModulesManifest object of the groups to persist
    """
    g = group_manifest.name if group_manifest.name else ""
    mi.write_group_manifest(deployment=deployment_name, group=g, data=group_manifest.dict())


def filter_deploy_destroy(apply_manifest: DeploymentManifest, module_info_index: ModuleInfoIndex) -> DeploymentManifest:
    """
    This method takes a populated DeploymentManifest object based off the requested deployment.
    It compares this requested deployment with what is currently deployed.  If there are groups or
    modules that are not in the request, a DeploymentManifest object is returned populated with all
    the information of modules to be destroyed.

    Parameters
    ----------
    apply_manifest : DeploymentManifest
        The DeploymentManifest object based off a deployment manifest of a requested deployment.
    module_info_index: ModuleInfoIndex
        The index of existing module info for all Target accounts and regions

    Returns
    -------
    DeploymentManifest
        A populated DeploymentManifest object with the modules needed to be destroyed
    """
    deployment_name = cast(str, apply_manifest.name)

    destroy_manifest = apply_manifest.copy()
    delattr(destroy_manifest, "groups")
    destroy_group_list = _populate_groups_to_remove(deployment_name, apply_manifest.groups, module_info_index)
    destroy_manifest.groups = destroy_group_list
    for group in apply_manifest.groups:
        destroy_module_list = _populate_modules_to_remove(deployment_name, group.name, group.modules, module_info_index)
        if destroy_module_list:
            to_destroy = ModulesManifest(name=group.name, path=group.path, modules=destroy_module_list)
            destroy_manifest.groups.append(to_destroy)

    # Make sure the groups are sorted in proper order of the deployment
    try:
        ordering = get_deployed_group_ordering(deployment_name)

        def groupOrderingFilter(module: ModulesManifest) -> int:
            return ordering.get(module.name, 99)

        destroy_manifest.groups.sort(key=groupOrderingFilter)
    except Exception as e:
        _logger.info(f"Threw and error trying to sort the groups for destroy, ignoring and moving on {e}")

    destroy_manifest.validate_and_set_module_defaults()
    return destroy_manifest


def _populate_group_modules_from_index(
    deployment_name: str, group_name: str, module_info_index: ModuleInfoIndex, skip_deploy_spec: bool
) -> List[Dict[str, Any]]:
    modules = []
    for group_key in module_info_index.get_keys_for_group(group_name):
        deployment_params_cache = module_info_index.get_module_info(**group_key)
        module_manifest = mi.get_module_manifest(
            deployment_name, group_name, group_key["module_name"], deployment_params_cache
        )
        if module_manifest is not None:
            if not skip_deploy_spec:
                module_manifest["deploy_spec"] = mi.get_deployspec(
                    deployment_name, group_name, group_key["module_name"], deployment_params_cache
                )
            modules.append(module_manifest)
    return modules


def _populate_groups_to_remove(
    deployment_name: str, apply_groups: List[ModulesManifest], module_info_index: ModuleInfoIndex
) -> List[ModulesManifest]:
    set_requested_groups = set([g.name for g in apply_groups])
    set_deployed_groups = module_info_index.groups
    destroy_groups = list(sorted(set_deployed_groups - set_requested_groups))
    _logger.debug("Groups already deployed that will be DESTROYED : %s", destroy_groups)
    destroy_group_list = []
    for destroy_group in destroy_groups:
        group_manifest = {
            "name": destroy_group,
            "modules": _populate_group_modules_from_index(
                deployment_name=deployment_name,
                group_name=destroy_group,
                module_info_index=module_info_index,
                skip_deploy_spec=False,
            ),
        }
        destroy_group_list.append(ModulesManifest(**group_manifest))
    return destroy_group_list


def _populate_modules_to_remove(
    deployment_name: str, group: str, apply_modules: List[ModuleManifest], module_info_index: ModuleInfoIndex
) -> List[ModuleManifest]:
    set_requests_modules = set([m.name for m in apply_modules])
    set_deployed_modules = set([m["module_name"] for m in module_info_index.get_keys_for_group(group)])
    destroy_modules = list(sorted(set_deployed_modules - set_requests_modules))
    _logger.debug("Modules of Group %s already deployed that will be DESTROYED: %s", group, destroy_modules)

    destroy_module_list = []
    for destroy_module in destroy_modules:
        deployment_params_cache = module_info_index.get_module_info(
            **module_info_index.get_key_for_module_name(group=group, module_name=destroy_module)
        )
        module_manifest = mi.get_module_manifest(deployment_name, group, destroy_module, deployment_params_cache)
        if module_manifest is not None:
            module_manifest["deploy_spec"] = mi.get_deployspec(
                deployment_name, group, destroy_module, deployment_params_cache
            )
            destroy_module_list.append(ModuleManifest(**module_manifest))
    return destroy_module_list


def update_deployspec(
    deployment: str, group: str, module: str, module_path: str, session: Optional[Session] = None
) -> None:
    d_path = mi.get_deployspec_path(module_path=module_path)
    with open(d_path) as deploymentspec:
        new_spec = DeploySpec(**yaml.safe_load(deploymentspec))
    mi.write_deployspec(deployment, group, module, new_spec.dict(), session=session)
