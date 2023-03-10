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

from typing import Optional, cast

import humps
from pydantic import BaseModel


def to_camel(string: str) -> str:
    return cast(str, humps.camelize(string))  # type: ignore


class CamelModel(BaseModel):
    class Config:
        alias_generator = to_camel
        allow_population_by_field_name = True
        underscore_attrs_are_private = True


class ModuleRef(CamelModel):
    name: str
    group: str
    key: Optional[str] = None


class ValueRef(CamelModel):
    module_metadata: Optional[ModuleRef] = None
    env_variable: Optional[str] = None
    parameter_store: Optional[str] = None
    secrets_manager: Optional[str] = None
    parameter_value: Optional[str] = None


class ValueFromRef(CamelModel):
    value_from: Optional[ValueRef] = None
