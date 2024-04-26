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
from pydantic import BaseModel, ConfigDict, model_validator

from seedfarmer.errors.seedfarmer_errors import InvalidManifestError


def to_camel(string: str) -> str:
    return cast(str, humps.camelize(string))  # type: ignore


class CamelModel(BaseModel):
    # TODO[pydantic]: The following keys were removed: `underscore_attrs_are_private`.
    # Check https://docs.pydantic.dev/dev-v2/migration/#changes-to-config for more information.
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True, extra="allow")

    @model_validator(mode="after")
    def check_for_extra_fields(self) -> "CamelModel":
        from seedfarmer import config

        if config.MANIFEST_VALIDATION_FAIL_ON_UNKNOWN_FIELDS and self.model_extra:
            raise InvalidManifestError(f"The following keys are not allowed: {self.model_extra}")

        return self


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
