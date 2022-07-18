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

from enum import Enum
from typing import Any, Dict, Optional

from pydantic import PrivateAttr

from seedfarmer.models._base import CamelModel
from seedfarmer.utils import generate_codebuild_url


class StatusType(Enum):
    SUCCESS = "SUCCESS"
    ERROR = "ERROR"


class CodeSeederMetadata(CamelModel):

    _build_url: str = PrivateAttr()

    aws_account_id: Optional[str]
    aws_region: Optional[str]
    codebuild_build_id: Optional[str]
    codebuild_log_path: Optional[str]

    def __init__(self, **data: Any) -> None:
        super().__init__(**data)
        self._build_url = generate_codebuild_url(
            self.aws_account_id,  # type: ignore
            self.aws_region,  # type: ignore
            self.codebuild_build_id,  # type: ignore
        )

    @property
    def build_url(self) -> str:
        return self._build_url


class ModuleDeploymentResponse(CamelModel):

    deployment: str
    group: Optional[str]
    module: str
    status: str
    codeseeder_metadata: Optional[CodeSeederMetadata]
    codeseeder_output: Optional[Dict[Any, Any]]

    def __init__(self, **data: Any) -> None:
        super().__init__(**data)
        if data.get("status"):
            status_in = str(data["status"]).upper()
            self.status = status_in if status_in in StatusType.__members__.keys() else StatusType.SUCCESS.value
        else:
            self.build_type = StatusType.SUCCESS.value
