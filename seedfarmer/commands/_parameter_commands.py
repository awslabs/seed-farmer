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
from typing import Any, Dict, List, Optional, Tuple, cast

import seedfarmer.errors
import seedfarmer.mgmt.module_info as mi
from seedfarmer import config
from seedfarmer.mgmt.module_info import get_module_metadata
from seedfarmer.models.manifests import DeploymentManifest, ModuleManifest, ModuleParameter
from seedfarmer.services.session_manager import SessionManager
from seedfarmer.types.parameter_types import EnvVar, EnvVarType
from seedfarmer.utils import upper_snake_case

_logger: logging.Logger = logging.getLogger(__name__)


def generate_export_env_params(metadata: Optional[Dict[str, Any]]) -> Optional[List[str]]:
    envs: List[str] = []
    if metadata is not None:
        envs = [
            f"export {config.PROJECT.upper()}_PARAMETER_{upper_snake_case(k)}='{metadata[k]}'" for k in metadata.keys()
        ]
    return envs


def generate_export_raw_env_params(metadata: Optional[Dict[str, Any]]) -> Optional[List[str]]:
    envs: List[str] = []
    if metadata is not None:
        envs = [f"export {upper_snake_case(k)}='{metadata[k]}'" for k in metadata.keys()]
    return envs


def load_parameter_values(
    deployment_name: str,
    parameters: List[ModuleParameter],
    deployment_manifest: DeploymentManifest,
    target_account: Optional[str],
    target_region: Optional[str],
) -> List[ModuleParameter]:
    parameter_values = []
    parameter_values_cache: Dict[Tuple[str, str, str], Any] = {}
    for parameter in parameters:
        if _logger.isEnabledFor(logging.DEBUG):
            _logger.debug("parameter: %s", parameter.model_dump())

        if parameter.value is not None:
            _logger.debug("static parameter value: %s", parameter.value)
            parameter_values.append(parameter)
        elif parameter.value_from:
            if parameter.value_from.module_metadata:
                module_metatdata = _module_metatdata(
                    deployment_name, parameter, parameter_values_cache, deployment_manifest
                )
                if module_metatdata:
                    parameter_values.append(module_metatdata)
                else:
                    raise seedfarmer.errors.InvalidManifestError(
                        f"The module metadata parameter ({parameter.value_from.module_metadata}) is not available"
                    )
            elif parameter.value_from.env_variable:
                if parameter.value_from.env_variable in os.environ:
                    parameter_values.append(
                        ModuleParameter(name=parameter.name, value=os.getenv(parameter.value_from.env_variable, ""))
                    )
                else:
                    raise seedfarmer.errors.InvalidManifestError(
                        f"The environment variable ({parameter.value_from.env_variable}) is not available"
                    )
            elif parameter.value_from.parameter_store:
                parameter_values.append(
                    ModuleParameter(
                        name=parameter.name,
                        value=EnvVar(value=parameter.value_from.parameter_store, type=EnvVarType.PARAMETER_STORE),
                    ),
                )
            elif parameter.value_from.secrets_manager:
                parameter_values.append(
                    ModuleParameter(
                        name=parameter.name,
                        value=EnvVar(value=parameter.value_from.secrets_manager, type=EnvVarType.SECRETS_MANAGER),
                    ),
                )
            elif parameter.value_from.parameter_value:
                p_value = deployment_manifest.get_parameter_value(
                    parameter=parameter.value_from.parameter_value, account_id=target_account, region=target_region
                )
                if p_value is not None:
                    p_value = str(p_value) if isinstance(p_value, str) else json.dumps(p_value)
                    parameter_values.append(ModuleParameter(name=parameter.name, value=p_value))
                else:
                    raise seedfarmer.errors.InvalidManifestError(
                        f"The parameter value defined ({parameter.value_from.parameter_value}) is not available"
                    )

    return parameter_values


def resolve_params_for_checksum(
    deployment_manifest: DeploymentManifest,
    module: ModuleManifest,
    group_name: str,
) -> None:
    for param in module.parameters:
        if param.value_from and param.value_from.parameter_store:
            if ":" in param.value_from.parameter_store:
                raise seedfarmer.errors.InvalidConfigurationError(
                    f"CodeBuild does not support Versioned SSM Parameters -- see {group_name}-{module.name}"
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
        elif param.value_from and param.value_from.parameter_value:
            p_value = deployment_manifest.get_parameter_value(
                parameter=param.value_from.parameter_value,
                account_alias=module.target_account,
                region=module.target_region,
            )
            if p_value is not None:
                param.resolved_value = str(p_value) if isinstance(p_value, str) else json.dumps(p_value)
            else:
                raise seedfarmer.errors.InvalidManifestError(
                    f"The parameter value defined ({param.value_from.parameter_value}) is not available"
                )

        elif param.value_from and param.value_from.env_variable:
            if param.value_from.env_variable in os.environ:
                param.resolved_value = os.getenv(param.value_from.env_variable)
            else:
                raise seedfarmer.errors.InvalidManifestError(
                    f"The environment variable ({param.value_from.env_variable}) is not available"
                )


def _get_param_value_cache(
    d_name: str,
    g_name: str,
    m_name: str,
    parameter_values_cache: Dict[Tuple[str, str, str], Any],
    deployment_manifest: DeploymentManifest,
) -> Dict[Any, Any]:
    if (d_name, g_name, m_name) not in parameter_values_cache:
        module = deployment_manifest.get_module(group=g_name, module=m_name)
        if module is not None:
            module_session = (
                SessionManager()
                .get_or_create()
                .get_deployment_session(
                    account_id=cast(str, module.get_target_account_id()), region_name=cast(str, module.target_region)
                )
            )
            parameter_values_cache[(d_name, g_name, m_name)] = get_module_metadata(
                d_name, g_name, m_name, session=module_session
            )
        else:
            return {}
    return cast(Dict[Any, Any], parameter_values_cache[(d_name, g_name, m_name)])


def _module_metatdata(
    deployment_name: str,
    parameter: ModuleParameter,
    parameter_values_cache: Dict[Tuple[str, str, str], Any],
    deployment_manifest: DeploymentManifest,
) -> Optional[ModuleParameter]:
    if parameter.value_from and parameter.value_from.module_metadata:
        group = parameter.value_from.module_metadata.group
        module_name = parameter.value_from.module_metadata.name
        _logger.debug("Loading metadata for dependency group, module: %s, %s" % (group, module_name))

        # Ensure we only retrieve the SSM Parameter value once per module
        parameter_value = _get_param_value_cache(
            deployment_name, group, module_name, parameter_values_cache, deployment_manifest
        )
        _logger.debug("loaded parameter value: %s", parameter_value)

        parameter_value = (
            parameter_value.get(parameter.value_from.module_metadata.key, None)  # type: ignore[assignment]
            if parameter_value is not None and parameter.value_from.module_metadata.key is not None
            else parameter_value
        )
        _logger.debug("parsed parameter value: %s", parameter_value)

        if parameter_value is not None:
            return ModuleParameter(
                name=parameter.name,
                value=parameter_value,
            )
    return None
