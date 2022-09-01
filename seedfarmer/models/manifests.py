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
from typing import Any, Dict, List, Optional, Tuple, cast

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
    """

    name: str
    path: str
    bundle_md5: Optional[str]
    parameters: List[ModuleParameter] = []
    deploy_spec: Optional[DeploySpec] = None
    target_account: Optional[str] = None
    target_region: Optional[str] = None
    _target_account_id: Optional[str] = PrivateAttr(default=None)

    def set_target_account_id(self, account_id: str) -> None:
        self._target_account_id = account_id

    def get_target_account_id(self) -> Optional[str]:
        return self._target_account_id


class ModulesManifest(CamelModel):
    """
    ModulesManifest
    This is a group in the deployment and defines the name of the group,
    the path of the group definiton, and the modules that comprise the group
    """

    name: str
    path: Optional[str] = None
    modules: List[ModuleManifest] = []
    concurrency: Optional[int] = None


class RegionMapping(CamelModel):
    """
    RegionMapping
    This class provides metadata about the regions where Modules are deployed
    """

    region: str
    default: bool = False
    parameters_regional: Dict[str, str] = {}


class TargetAccountMapping(CamelModel):
    """
    TargetAccountMapping
    This class provides metadata about the accounts where Modules are deployed
    """

    alias: str
    account_id: str
    default: bool = False
    parameters_global: Dict[str, str] = {}
    region_mappings: List[RegionMapping] = []
    _default_region: Optional[RegionMapping] = PrivateAttr(default=None)
    _region_index: Dict[str, RegionMapping] = PrivateAttr(default_factory=dict)

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        for r in self.region_mappings:
            if r.default:
                self._default_region = r
            self._region_index[r.region] = r

    def get_region_mapping(self, region: str) -> Optional[RegionMapping]:
        return self._region_index.get(region, None)

    @property
    def default_region_mapping(self) -> Optional[RegionMapping]:
        return self._default_region


class DeploymentManifest(CamelModel):
    """
    DeploymentManifest
    This represents the top layer of the Deployment definiton.
    It includes things like the name of the deployment, the groups in the deployment
    and a policy that is applied to all build roles.
    """

    name: str
    toolchainRegion: str
    groups: List[ModulesManifest] = []
    description: Optional[str]
    target_account_mappings: List[TargetAccountMapping] = []
    _default_account: Optional[TargetAccountMapping] = PrivateAttr(default=None)
    _account_alias_index: Dict[str, TargetAccountMapping] = PrivateAttr(default_factory=dict)
    _account_id_index: Dict[str, TargetAccountMapping] = PrivateAttr(default_factory=dict)
    _accounts_regions: Optional[List[Dict[str, str]]] = PrivateAttr(default=None)
    _module_index: Dict[Tuple[str, str], ModuleManifest] = PrivateAttr(default_factory=dict)

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        for ta in self.target_account_mappings:
            if ta.default:
                self._default_account = ta
            self._account_alias_index[ta.alias] = ta
            self._account_id_index[ta.account_id] = ta

    def get_target_account_mapping(
        self, account_alias: Optional[str] = None, account_id: Optional[str] = None
    ) -> Optional[TargetAccountMapping]:
        if account_alias is None and account_id is None:
            raise ValueError("One of 'account_alias' or 'account_id' is required")
        elif account_alias is not None and account_id is not None:
            raise ValueError("Only one of 'account_alias' and 'account_id' is allowed")
        elif account_alias:
            return self._account_alias_index.get(account_alias, None)
        elif account_id:
            return self._account_id_index.get(account_id, None)
        else:
            return None

    @property
    def default_target_account_mapping(self) -> Optional[TargetAccountMapping]:
        return self._default_account

    @property
    def target_accounts_regions(self) -> List[Dict[str, str]]:
        if self._accounts_regions is None:
            self._accounts_regions = []
            for target_account in self.target_account_mappings:
                for region in target_account.region_mappings:
                    self._accounts_regions.append(
                        {
                            "alias": target_account.alias,
                            "account_id": target_account.account_id,
                            "region": region.region,
                        }
                    )
        return self._accounts_regions

    def get_parameter_value(
        self,
        parameter: str,
        *,
        account_alias: Optional[str] = None,
        account_id: Optional[str] = None,
        region: Optional[str] = None,
        default: Optional[str] = None,
    ) -> Optional[str]:
        if account_alias is not None and account_id is not None:
            raise ValueError("Only one of 'account_alias' and 'account_id' is allowed")

        use_default_account = account_alias is None and account_id is None
        use_default_region = region is None

        for target_account in self.target_account_mappings:
            if (
                account_alias == target_account.alias
                or account_id == target_account.account_id
                or (use_default_account and target_account.default)
            ):
                # Search the region_mappings for the region, if the parameter is in parameters_regional return it
                for region_mapping in target_account.region_mappings:
                    if (
                        region == region_mapping.region or (use_default_region and region_mapping.default)
                    ) and parameter in region_mapping.parameters_regional:
                        return region_mapping.parameters_regional[parameter]

                # If no region_mapping found for the region or no value for the parameter found in parameters_regional
                # return the value for parameter from parameters_global, default None
                return target_account.parameters_global.get(parameter, default)
        else:
            return default

    def validate_and_set_module_defaults(self) -> None:
        for group in self.groups:
            for module in group.modules:
                self._module_index[(group.name, module.name)] = module
                module.target_account = (
                    self.default_target_account_mapping.alias
                    if self.default_target_account_mapping is not None and module.target_account is None
                    else module.target_account
                )

                target_account = self.get_target_account_mapping(account_alias=module.target_account)
                if target_account is None:
                    raise ValueError(
                        f"Invalid target_account ({module.target_account}) for "
                        f"Module {module.name} in Group {group.name}"
                    )
                module.set_target_account_id(target_account.account_id)

                module.target_region = (
                    target_account.default_region_mapping.region
                    if target_account.default_region_mapping is not None and module.target_region is None
                    else module.target_region
                )

                if target_account.get_region_mapping(region=cast(str, module.target_region)) is None:
                    raise ValueError(
                        f"Invalid target_region ({module.target_region}) in target_account ({target_account.alias}) "
                        f"for Module {module.name} in Group {group.name}"
                    )

    def get_module(self, group: str, module: str) -> Optional[ModuleManifest]:
        return self._module_index.get((group, module), None)
