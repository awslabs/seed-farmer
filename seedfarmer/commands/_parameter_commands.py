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
from typing import Any, Dict, List, Optional, Tuple

from seedfarmer import PROJECT
from seedfarmer.mgmt.module_info import get_module_metadata
from seedfarmer.models.manifests import ModuleParameter
from seedfarmer.utils import upper_snake_case

_logger: logging.Logger = logging.getLogger(__name__)


def generate_export_env_params(metadata: Optional[Dict[str, Any]]) -> Optional[List[str]]:
    envs: List[str] = [
        f"export {PROJECT.upper()}_PARAMETER_{upper_snake_case(k)}={metadata[k]}"
        for k in metadata.keys()  # type: ignore
        if metadata is not None and metadata.keys() is not None
    ]
    return envs


def load_parameter_values(deployment_name: str, parameters: List[ModuleParameter]) -> List[ModuleParameter]:
    parameter_values = []
    parameter_values_cache: Dict[Tuple[str, str, str], Any] = {}
    for parameter in parameters:
        if _logger.isEnabledFor(logging.DEBUG):
            _logger.debug("parameter: %s", parameter.dict())
        if parameter.value:
            _logger.debug("static parameter value: %s", parameter.value)
            parameter_values.append(parameter)
        # Load parameter from Module Metadata
        elif parameter.value_from and parameter.value_from.module_metadata:
            module_metatdata = _module_metatdata(deployment_name, parameter, parameter_values_cache)
            parameter_values.append(module_metatdata) if module_metatdata else None
    return parameter_values


def _get_param_value_cache(
    d_name: str, g_name: str, m_name: str, parameter_values_cache: Dict[Tuple[str, str, str], Any]
) -> Dict[Any, Any]:
    if (d_name, g_name, m_name) not in parameter_values_cache:
        parameter_values_cache[(d_name, g_name, m_name)] = get_module_metadata(
            d_name,
            g_name,
            m_name,
        )
    return parameter_values_cache[(d_name, g_name, m_name)]


def _module_metatdata(
    deployment_name: str, parameter: ModuleParameter, parameter_values_cache: Dict[Tuple[str, str, str], Any]
) -> Optional[ModuleParameter]:
    if parameter.value_from and parameter.value_from.module_metadata:
        group = parameter.value_from.module_metadata.group
        module_name = parameter.value_from.module_metadata.name
        _logger.debug("Loading metadata for dependency group, module: %s, %s" % (group, module_name))

        # Ensure we only retrieve the SSM Parameter value once per module
        parameter_value = _get_param_value_cache(deployment_name, group, module_name, parameter_values_cache)
        _logger.debug("loaded parameter value: %s", parameter_value)

        parameter_value = (
            parameter_value.get(parameter.value_from.module_metadata.key, None)
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
