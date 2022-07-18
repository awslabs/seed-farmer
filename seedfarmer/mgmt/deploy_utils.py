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
from typing import Any, Dict, List, Optional

import yaml

import seedfarmer.mgmt.module_info as mi
from seedfarmer.models.manifests import DeploymentManifest, DeploySpec, ModuleManifest, ModulesManifest

_logger: logging.Logger = logging.getLogger(__name__)


def generate_deployment_cache(deployment_name: str) -> Optional[Dict[str, Any]]:
    """
    generate_deployment_cache
        Fetch all parameters for the deployemnt currently stored

    Parameters
    ----------
    deployment_name: str
        The name of the deployment

    Returns
    -------
    Dict[str,Any]
        A dictionary representation of what is in the store (SSM for DDB) of the modules deployed
    """
    c = mi.get_parameter_data_cache(deployment=deployment_name)
    return c if len(c) > 0 else None


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
    mi.write_deployed_deployment_manifest(deployment=deployment_name, data=deployment_manifest.dict())


def generate_deployed_manifest(
    deployment_name: str,
    deployment_params_cache: Optional[Dict[str, Any]] = None,
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
    dep_manifest_dict = mi.get_deployed_deployment_manifest(deployment_name, deployment_params_cache)
    if dep_manifest_dict is None:
        # No successful deployments, just use what was last requested
        dep_manifest_dict = mi.get_deployment_manifest(deployment_name, deployment_params_cache)
    destroy_manifest = None
    if dep_manifest_dict:
        for module_group in dep_manifest_dict["groups"] if dep_manifest_dict["groups"] else []:
            group_name = module_group["name"]
            from_ssm = mi.get_group_manifest(deployment_name, group_name, deployment_params_cache)
            if from_ssm:
                module_group["modules"] = from_ssm["modules"]
                if not skip_deploy_spec:
                    for module in module_group["modules"] if module_group["modules"] else []:
                        module["deploy_spec"] = mi.get_deployspec(deployment_name, group_name, module["name"])
        destroy_manifest = DeploymentManifest(**dep_manifest_dict)
    return destroy_manifest


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
    module_bundle_md5 = module_manifest.bundle_md5 if module_manifest.bundle_md5 else []

    if (
        mi.does_md5_match(d, g, m, str(module_bundle_md5), mi.ModuleConst.BUNDLE, deployment_params_cache)
        and mi.does_md5_match(d, g, m, module_deployspec_md5, mi.ModuleConst.DEPLOYSPEC, deployment_params_cache)
        and mi.does_md5_match(d, g, m, module_manifest_md5, mi.ModuleConst.MANIFEST, deployment_params_cache)
    ):
        return False
    else:
        if not dryrun:
            mi.write_deployspec(deployment=d, group=g, module=m, data=module_deployspec.dict())
            mi.write_module_manifest(deployment=d, group=g, module=m, data=module_manifest.dict())
            mi.write_module_md5(
                deployment=d, group=g, module=m, hash=module_deployspec_md5, type=mi.ModuleConst.DEPLOYSPEC
            )
            mi.write_module_md5(deployment=d, group=g, module=m, hash=module_manifest_md5, type=mi.ModuleConst.MANIFEST)
            mi.remove_module_md5(deployment=d, group=g, module=m, type=mi.ModuleConst.BUNDLE)
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


def filter_deploy_destroy(
    apply_manifest: DeploymentManifest, deployment_params_cache: Optional[Dict[str, Any]] = None
) -> DeploymentManifest:
    """
    This method takes a populated DeploymentManifest object based off the requested deployment.
    It compares this requested deployment with what is currently deployed.  If there are groups or
    modules that are not in the request, a DeploymentManifest object is returned populated with all
    the information of modules to be destroyed.

    Parameters
    ----------
    apply_manifest : DeploymentManifest
        The DeploymentManifest object based off a deployment manifest of a requested deployment.

    Returns
    -------
    DeploymentManifest
        A populated DeploymentManifest object with the modules needed to be destroyed
    """ """"""
    dep_name = apply_manifest.name

    destroy_manifest = apply_manifest.copy()
    delattr(destroy_manifest, "groups")
    destroy_group_list = _populate_groups_to_remove(dep_name, apply_manifest.groups)
    destroy_manifest.groups = destroy_group_list
    for group in apply_manifest.groups:
        destroy_module_list = _populate_modules_to_remove(dep_name, group.name, group.modules, deployment_params_cache)
        if destroy_module_list:
            to_destroy = ModulesManifest(name=group.name, path=group.path, modules=destroy_module_list)
            destroy_manifest.groups.append(to_destroy)
    return destroy_manifest


def _populate_groups_to_remove(
    dep_name: str, apply_groups: List[ModulesManifest], deployment_params_cache: Optional[Dict[str, Any]] = None
) -> List[ModulesManifest]:
    set_requested_groups = set([g.name for g in apply_groups])
    set_deployed_groups = set(mi.get_all_groups(dep_name))
    destroy_groups = list(sorted(set_deployed_groups - set_requested_groups))
    _logger.debug("Groups already deployed that will be DESTROYED : %s", destroy_groups)
    destroy_group_list = []
    for destroy_group in destroy_groups:
        group_manifests = mi.get_group_manifest(dep_name, destroy_group, deployment_params_cache)
        if group_manifests:
            valid_modules = []
            for module in group_manifests["modules"]:
                mod_manifest = mi.get_module_manifest(dep_name, destroy_group, module["name"], deployment_params_cache)
                if mod_manifest:
                    module["deploy_spec"] = mi.get_deployspec(
                        dep_name, destroy_group, module["name"], deployment_params_cache
                    )
                    module["parameters"] = mod_manifest["parameters"]
                    valid_modules.append(module)
            if valid_modules:
                group_manifests["modules"] = valid_modules
            destroy_group_list.append(ModulesManifest(**group_manifests))
    return destroy_group_list


def _populate_modules_to_remove(
    dep_name: str,
    group: str,
    apply_modules: List[ModuleManifest],
    deployment_params_cache: Optional[Dict[str, Any]] = None,
) -> List[ModuleManifest]:
    set_requests_modules = set([m.name for m in apply_modules])
    set_deployed_modules = set(mi.get_deployed_modules(dep_name, group, deployment_params_cache))
    destroy_modules = list(sorted(set_deployed_modules - set_requests_modules))
    _logger.debug("Modules of Group %s already deployed that will be DESTROYED: %s", group, destroy_modules)

    destroy_module_list = []
    for destroy_module in destroy_modules:
        mod_manifest = mi.get_module_manifest(dep_name, group, destroy_module, deployment_params_cache)
        if mod_manifest:
            mod_manifest["deploy_spec"] = mi.get_deployspec(dep_name, group, destroy_module, deployment_params_cache)
            destroy_module_list.append(ModuleManifest(**mod_manifest))
    return destroy_module_list


def update_deployspec(deployment: str, group: str, module: str, module_path: str) -> None:
    d_path = mi._get_deployspec_path(module_path=module_path)
    with open(d_path) as deploymentspec:
        new_spec = DeploySpec(**yaml.safe_load(deploymentspec))
    mi.write_deployspec(deployment, group, module, new_spec.dict())
