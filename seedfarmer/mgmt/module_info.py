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
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

from seedfarmer import OPS_ROOT, PROJECT
from seedfarmer.services import _secrets_manager as secrets
from seedfarmer.services import _ssm as store
from seedfarmer.utils import generate_hash

_logger: logging.Logger = logging.getLogger(__name__)


class ModuleConst(Enum):
    DEPLOYSPEC = "deployspec"
    BUNDLE = "bundle"
    METADATA = "metadata"
    MD5 = "md5"
    MANIFEST = "manifest"
    DEPLOYED = "deployed"


def get_parameter_data_cache(deployment: str) -> Dict[str, Any]:
    """
    get_parameter_data_cache
        Fetch the deployment parameters stored

    Parameters
    ----------
    deployment : str
       Name of the deployment

    Returns
    -------
    Dict[str,Any]
        A dictionary representation of what is in the store (SSM for DDB) of the modules deployed
    """
    return store.get_all_parameter_data_by_path(_deployment_key(deployment))


def get_all_deployments() -> List[str]:
    """
    get_all_deployments
        Get all names of curently deployments

    Returns
    -------
    List[str]
        A list of the deployments in the account
    """
    prefix = f"/{PROJECT}"
    _filter = f"{ModuleConst.MANIFEST.value}"
    ret = set()
    params = store.list_parameters_with_filter(prefix, _filter)
    for param in params:
        _logger.debug(param)
        p = param.split("/")[3]
        if ModuleConst.MANIFEST.value in p:
            ret.add(param.split("/")[2])
    return list(ret)


def get_all_groups(deployment: str, params_cache: Optional[Dict[str, Any]] = None) -> List[str]:
    """
    get_all_groups
        Get all groups in a deployment

    Parameters
    ----------
    deployment : str
       The name of the deployment
    params_cache : Dict[str,Any], optional
       A populated dict with the key  of the parameter stored and its value

    Returns
    -------
    List[str]
        A list of the group names
    """
    prefix = _deployment_key(deployment)
    _filter = f"{ModuleConst.MANIFEST.value}"
    ret = set()
    params = params_cache.keys() if params_cache else store.list_parameters_with_filter(prefix, _filter)
    for param in params:
        p = param.split("/")[3]
        if ModuleConst.MANIFEST.value not in p:
            ret.add(param.split("/")[3])
    return list(ret)


def get_deployed_modules(deployment: str, group: str, params_cache: Optional[Dict[str, Any]] = None) -> List[str]:
    """
    get_deployed_modules
        Get all modules deployed in a group of a deployment

    Parameters
    ----------
    deployment : str
        The name of the deployment
    group : str
        The name of the group
    params_cache : Dict[str,Any], optional
       A populated dict with the key  of the parameter stored and its value

    Returns
    -------
    List[str]
        A list of the names of the modules in the group
    """
    prefix = f"/{PROJECT}/{deployment}/{group}"
    _filter = f"{ModuleConst.MD5.value}/{ModuleConst.BUNDLE.value}"
    params = params_cache.keys() if params_cache else store.list_parameters_with_filter(prefix, _filter)
    ret: List[str] = []
    for param in params:
        ret.append(param.split("/")[4]) if _filter in param else None
    return ret


def get_module_md5(deployment: str, group: str, module: str, type: ModuleConst) -> Optional[str]:
    """
    get_module_md5
        Get the md5 of a currently deployed module.
        There are three (3) relative md5 hashes of the module:
            - bundle / zip of currently deployed module
            - deployspec of currently deployed module
            - manifest of currently deployed module

    Parameters
    ----------
    deployment : str
        The name of the deployment
    group : str
        The name of the group
    module : str
        The name of the module
    type : ModuleConst
        An emumeration value of the md5 of the module you want

    Returns
    -------
    Optional[str]
        The md5 hash as a string
    """
    name = _md5_module_key(deployment, group, module, type)
    p = store.get_parameter_if_exists(name=name)
    return p["hash"] if p else None


def get_module_metadata(
    deployment: str, group: str, module: str, params_cache: Optional[Dict[str, Any]] = None
) -> Optional[Dict[str, Any]]:
    """
    get_module_metadata
        Get the metadata stored for a deployed module

    Parameters
    ----------
    deployment : str
        The name of the deployment
    group : str
        The name of the group
    module : str
        The name of the module
    params_cache : Dict[str,Any], optional
       A populated dict with the key  of the parameter stored and its value

    Returns
    -------
    Optional[Dict[str, Any]]
        A dict containg the metadata of the module requested
    """
    return _fetch_helper(_metadata_key(deployment, group, module), params_cache)


def get_module_manifest(
    deployment: str, group: str, module: str, params_cache: Optional[Dict[str, Any]] = None
) -> Optional[Dict[str, Any]]:
    """
    get_module_manifest
        Get the manifest stored for a deployed module

    Parameters
    ----------
    deployment : str
        The name of the deployment
    group : str
        The name of the group
    module : str
        The name of the module
    params_cache : Dict[str,Any], optional
       A populated dict with the key  of the parameter stored and its value

    Returns
    -------
    Optional[Dict[str, Any]]
        A dict containg the manifest of the module requested
    """
    return _fetch_helper(_manifest_key(deployment, group, module), params_cache)


def get_deployspec(
    deployment: str, group: str, module: str, params_cache: Optional[Dict[str, Any]] = None
) -> Optional[Dict[str, Any]]:
    """
    get_deployspec
        Get the deployspec stored for a deployed module

    Parameters
    ----------
    deployment : str
        The name of the deployment
    group : str
        The name of the group
    module : str
        The name of the module
    params_cache : Dict[str,Any], optional
       A populated dict with the key  of the parameter stored and its value

    Returns
    -------
    Optional[Dict[str, Any]]
        A dict containg the deployspec of the module requested
    """
    return _fetch_helper(_deployspec_key(deployment, group, module), params_cache)


def get_deployment_manifest(deployment: str, params_cache: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
    """
    get_deployment_manifest
        Get the deployment manifest stored for a deployment

    Parameters
    ----------
    deployment : str
        The name of the deployment
    params_cache : Dict[str,Any], optional
       A populated dict with the key  of the parameter stored and its value

    Returns
    -------
    Optional[Dict[str, Any]]
        A dict of the deployment
    """
    return _fetch_helper(_deployment_manifest_key(deployment), params_cache)


def get_deployed_deployment_manifest(
    deployment: str, params_cache: Optional[Dict[str, Any]] = None
) -> Optional[Dict[str, Any]]:
    """
    get_deployed_deployment_manifest
        Get the deployment manifest stored for a completed successful deployment deployment

    Parameters
    ----------
    deployment : str
        The name of the deployment
    params_cache : Dict[str,Any], optional
       A populated dict with the key  of the parameter stored and its value

    Returns
    -------
    Optional[Dict[str, Any]]
        A dict of the deployment
    """
    return _fetch_helper(_deployed_deployment_manifest_key(deployment), params_cache)


def get_secret_secrets_manager(name: str) -> Dict[str, Any]:
    """
    get_secret_secrets_manager Fetches the data in the Secrets Manager with the key (name) given

    Parameters
    ----------
    name : str
        The name of the Secret in the Secrets manager

    Returns
    -------
    Dict[str, Any]
        The object in the Secrets Manager
    """
    return secrets.get_secret_secrets_manager(name=name)


def get_group_manifest(
    deployment: str, group: str, params_cache: Optional[Dict[str, Any]] = None
) -> Optional[Dict[str, Any]]:
    """
    get_group_manifest
        Get the group manifest stored for a deployed group

    Parameters
    ----------
    deployment : str
        The name of the deployment
    group : str
        The name of the group
    params_cache : Dict[str,Any], optional
       A populated dict with the key  of the parameter stored and its value

    Returns
    -------
    Optional[Dict[str, Any]]
        A dict of the group in a deployment
    """
    return _fetch_helper(_group_key(deployment, group), params_cache)


def does_md5_match(
    deployment: str,
    group: str,
    module: str,
    hash: str,
    type: ModuleConst,
    deployment_params_cache: Optional[Dict[str, Any]] = None,
) -> bool:
    """
    does_md5_match
        Check if a gneerated md5 hash matches what is currently deployed for a module

    Parameters
    ----------
    deployment : str
        The name of the deployment
    group : str
        The name of the group
    module : str
        The name of the module
    hash : str
        The generated md5 has you want to compare to what is currently dpeloyed
    type : ModuleConst
        An emumeration value of the md5 of the module you want
    params_cache : Dict[str,Any], optional
       A populated dict with the key  of the parameter stored and its value

    Returns
    -------
    bool
        Whether it does match or not
    """
    name = _md5_module_key(deployment, group, module, type)
    if not deployment_params_cache:
        p = store.get_parameter_if_exists(name=name)
    else:
        p = deployment_params_cache[name] if name in deployment_params_cache.keys() else None
    if not p:
        return False
    elif hash != p["hash"]:
        return False
    else:
        return True


def does_module_exist(deployment: str, group: str, module: str) -> bool:
    """
    does_module_exist
        Checks if a module of a group is deployed

    Parameters
    ----------
    deployment : str
        The name of the deployment
    group : str
        The name of the group
    module : str
        The name of the module
    Returns
    -------
    bool
        Whether the module is deployed
    """
    return store.does_parameter_exist(name=_md5_module_key(deployment, group, module, ModuleConst.BUNDLE))


def write_metadata(deployment: str, group: str, module: str, data: Dict[str, Any]) -> None:
    """
    write_metadata
        Persists the medadata of a deployed module

    Parameters
    ----------
    deployment : str
        The name of the deployment
    group : str
        The name of the group
    module : str
        The name of the module
    data : Dict[str, Any]
        The metadata of the module
    """
    store.put_parameter(name=_metadata_key(deployment, group, module), obj=data)


def write_group_manifest(deployment: str, group: str, data: Dict[str, Any]) -> None:
    """
    write_group_manifest
         Persists the manifest of a deployed group

    Parameters
    ----------
    deployment : str
        The name of the deployment
    group : str
        The name of the group
    data : Dict[str, Any]
        The metadat of the module
    """
    store.put_parameter(name=_group_key(deployment, group), obj=data)


def write_module_manifest(deployment: str, group: str, module: str, data: Dict[str, Any]) -> None:
    """
    write_module_manifest
        Persists the manifest of a deployed module

    Parameters
    ----------
    deployment : str
        The name of the deployment
    group : str
        The name of the group
    module : str
        The name of the module
    data : Dict[str, Any]
        A dict of the data to be persisted
    """
    store.put_parameter(name=_manifest_key(deployment, group, module), obj=data)


def write_deployspec(deployment: str, group: str, module: str, data: Dict[str, Any]) -> None:
    """
    write_deployspec
        Persists the deployspec of a deployed module

    Parameters
    ----------
    deployment : str
        The name of the deployment
    group : str
        The name of the group
    module : str
        The name of the module
    data : Dict[str, Any]
        A dict of the data to be persisted
    """
    store.put_parameter(name=_deployspec_key(deployment, group, module), obj=data)


def write_module_md5(deployment: str, group: str, module: str, hash: str, type: ModuleConst) -> None:
    """
    write_module_md5
        Persists the md5 of a module.
        There are three (3) relative md5 hashes of the module:
            - bundle / zip of currently deployed module
            - deployspec of currently deployed module
            - manifest of currently deployed module

    Parameters
    ----------
    deployment : str
        The name of the deployment
    group : str
        The name of the group
    module : str
        The name of the module
    hash : str
        The md5 has of the data
    type : ModuleConst
        An emumeration value of the md5 of the module this is
    """
    store.put_parameter(name=_md5_module_key(deployment, group, module, type), obj={"hash": hash})


def write_deployment_manifest(deployment: str, data: Dict[str, Any]) -> None:
    """
    write_deployment
        Persists the deployment manifest

    Parameters
    ----------
    deployment : str
        The name of the deployment
    data : Dict[str, Any]
        A dict of the deployment manifest
    """
    if _logger.isEnabledFor(logging.DEBUG):
        _logger.debug("Writing to %s values %s", _deployment_manifest_key(deployment), data)
    store.put_parameter(name=_deployment_manifest_key(deployment), obj=data)


def write_deployed_deployment_manifest(deployment: str, data: Dict[str, Any]) -> None:
    """
    write_deployed_deployment_manifest
        Persists the deployment manifest once all modules have been deployed

    Parameters
    ----------
    deployment : str
        The name of the deployment
    data : Dict[str, Any]
        A dict of the deployment manifest
    """
    key = _deployed_deployment_manifest_key(deployment)
    _logger.debug("Writing to %s value %s", key, data)

    store.put_parameter(name=key, obj=data)


def remove_module_info(deployment: str, group: str, module: str) -> None:
    """
    remove_module_info
        Delete all persisted data of a module in a group of a deployment

    Parameters
    ----------
    deployment : str
        The name of the deployment
    group : str
        The name of the group
    module : str
        The name of the module
    """
    store.delete_parameters(parameters=_all_module_keys(deployment, group, module))


def remove_group_info(deployment: str, group: str) -> None:
    """
    remove_group_info
        Delete all persisted data of a group of a deployment

    Parameters
    ----------
    deployment : str
        The name of the deployment
    group : str
        The name of the group
    """
    store.delete_parameters(parameters=(_all_group_keys(deployment, group)))


def remove_module_md5(deployment: str, group: str, module: str, type: ModuleConst) -> None:
    """
    remove_module_md5
        Delete the md5 hash persisted of a module.
        There are three (3) relative md5 hashes of the module:
            - bundle / zip of currently deployed module
            - deployspec of currently deployed module
            - manifest of currently deployed module

    Parameters
    ----------
    deployment : str
        The name of the deployment
    group : str
        The name of the group
    module : str
        The name of the module
    type : ModuleConst
         An emumeration value of the md5 you want to delete
    """
    store.delete_parameters(parameters=[_md5_module_key(deployment, group, module, type)])


def remove_deployment_manifest(deployment: str) -> None:
    """
    remove_deployment_manifest
        Delete the deployment manifest persisted of a deployment

    Parameters
    ----------
    deployment : str
        The name of the deployment
    """
    store.delete_parameters(parameters=[_deployment_manifest_key(deployment)])


def remove_deployed_deployment_manifest(deployment: str) -> None:
    """
    remove_deployment_manifest
        Delete the deployment manifest persisted of a deployment

    Parameters
    ----------
    deployment : str
        The name of the deployment
    """
    store.delete_parameters(parameters=[_deployed_deployment_manifest_key(deployment)])


def _metadata_key(deployment: str, group: str, module: str) -> str:
    return f"/{PROJECT}/{deployment}/{group}/{module}/{ModuleConst.METADATA.value}"


def _md5_module_key(deployment: str, group: str, module: str, type: ModuleConst) -> str:
    return f"/{PROJECT}/{deployment}/{group}/{module}/{ModuleConst.MD5.value}/{type.value}"


def _md5_group_key(deployment: str, group: str, type: ModuleConst) -> str:
    return f"/{PROJECT}/{deployment}/{group}/{ModuleConst.MD5.value}/{type.value}"


def _deployspec_key(deployment: str, group: str, module: str) -> str:
    return f"/{PROJECT}/{deployment}/{group}/{module}/{ModuleConst.DEPLOYSPEC.value}"


def _manifest_key(deployment: str, group: str, module: str) -> str:
    return f"/{PROJECT}/{deployment}/{group}/{module}/{ModuleConst.MANIFEST.value}"


def _group_key(deployment: str, group: str) -> str:
    return f"/{PROJECT}/{deployment}/{group}/{ModuleConst.MANIFEST.value}"


def _deployment_manifest_key(deployment: str) -> str:
    return f"/{PROJECT}/{deployment}/{ModuleConst.MANIFEST.value}"


def _deployed_deployment_manifest_key(deployment: str) -> str:
    return f"/{PROJECT}/{deployment}/{ModuleConst.MANIFEST.value}/{ModuleConst.DEPLOYED.value}"


def _all_module_keys(deployment: str, group: str, module: str) -> List[str]:
    return [
        _metadata_key(deployment, group, module),
        _md5_module_key(deployment, group, module, ModuleConst.DEPLOYSPEC),
        _md5_module_key(deployment, group, module, ModuleConst.BUNDLE),
        _md5_module_key(deployment, group, module, ModuleConst.MANIFEST),
        _deployspec_key(deployment, group, module),
        _manifest_key(deployment, group, module),
    ]


def _all_group_keys(deployment: str, group: str) -> List[str]:
    return [_group_key(deployment, group), _md5_group_key(deployment, group, ModuleConst.MANIFEST)]


def _deployment_key(deployment: str) -> str:
    return f"/{PROJECT}/{deployment}/"


def _fetch_helper(name: str, params_cache: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
    if params_cache:
        return params_cache[name] if name in params_cache.keys() else None
    else:
        return store.get_parameter_if_exists(name=name)


def _get_module_stack_names(deployment_name: str, group_name: str, module_name: str) -> Tuple[str, str]:
    module_stack_name = f"{PROJECT}-{deployment_name}-{group_name}-{module_name}-iam-policy"
    module_role_name = f"{PROJECT}-{deployment_name}-{group_name}-{module_name}-{generate_hash()}"
    return module_stack_name, module_role_name


def _get_modulestack_path(module_path: str) -> Any:
    p = os.path.join(OPS_ROOT, module_path, "modulestack.yaml")
    if not os.path.exists(p):
        _logger.debug("No modulestack.yaml found")
        return None
    return p


def _get_deployspec_path(module_path: str) -> str:
    p = os.path.join(OPS_ROOT, module_path, "deployspec.yaml")
    if not os.path.exists(p):
        raise Exception("No deployspec.yaml file found in module directory: %s", p)
    return os.path.join(OPS_ROOT, module_path, "deployspec.yaml")
