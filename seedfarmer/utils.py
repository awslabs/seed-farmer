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

import hashlib
import logging

import humps
import yaml

from seedfarmer.services._service_utils import get_account_id, get_region

_logger: logging.Logger = logging.getLogger(__name__)

NoDatesSafeLoader = yaml.SafeLoader


class CfnSafeYamlLoader(yaml.SafeLoader):
    """
    CfnSafeYamlLoader
    A predefined class loader to support safely reading YAML files

    Parameters
    ----------
    yaml : _type_
    """ """"""

    yaml_implicit_resolvers = {
        k: [r for r in v if r[0] != "tag:yaml.org,2002:timestamp"]
        for k, v in NoDatesSafeLoader.yaml_implicit_resolvers.items()
    }


def upper_snake_case(value: str) -> str:
    """
    This will convert strings to a standard format

    Parameters
    ----------
    value : str
        The string you want to convert

    Returns
    -------
    str
        the string standardized
    """ """"""
    if humps.is_camelcase(value):  # type: ignore
        return humps.decamelize(value).upper()  # type: ignore
    elif humps.is_pascalcase(value):  # type: ignore
        return humps.depascalize(value).upper()  # type: ignore
    else:
        return value.replace("-", "_").upper()


def generate_hash() -> str:
    account = get_account_id()
    region = get_region()
    concatenated_string = f"{account}-{region}"
    hash_value = (hashlib.sha1(concatenated_string.encode("UTF-8")).hexdigest())[:8]
    _logger.debug(f"HASH generated is {hash_value}")
    return hash_value
