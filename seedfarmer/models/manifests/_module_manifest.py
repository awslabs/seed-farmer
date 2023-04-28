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

from typing import Any, List, Optional

from pydantic import PrivateAttr

from seedfarmer.models._base import CamelModel, ValueFromRef
from seedfarmer.models._deploy_spec import DeploySpec
from seedfarmer.utils import upper_snake_case


class ModuleParameter(ValueFromRef):
    _upper_snake_case: str = PrivateAttr()

    name: str
    value: Optional[Any] = None
    version: Optional[Any] = None

    def __init__(self, **data: Any) -> None:
        super().__init__(**data)
        self._upper_snake_case = upper_snake_case(self.name)

    @property
    def upper_snake_case(self) -> str:
        return self._upper_snake_case


class DataFile(CamelModel):
    file_path: str
    _local_file_path: Optional[str] = PrivateAttr(default=None)
    _bundle_path: Optional[str] = PrivateAttr(default=None)

    def __init__(self, **data: Any) -> None:
        super().__init__(**data)
        self._local_file_path = "."
        self._bundle_path = self.file_path

    def set_local_file_path(self, _local_file_path: str) -> None:
        self._local_file_path = _local_file_path

    def get_local_file_path(self) -> Optional[str]:
        return self._local_file_path

    def set_bundle_path(self, bundle_path: str) -> None:
        self._bundle_path = bundle_path

    def get_bundle_path(self) -> Optional[str]:
        return self._bundle_path


class ModuleManifest(CamelModel):
    """
    ModuleManifest
    This is a module in a group of the deployment and consists of a name,
    the path of the module manifest, any ModuleParameters for deployment, and
    the DeploySpec.
    """

    name: str
    path: str
    bundle_md5: Optional[str]
    manifest_md5: Optional[str]
    deployspec_md5: Optional[str]
    parameters: List[ModuleParameter] = []
    deploy_spec: Optional[DeploySpec] = None
    target_account: Optional[str] = None
    target_region: Optional[str] = None
    codebuild_image: Optional[str] = None
    data_files: Optional[List[DataFile]] = None
    _target_account_id: Optional[str] = PrivateAttr(default=None)
    _local_path: Optional[str] = PrivateAttr(default=None)

    def __init__(self, **data: Any) -> None:
        super().__init__(**data)
        self._local_path = self.path

    def set_target_account_id(self, account_id: str) -> None:
        self._target_account_id = account_id

    def get_target_account_id(self) -> Optional[str]:
        return self._target_account_id

    def set_local_path(self, local_path: str) -> None:
        self._local_path = local_path

    def get_local_path(self) -> Optional[str]:
        return self._local_path
