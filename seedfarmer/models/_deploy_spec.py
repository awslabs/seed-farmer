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
    BUILD_LAMBDA_1GB = "BUILD_LAMBDA_1GB"
    BUILD_LAMBDA_2GB = "BUILD_LAMBDA_2GB"
    BUILD_LAMBDA_4GB = "BUILD_LAMBDA_4GB"
    BUILD_LAMBDA_8GB = "BUILD_LAMBDA_8GB"
    BUILD_LAMBDA_10GB = "BUILD_LAMBDA_10GB"


class EnvironmentType(Enum):
    ARM_CONTAINER = "ARM_CONTAINER"
    LINUX_CONTAINER = "LINUX_CONTAINER"
    LINUX_GPU_CONTAINER = "LINUX_GPU_CONTAINER"
    WINDOWS_SERVER_2019_CONTAINER = "WINDOWS_SERVER_2019_CONTAINER"
    ARM_LAMBDA_CONTAINER = "ARM_LAMBDA_CONTAINER"
    LINUX_LAMBDA_CONTAINER = "LINUX_LAMBDA_CONTAINER"


class BuildPhase(CamelModel):
    """
    BuildPhase
    This is a list of strings that are passed to CodeSeeder to be executed
    in their respective phases as commands
    """

    commands: List[str] = []


class BuildPhases(CamelModel):
    """
    BuildPhases
    This object has the individual commands for each of the define build phases:
    install, pre_build,  build, post_build
    """

    install: BuildPhase = BuildPhase()
    pre_build: BuildPhase = BuildPhase()
    build: BuildPhase = BuildPhase()
    post_build: BuildPhase = BuildPhase()


class ExecutionType(CamelModel):
    """
    ExecutionType
    This an object that contains the Build Phases object for the destroy or deploy
    object of the DeploySpec
    """

    phases: BuildPhases = BuildPhases()


class DeploySpec(CamelModel):
    """
    DeploySpec
    This represents the commands passed to CodeSeeder that will be executed
    on behalf of the module to be built.
    The deploy and the destroy objects each have an ExecutionType object.
    """

    deploy: Optional[ExecutionType] = None
    destroy: Optional[ExecutionType] = None
    build_type: Optional[str] = None
    environment_type: Optional[str] = None
    publish_generic_env_variables: Optional[bool] = False

    def __init__(self, **data: Any) -> None:
        super().__init__(**data)
        import logging

        _logger: logging.Logger = logging.getLogger(__name__)
        _logger.debug("LUCAS DEBUG")
        _logger.debug(data.keys())
        _logger.debug(data["environment_type"])
        if data.get("build_type"):
            chk = str(data["build_type"]).upper()
            self.build_type = chk if chk in BuildType.__members__.keys() else BuildType.BUILD_GENERAL1_SMALL.value
        else:
            self.build_type = BuildType.BUILD_GENERAL1_SMALL.value
        if data.get("environment_type"):
            chk = str(data["environment_type"]).upper()
            _logger.debug(f"LUCAS DEBUG: {chk}")
            _logger.debug(f"LUCAS DEBUG: {EnvironmentType.__members__.keys()}")
            self.environment_type = chk if chk in EnvironmentType.__members__.keys() else None
