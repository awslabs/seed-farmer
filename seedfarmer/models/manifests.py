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

from pydantic import PrivateAttr

from seedfarmer.models._base import CamelModel
from seedfarmer.utils import upper_snake_case


class BuildType(Enum):
    BUILD_GENERAL1_SMALL = "BUILD_GENERAL1_SMALL"
    BUILD_GENERAL1_MEDIUM = "BUILD_GENERAL1_MEDIUM"
    BUILD_GENERAL1_LARGE = "BUILD_GENERAL1_LARGE"
    BUILD_GENERAL1_2XLARGE = "BUILD_GENERAL1_2XLARGE"


class BuildPhase(CamelModel):
    """
    BuildPhase
    This is a list of strings that are passed to CodeSeeder to be executed
    in their respective phases as commands
    """ """"""

    commands: List[str] = []


class BuildPhases(CamelModel):
    """
    BuildPhases
    This object has the individual commands for each of the define build phases:
    install, pre_build,  build, post_build
    """ """"""

    install: BuildPhase = BuildPhase()
    pre_build: BuildPhase = BuildPhase()
    build: BuildPhase = BuildPhase()
    post_build: BuildPhase = BuildPhase()


class ExecutionType(CamelModel):
    """
    ExecutionType
    This an object that contains the Build Phases object for the destroy or deploy
    object of the DeploySpec
    """ """"""

    phases: BuildPhases = BuildPhases()


class DeploySpec(CamelModel):
    """
    DeploySpec
    This represents the commands passed to CodeSeeder that will be executed
    on behalf of the module to be built.
    The deploy and the destroy objects each have an ExecutionType object.
    """ """"""

    deploy: Optional[ExecutionType] = None
    destroy: Optional[ExecutionType] = None
    build_type: Optional[str] = None

    def __init__(self, **data: Any) -> None:
        super().__init__(**data)
        if data.get("build_type"):
            chk = str(data["build_type"]).upper()
            self.build_type = chk if chk in BuildType.__members__.keys() else BuildType.BUILD_GENERAL1_SMALL.value
        else:
            self.build_type = BuildType.BUILD_GENERAL1_SMALL.value


class ModuleRef(CamelModel):
    name: str
    group: str
    key: Optional[str] = None


class ValueRef(CamelModel):
    module_metadata: Optional[ModuleRef] = None


class ModuleParameter(CamelModel):
    _upper_snake_case: str = PrivateAttr()

    name: str
    value: Optional[Any] = None
    value_from: Optional[ValueRef] = None

    def __init__(self, **data: Any) -> None:
        super().__init__(**data)
        self._upper_snake_case = upper_snake_case(self.name)

    @property
    def upper_snake_case(self) -> str:
        return self._upper_snake_case


class ModuleManifest(CamelModel):
    """
    ModuleManifest
    This is a module in a group of the deployment and consists of a name,
    the path of the module manifest, any ModuleParameters for deployment, and
    the DeploySpec.
    """ """"""

    name: str
    path: str
    bundle_md5: Optional[str]
    parameters: List[ModuleParameter] = []
    deploy_spec: Optional[DeploySpec]


class ModulesManifest(CamelModel):
    """
    ModulesManifest
    This is a group in the deployment and defines the name of the group,
    the path of the group definiton, and the modules that comprise the group
    """ """"""

    name: str
    path: Optional[str] = None
    modules: List[ModuleManifest] = []
    concurrency: Optional[int] = None


class DeploymentManifest(CamelModel):
    """
    DeploymentManifest
    This represents the top layer of the Deployment definiton.
    It includes things like the name of the deployment, the groups in the deployment
    and a policy that is applied to all build roles.
    """ """"""

    name: str
    groups: List[ModulesManifest] = []
    project_policy: Optional[str]
    description: Optional[str]
    docker_credentials_secret: Optional[str]
    permission_boundary_arn: Optional[str]
