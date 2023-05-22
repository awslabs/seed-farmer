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
from typing import Any, Dict, List, cast

import seedfarmer.errors
import seedfarmer.services._ssm as ssm
from seedfarmer.models import ValueFromRef
from seedfarmer.models.manifests import NetworkMapping
from seedfarmer.services.session_manager import SessionManager

_logger: logging.Logger = logging.getLogger(__name__)


def load_network_values(
    network: NetworkMapping, parameters_regional: Dict[str, Any], account_id: str, region: str
) -> NetworkMapping:
    _logger.debug("Evaluating network for  %s and %s", account_id, region)

    if network.vpc_id is None and network.private_subnet_ids is None and network.security_group_ids is None:
        _logger.debug("None of the parameters are populated, ignoring networking")
        return network

    session = SessionManager().get_or_create().get_deployment_session(account_id=account_id, region_name=region)

    if isinstance(network.vpc_id, ValueFromRef):
        if network.vpc_id.value_from and network.vpc_id.value_from.parameter_value:
            network.vpc_id = cast(
                str,
                parameters_regional.get(str(network.vpc_id.value_from.parameter_value)),
            )
        elif network.vpc_id.value_from and network.vpc_id.value_from.parameter_store:
            network.vpc_id = cast(
                str, ssm.get_parameter(name=str(network.vpc_id.value_from.parameter_store), session=session)
            )
        elif network.vpc_id.value_from and network.vpc_id.value_from.env_variable:
            network.vpc_id = cast(str, os.getenv(network.vpc_id.value_from.env_variable, ""))

    if isinstance(network.private_subnet_ids, ValueFromRef):
        if network.private_subnet_ids.value_from and network.private_subnet_ids.value_from.parameter_value:
            network.private_subnet_ids = cast(
                List[str],
                parameters_regional.get(str(network.private_subnet_ids.value_from.parameter_value)),
            )
        elif network.private_subnet_ids.value_from and network.private_subnet_ids.value_from.parameter_store:
            network.private_subnet_ids = cast(
                List[str],
                ssm.get_parameter(name=str(network.private_subnet_ids.value_from.parameter_store), session=session),
            )
        elif network.private_subnet_ids.value_from and network.private_subnet_ids.value_from.env_variable:
            network.private_subnet_ids = cast(
                List[str],
                json.loads(os.getenv(network.private_subnet_ids.value_from.env_variable, "")),
            )
    if isinstance(network.security_group_ids, ValueFromRef):
        if network.security_group_ids.value_from and network.security_group_ids.value_from.parameter_value:
            network.security_group_ids = cast(
                List[str],
                parameters_regional.get(str(network.security_group_ids.value_from.parameter_value)),
            )
        elif network.security_group_ids.value_from and network.security_group_ids.value_from.parameter_store:
            network.security_group_ids = cast(
                List[str],
                ssm.get_parameter(name=str(network.security_group_ids.value_from.parameter_store), session=session),
            )
        elif network.security_group_ids.value_from and network.security_group_ids.value_from.env_variable:
            network.security_group_ids = cast(
                List[str],
                json.loads(os.getenv(network.security_group_ids.value_from.env_variable, "")),
            )

        if len(network.security_group_ids) > 5:  # type: ignore
            raise seedfarmer.errors.InvalidConfigurationError("Cannot have more than 5 Security Groups in a Network")

    _logger.debug("Returning network for %s - %s : %s", account_id, region, network)
    return network
