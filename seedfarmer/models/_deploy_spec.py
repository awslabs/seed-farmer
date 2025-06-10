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
from typing import Any, List, Optional

from seedfarmer.models._base import CamelModel


class BuildType(Enum):
    BUILD_GENERAL1_SMALL = "BUILD_GENERAL1_SMALL"
    BUILD_GENERAL1_MEDIUM = "BUILD_GENERAL1_MEDIUM"
    BUILD_GENERAL1_LARGE = "BUILD_GENERAL1_LARGE"
    BUILD_GENERAL1_2XLARGE = "BUILD_GENERAL1_2XLARGE"


class BuildPhase(CamelModel):
    """
    BuildPhase
    This is a list of strings that are passed to be executed
    in their respective phases as commands
    """

    commands: List[str] = []


class BuildPhases(CamelModel):
    """
    BuildPhases
    This object has the individual commands for each of the define build phases:
    install, pre_build,  build, post_build
    """

    install: BuildPhase = BuildPhase.model_construct()
    pre_build: BuildPhase = BuildPhase.model_construct()
    build: BuildPhase = BuildPhase.model_construct()
    post_build: BuildPhase = BuildPhase.model_construct()


class ExecutionType(CamelModel):
    """
    ExecutionType
    This an object that contains the Build Phases object for the destroy or deploy
    object of the DeploySpec
    """

    phases: BuildPhases = BuildPhases.model_construct()


class DeploySpec(CamelModel):
    """
    DeploySpec
    This represents the commands passed that will be executed
    on behalf of the module to be built.
    The deploy and the destroy objects each have an ExecutionType object.
    """

    deploy: Optional[ExecutionType] = None
    destroy: Optional[ExecutionType] = None
    build_type: Optional[str] = None
    publish_generic_env_variables: Optional[bool] = True

    def __init__(self, **data: Any) -> None:
        super().__init__(**data)
        if data.get("build_type"):
            chk = str(data["build_type"]).upper()
            self.build_type = chk if chk in BuildType.__members__.keys() else BuildType.BUILD_GENERAL1_SMALL.value
        else:
            self.build_type = BuildType.BUILD_GENERAL1_SMALL.value
