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
from threading import Lock
from typing import Any, Dict, List, Optional, Set, Tuple, cast

import yaml
from boto3 import Session

import seedfarmer.mgmt.module_info as mi
from seedfarmer.models.manifests import DeploymentManifest, DeploySpec, ModuleManifest, ModulesManifest
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
        Fetch all info for the deployemnt currently stored, across all Target accounts and regions

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
    # TODO: Enable multi-threaded query of account/region pairs
    for account_region in deployment_manifest.target_accounts_regions:
        account_id = account_region["account_id"]
        region = account_region["region"]
        session = SessionManager().get_or_create().get_deployment_session(account_id=account_id, region_name=region)
        module_info = mi.get_parameter_data_cache(deployment=deployment_manifest.name, session=session)
        for key, value in module_info.items():
            key_parts = key.split("/")[1:]
            if len(key_parts) < 4:
                continue
            group = key_parts[2]
            module_name = key_parts[3]
            module_info_index.index_module_info(
                group=group,
                account_id=account_id,
                region=region,
                module_name=module_name,
                module_info={key: value},
            )
    return module_info_index


def write_deployed_deployment_manifest(deployment_manifest: DeploymentManifest) -> None:
    """
    write_deployed_deployment_manifest
        Write the deployment manifest to the store

    Parameters
    ----------
    deployment_manifest : DeploymentManifest
        The deployment manifest ojject to store
    """
    deployment_name = deployment_manifest.name
    for group in deployment_manifest.groups:
        delattr(group, "modules")
    session = SessionManager().get_or_create().toolchain_session
    mi.write_deployed_deployment_manifest(deployment=deployment_name, data=deployment_manifest.dict(), session=session)


def generate_deployed_manifest(
    deployment_name: str,
    skip_deploy_spec: bool = False,
) -> Optional[DeploymentManifest]:
    """
    Generate a DeploymentManifest object from based off deployed modules in a deployment

    Parameters
    ----------
    deployment_name : str
        The name of the deployment the manifest is generated for
    skip_deploy_spec : bool, optional
        Skip populating each module deployspec - handy for getting the list of deployed modules quickly

    Returns
    -------
    Optional[DeploymentManifest]
        The hydrated DeploymentManifest object of deployed modules
    """
    session_manager = SessionManager().get_or_create()
    dep_manifest_dict = mi.get_deployed_deployment_manifest(deployment_name, session=session_manager.toolchain_session)
    if dep_manifest_dict is None:
        # No successful deployments, just use what was last requested
        dep_manifest_dict = mi.get_deployment_manifest(deployment_name, session=session_manager.toolchain_session)
    deployed_manifest = None
    if dep_manifest_dict:
        deployed_manifest = DeploymentManifest(**dep_manifest_dict)
        module_info_index = populate_module_info_index(deployment_manifest=deployed_manifest)
        for module_group in dep_manifest_dict["groups"] if dep_manifest_dict["groups"] else []:
            # TODO: Investigate whether this group manifest in SSM is needed, for now load from index
            # from_ssm = mi.get_group_manifest(deployment_name, group_name, module_info_index.get_keys_for_group())
            group_name = module_group["name"]
            module_group["modules"] = _populate_group_modules_from_index(
                deployment_name=deployment_name,
                group_name=group_name,
                module_info_index=module_info_index,
                skip_deploy_spec=skip_deploy_spec,
            )
        deployed_manifest.groups = [ModulesManifest(**group) for group in dep_manifest_dict["groups"]]
    return deployed_manifest


def need_to_build(
    deployment_name: str,
    group_name: str,
    module_manifest: ModuleManifest,
    module_deployspec: DeploySpec,
    module_deployspec_md5: str,
    module_manifest_md5: str,
    dryrun: bool = False,
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
        A populated ModuleManifest Object corrresponding to the module
    module_deployspec : DeploySpec
        A populated DeploySpec Object corrresponding to the module
    module_deployspec_md5 : str
        The MD5 hash of the deployspec file
    module_manifest_md5 : str
        The MD5 hash of the module manifest file

    Returns
    -------
    bool
        Indicator whether the module needs to be build or not.
        True - yes, built it
        False - no, do not build it
    """

    d = deployment_name
    g = group_name
    m = module_manifest.name if module_manifest.name else ""
    module_bundle_md5 = module_manifest.bundle_md5 if module_manifest.bundle_md5 else ""
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
            d, g, m, str(module_bundle_md5), mi.ModuleConst.BUNDLE, deployment_params_cache, session=session
        )
        and mi.does_md5_match(
            d, g, m, module_deployspec_md5, mi.ModuleConst.DEPLOYSPEC, deployment_params_cache, session=session
        )
        and mi.does_md5_match(
            d, g, m, module_manifest_md5, mi.ModuleConst.MANIFEST, deployment_params_cache, session=session
        )
    ):
        return False
    else:
        if not dryrun:
            mi.write_deployspec(deployment=d, group=g, module=m, data=module_deployspec.dict(), session=session)
            mi.write_module_manifest(deployment=d, group=g, module=m, data=module_manifest.dict(), session=session)
            mi.write_module_md5(
                deployment=d,
                group=g,
                module=m,
                hash=module_deployspec_md5,
                type=mi.ModuleConst.DEPLOYSPEC,
                session=session,
            )
            mi.write_module_md5(
                deployment=d, group=g, module=m, hash=module_manifest_md5, type=mi.ModuleConst.MANIFEST, session=session
            )
            mi.remove_module_md5(deployment=d, group=g, module=m, type=mi.ModuleConst.BUNDLE, session=session)
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
    deployment_name = apply_manifest.name

    destroy_manifest = apply_manifest.copy()
    delattr(destroy_manifest, "groups")
    destroy_group_list = _populate_groups_to_remove(deployment_name, apply_manifest.groups, module_info_index)
    destroy_manifest.groups = destroy_group_list
    for group in apply_manifest.groups:
        destroy_module_list = _populate_modules_to_remove(deployment_name, group.name, group.modules, module_info_index)
        if destroy_module_list:
            to_destroy = ModulesManifest(name=group.name, path=group.path, modules=destroy_module_list)
            destroy_manifest.groups.append(to_destroy)
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
        # TODO: Investigate whether it's necessary to read the existing group manifest from SSM
        # group_manifest = mi.get_group_manifest(deployment_name, destroy_group, deployment_params_cache)
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
    d_path = mi._get_deployspec_path(module_path=module_path)
    with open(d_path) as deploymentspec:
        new_spec = DeploySpec(**yaml.safe_load(deploymentspec))
    mi.write_deployspec(deployment, group, module, new_spec.dict(), session=session)
