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

import json
import logging
import os
import sys
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

from boto3 import Session

import seedfarmer.errors
from seedfarmer import config
from seedfarmer.services import _secrets_manager as secrets
from seedfarmer.services import _ssm as ssm
from seedfarmer.utils import generate_hash, generate_session_hash, remove_nulls

_logger: logging.Logger = logging.getLogger(__name__)


class ModuleConst(Enum):
    DEPLOYSPEC = "deployspec"
    BUNDLE = "bundle"
    METADATA = "metadata"
    MD5 = "md5"
    MANIFEST = "manifest"
    DEPLOYED = "deployed"


def get_parameter_data_cache(deployment: str, session: Session) -> Dict[str, Any]:
    """
    get_parameter_data_cache
        Fetch the deployment parameters stored

    Parameters
    ----------
    deployment : str
        Name of the deployment
    session: Session, optional
        The boto3.Session to use to for SSM Parameter queries, default None

    Returns
    -------
    Dict[str,Any]
        A dictionary representation of what is in the store (SSM for DDB) of the modules deployed
    """
    return ssm.get_all_parameter_data_by_path(prefix=_deployment_key(deployment), session=session)


def get_all_deployments(session: Optional[Session] = None) -> List[str]:
    """
    get_all_deployments
        Get all names of curently deployments
    session: Session, optional
        The boto3.Session to use to for SSM Parameter queries, default None
    session: Session, optional
        The boto3.Session to use to for SSM Parameter queries, default None

    Returns
    -------
    List[str]
        A list of the deployments in the account
    """
    prefix = f"/{config.PROJECT}"
    _filter = f"{ModuleConst.MANIFEST.value}"
    ret = set()
    params = ssm.list_parameters_with_filter(prefix=prefix, contains_string=_filter, session=session)
    for param in params:
        _logger.debug(param)
        p = param.split("/")[3]
        if ModuleConst.MANIFEST.value in p:
            ret.add(param.split("/")[2])
    return list(ret)


def get_all_groups(
    deployment: str, params_cache: Optional[Dict[str, Any]] = None, session: Optional[Session] = None
) -> List[str]:
    """
    get_all_groups
        Get all groups in a deployment

    Parameters
    ----------
    deployment : str
        The name of the deployment
    params_cache : Dict[str,Any], optional
        A populated dict with the key  of the parameter stored and its value
    session: Session, optional
        The boto3.Session to use to for SSM Parameter queries, default None

    Returns
    -------
    List[str]
        A list of the group names
    """
    prefix = _deployment_key(deployment)
    _filter = f"{ModuleConst.MANIFEST.value}"
    ret = set()
    params = (
        params_cache.keys()
        if params_cache
        else ssm.list_parameters_with_filter(prefix=prefix, contains_string=_filter, session=session)
    )
    for param in params:
        p = param.split("/")[3]
        if ModuleConst.MANIFEST.value not in p:
            ret.add(param.split("/")[3])
    return list(ret)


def get_deployed_modules(
    deployment: str, group: str, params_cache: Optional[Dict[str, Any]] = None, session: Optional[Session] = None
) -> List[str]:
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
    session: Session, optional
        The boto3.Session to use to for SSM Parameter queries, default None

    Returns
    -------
    List[str]
        A list of the names of the modules in the group
    """
    prefix = f"/{config.PROJECT}/{deployment}/{group}"
    _filter = f"{ModuleConst.MD5.value}/{ModuleConst.BUNDLE.value}"
    params = params_cache.keys() if params_cache else ssm.list_parameters_with_filter(prefix, _filter, session=session)
    ret: List[str] = []
    for param in params:
        ret.append(param.split("/")[4]) if _filter in param else None
    return ret


def get_module_md5(
    deployment: str, group: str, module: str, type: ModuleConst, session: Optional[Session] = None
) -> Optional[str]:
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
    session: Session, optional
        The boto3.Session to use to for SSM Parameter queries, default None

    Returns
    -------
    Optional[str]
        The md5 hash as a string
    """
    name = _md5_module_key(deployment, group, module, type)
    p = ssm.get_parameter_if_exists(name=name, session=session)
    return p["hash"] if p else None


def get_module_metadata(
    deployment: str,
    group: str,
    module: str,
    params_cache: Optional[Dict[str, Any]] = None,
    session: Optional[Session] = None,
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
    session: Session, optional
        The boto3.Session to use to for SSM Parameter queries, default None

    Returns
    -------
    Optional[Dict[str, Any]]
        A dict containg the metadata of the module requested
    """
    return _fetch_helper(_metadata_key(deployment, group, module), params_cache, session=session)


def get_module_manifest(
    deployment: str,
    group: str,
    module: str,
    params_cache: Optional[Dict[str, Any]] = None,
    session: Optional[Session] = None,
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
    session: Session, optional
        The boto3.Session to use to for SSM Parameter queries, default None

    Returns
    -------
    Optional[Dict[str, Any]]
        A dict containg the manifest of the module requested
    """
    return _fetch_helper(_manifest_key(deployment, group, module), params_cache, session=session)


def get_deployspec(
    deployment: str,
    group: str,
    module: str,
    params_cache: Optional[Dict[str, Any]] = None,
    session: Optional[Session] = None,
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
    session: Session, optional
        The boto3.Session to use to for SSM Parameter queries, default None

    Returns
    -------
    Optional[Dict[str, Any]]
        A dict containg the deployspec of the module requested
    """
    return _fetch_helper(_deployspec_key(deployment, group, module), params_cache, session=session)


def get_deployment_manifest(
    deployment: str, params_cache: Optional[Dict[str, Any]] = None, session: Optional[Session] = None
) -> Optional[Dict[str, Any]]:
    """
    get_deployment_manifest
        Get the deployment manifest stored for a deployment

    Parameters
    ----------
    deployment : str
        The name of the deployment
    params_cache : Dict[str,Any], optional
        A populated dict with the key  of the parameter stored and its value
    session: Session, optional
        The boto3.Session to use to for SSM Parameter queries, default None

    Returns
    -------
    Optional[Dict[str, Any]]
        A dict of the deployment
    """
    return _fetch_helper(_deployment_manifest_key(deployment), params_cache, session=session)


def get_deployed_deployment_manifest(
    deployment: str, params_cache: Optional[Dict[str, Any]] = None, session: Optional[Session] = None
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
    session: Session, optional
        The boto3.Session to use to for SSM Parameter queries, default None

    Returns
    -------
    Optional[Dict[str, Any]]
        A dict of the deployment
    """
    return _fetch_helper(_deployed_deployment_manifest_key(deployment), params_cache, session=session)


def get_secret_secrets_manager(name: str, session: Optional[Session] = None) -> Dict[str, Any]:
    """
    get_secret_secrets_manager Fetches the data in the Secrets Manager with the key (name) given

    Parameters
    ----------
    name : str
        The name of the Secret in the Secrets manager
    session: Session, optional
        The boto3.Session to use to for SSM Parameter queries, default None

    Returns
    -------
    Dict[str, Any]
        The object in the Secrets Manager
    """
    return secrets.get_secrets_manager_value(name=name, session=session)


def get_secrets_version(
    secret_name: str,
    version_ref: Optional[str] = "AWSCURRENT",
    session: Optional[Session] = None,
) -> Optional[str]:
    versions = secrets.list_secret_version_ids(name=secret_name, session=session)

    if versions:
        for version in versions:
            version_id = version["VersionId"]
            version_stages = version["VersionStages"]
            if (version_id == version_ref) or (version_ref in version_stages):
                return str(version_id)
    return None


def get_ssm_parameter_version(
    ssm_parameter_name: str,
    session: Optional[Session] = None,
) -> Optional[int]:
    resp = ssm.describe_parameter(name=ssm_parameter_name, session=session)
    if resp is None:
        _logger.error("The SSM parameter %s could not be fetched", ssm_parameter_name)
        raise seedfarmer.errors.ModuleDeploymentError("The SSM parameter could not be fetched")
    else:
        return int(resp["Parameters"][0]["Version"]) if len(resp["Parameters"]) > 0 else None


def get_group_manifest(
    deployment: str, group: str, params_cache: Optional[Dict[str, Any]] = None, session: Optional[Session] = None
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
    session: Session, optional
        The boto3.Session to use to for SSM Parameter queries, default None

    Returns
    -------
    Optional[Dict[str, Any]]
        A dict of the group in a deployment
    """
    return _fetch_helper(_group_key(deployment, group), params_cache, session=session)


def does_md5_match(
    deployment: str,
    group: str,
    module: str,
    hash: str,
    type: ModuleConst,
    deployment_params_cache: Optional[Dict[str, Any]] = None,
    session: Optional[Session] = None,
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
    session: Session, optional
        The boto3.Session to use to for SSM Parameter queries, default None

    Returns
    -------
    bool
        Whether it does match or not
    """
    name = _md5_module_key(deployment, group, module, type)
    if not deployment_params_cache:
        p = ssm.get_parameter_if_exists(name=name, session=session)
    else:
        p = deployment_params_cache[name] if name in deployment_params_cache.keys() else None
    if not p:
        return False
    elif hash != p["hash"]:
        return False
    else:
        return True


def does_module_exist(deployment: str, group: str, module: str, session: Optional[Session] = None) -> bool:
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
    session: Session, optional
        The boto3.Session to use to for SSM Parameter queries, default None

    Returns
    -------
    bool
        Whether the module is deployed
    """
    return ssm.does_parameter_exist(
        name=_md5_module_key(deployment, group, module, ModuleConst.BUNDLE), session=session
    )


def write_metadata(
    deployment: str, group: str, module: str, data: Dict[str, Any], session: Optional[Session] = None
) -> None:
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
    session: Session, optional
        The boto3.Session to use to for SSM Parameter queries, default None
    """
    ssm.put_parameter(name=_metadata_key(deployment, group, module), obj=data, session=session)


def write_group_manifest(deployment: str, group: str, data: Dict[str, Any], session: Optional[Session] = None) -> None:
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
    session: Session, optional
        The boto3.Session to use to for SSM Parameter queries, default None
    """
    ssm.put_parameter(name=_group_key(deployment, group), obj=data, session=session)


def write_module_manifest(
    deployment: str, group: str, module: str, data: Dict[str, Any], session: Optional[Session] = None
) -> None:
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
    session: Session, optional
        The boto3.Session to use to for SSM Parameter queries, default None
    """

    # Temp fix until a larger persistence store is vetted
    process_data = data
    current_size = sys.getsizeof(json.dumps(data))
    if current_size > 8191:
        _logger.info("The manifest for %s-%s is %s, too large for SSM, reducing", group, module, current_size)
        process_data = remove_nulls(data)
        _logger.info("The size is now %s", sys.getsizeof(json.dumps(process_data)))
    ssm.put_parameter(name=_manifest_key(deployment, group, module), obj=process_data, session=session)


def write_deployspec(
    deployment: str, group: str, module: str, data: Dict[str, Any], session: Optional[Session] = None
) -> None:
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
    session: Session, optional
        The boto3.Session to use to for SSM Parameter queries, default None
    """
    ssm.put_parameter(name=_deployspec_key(deployment, group, module), obj=data, session=session)


def write_module_md5(
    deployment: str, group: str, module: str, hash: str, type: ModuleConst, session: Optional[Session] = None
) -> None:
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
    session: Session, optional
        The boto3.Session to use to for SSM Parameter queries, default None
    """
    ssm.put_parameter(name=_md5_module_key(deployment, group, module, type), obj={"hash": hash}, session=session)


def write_deployment_manifest(deployment: str, data: Dict[str, Any], session: Optional[Session] = None) -> None:
    """
    write_deployment
        Persists the deployment manifest

    Parameters
    ----------
    deployment : str
        The name of the deployment
    data : Dict[str, Any]
        A dict of the deployment manifest
    session: Session, optional
        The boto3.Session to use to for SSM Parameter queries, default None
    """
    if _logger.isEnabledFor(logging.DEBUG):
        _logger.debug("Writing to %s values %s", _deployment_manifest_key(deployment), data)
    ssm.put_parameter(name=_deployment_manifest_key(deployment), obj=data, session=session)


def write_deployed_deployment_manifest(
    deployment: str, data: Dict[str, Any], session: Optional[Session] = None
) -> None:
    """
    write_deployed_deployment_manifest
        Persists the deployment manifest once all modules have been deployed

    Parameters
    ----------
    deployment : str
        The name of the deployment
    data : Dict[str, Any]
        A dict of the deployment manifest
    session: Session, optional
        The boto3.Session to use to for SSM Parameter queries, default None
    """
    key = _deployed_deployment_manifest_key(deployment)
    _logger.debug("Writing to %s value %s", key, data)

    ssm.put_parameter(name=key, obj=data, session=session)


def remove_module_info(deployment: str, group: str, module: str, session: Optional[Session] = None) -> None:
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
    session: Session, optional
        The boto3.Session to use to for SSM Parameter queries, default None
    """
    ssm.delete_parameters(parameters=_all_module_keys(deployment, group, module), session=session)


def remove_group_info(deployment: str, group: str, session: Optional[Session] = None) -> None:
    """
    remove_group_info
        Delete all persisted data of a group of a deployment

    Parameters
    ----------
    deployment : str
        The name of the deployment
    group : str
        The name of the group
    session: Session, optional
        The boto3.Session to use to for SSM Parameter queries, default None
    """
    ssm.delete_parameters(parameters=(_all_group_keys(deployment, group)), session=session)


def remove_module_md5(
    deployment: str, group: str, module: str, type: ModuleConst, session: Optional[Session] = None
) -> None:
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
    session: Session, optional
        The boto3.Session to use to for SSM Parameter queries, default None
    """
    ssm.delete_parameters(parameters=[_md5_module_key(deployment, group, module, type)], session=session)


def remove_deployment_manifest(deployment: str, session: Optional[Session] = None) -> None:
    """
    remove_deployment_manifest
        Delete the deployment manifest persisted of a deployment

    Parameters
    ----------
    deployment : str
        The name of the deployment
    session: Session, optional
        The boto3.Session to use to for SSM Parameter queries, default None
    """
    ssm.delete_parameters(parameters=[_deployment_manifest_key(deployment)], session=session)


def remove_deployed_deployment_manifest(deployment: str, session: Optional[Session] = None) -> None:
    """
    remove_deployment_manifest
        Delete the deployment manifest persisted of a deployment

    Parameters
    ----------
    deployment : str
        The name of the deployment
    session: Session, optional
        The boto3.Session to use to for SSM Parameter queries, default None
    """
    ssm.delete_parameters(parameters=[_deployed_deployment_manifest_key(deployment)], session=session)


def _metadata_key(deployment: str, group: str, module: str) -> str:
    return f"/{config.PROJECT}/{deployment}/{group}/{module}/{ModuleConst.METADATA.value}"


def _md5_module_key(deployment: str, group: str, module: str, type: ModuleConst) -> str:
    return f"/{config.PROJECT}/{deployment}/{group}/{module}/{ModuleConst.MD5.value}/{type.value}"


def _md5_group_key(deployment: str, group: str, type: ModuleConst) -> str:
    return f"/{config.PROJECT}/{deployment}/{group}/{ModuleConst.MD5.value}/{type.value}"


def _deployspec_key(deployment: str, group: str, module: str) -> str:
    return f"/{config.PROJECT}/{deployment}/{group}/{module}/{ModuleConst.DEPLOYSPEC.value}"


def _manifest_key(deployment: str, group: str, module: str) -> str:
    return f"/{config.PROJECT}/{deployment}/{group}/{module}/{ModuleConst.MANIFEST.value}"


def _group_key(deployment: str, group: str) -> str:
    return f"/{config.PROJECT}/{deployment}/{group}/{ModuleConst.MANIFEST.value}"


def _deployment_manifest_key(deployment: str) -> str:
    return f"/{config.PROJECT}/{deployment}/{ModuleConst.MANIFEST.value}"


def _deployed_deployment_manifest_key(deployment: str) -> str:
    return f"/{config.PROJECT}/{deployment}/{ModuleConst.MANIFEST.value}/{ModuleConst.DEPLOYED.value}"


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
    return f"/{config.PROJECT}/{deployment}/"


def _fetch_helper(
    name: str, params_cache: Optional[Dict[str, Any]] = None, session: Optional[Session] = None
) -> Optional[Dict[str, Any]]:
    if params_cache:
        return params_cache.get(name, None)  # type: ignore[no-any-return]
    else:
        return ssm.get_parameter_if_exists(name=name, session=session)


def get_module_stack_names(
    deployment_name: str, group_name: str, module_name: str, session: Optional[Session] = None
) -> Tuple[str, str]:
    resource_name = f"{config.PROJECT}-{deployment_name}-{group_name}-{module_name}"
    resource_hash = generate_hash(string=resource_name, length=4)
    # Max length of a Stack Name is 128 chars, -iam-policy is 11 chars, resource_hash plus "-" is 5 chars
    # If the resource_name and "-iam-policy" is too long, truncate and use a resource_hash for uniqueness
    module_stack_name = (
        f"{resource_name[:128 - 11 - 5]}-{resource_hash}-iam-policy"
        if len(resource_name) > (128 - 11)
        else f"{resource_name}-iam-policy"
    )

    # Max length of a a Role Name is 64 chars, session_hash plus "-" is 9 chars, resource_hash plus "-" is 5 chars
    # If the resource_name and session_hash is too long, truncate and use a resource_hash for uniqueness
    session_hash = generate_session_hash(session=session)
    module_role_name = (
        f"{resource_name[:64 - 9 - 5]}-{resource_hash}-{session_hash}"
        if len(resource_name) > (64 - 9)
        else f"{resource_name}-{session_hash}"
    )

    return module_stack_name, module_role_name


def get_modulestack_path(module_path: str) -> Any:
    p = os.path.join(config.OPS_ROOT, module_path, "modulestack.yaml")
    if not os.path.exists(p):
        _logger.debug("No modulestack.yaml found")
        return None
    return p


def get_deployspec_path(module_path: str) -> str:
    p = os.path.join(config.OPS_ROOT, module_path, "deployspec.yaml")
    if not os.path.exists(p):
        raise seedfarmer.errors.InvalidPathError(f"No deployspec.yaml file found in module directory: {p}")
    return os.path.join(config.OPS_ROOT, module_path, "deployspec.yaml")
