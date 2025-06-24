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

import os
from typing import Any, Dict, List, Optional, Tuple, Union, cast

from pydantic import PrivateAttr

import seedfarmer.errors
from seedfarmer.models._base import CamelModel, ValueFromRef
from seedfarmer.models.manifests._module_manifest import ModuleManifest


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


class NetworkMapping(CamelModel):
    """
    NetworkMapping
    This class provides network metadata
    """

    vpc_id: Optional[Union[str, ValueFromRef]] = None
    private_subnet_ids: Optional[Union[List[str], ValueFromRef]] = None
    security_group_ids: Optional[Union[List[str], ValueFromRef]] = None


class RegionMapping(CamelModel):
    """
    RegionMapping
    This class provides metadata about the regions where Modules are deployed
    """

    region: str
    default: bool = False
    parameters_regional: Dict[str, Any] = {}
    network: Optional[NetworkMapping] = None
    codebuild_image: Optional[str] = None
    runtime_overrides: Optional[Dict[str, str]] = None
    npm_mirror: Optional[str] = None
    pypi_mirror: Optional[str] = None
    pypi_mirror_secret: Optional[str] = None
    npm_mirror_secret: Optional[str] = None
    seedkit_metadata: Optional[Dict[str, Any]] = None
    seedfarmer_artifact_bucket: Optional[str] = None
    role_prefix: Optional[str] = None
    policy_prefix: Optional[str] = None


class TargetAccountMapping(CamelModel):
    """
    TargetAccountMapping
    This class provides metadata about the accounts where Modules are deployed
    """

    alias: str
    account_id: Union[int, str, ValueFromRef]
    default: bool = False
    parameters_global: Dict[str, str] = {}
    region_mappings: List[RegionMapping] = []
    codebuild_image: Optional[str] = None
    runtime_overrides: Optional[Dict[str, str]] = None
    npm_mirror: Optional[str] = None
    npm_mirror_secret: Optional[str] = None
    pypi_mirror: Optional[str] = None
    pypi_mirror_secret: Optional[str] = None
    _default_region: Optional[RegionMapping] = PrivateAttr(default=None)
    _region_index: Dict[str, RegionMapping] = PrivateAttr(default_factory=dict)
    role_prefix: Optional[str] = None
    policy_prefix: Optional[str] = None

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        for r in self.region_mappings:
            if r.default:
                self._default_region = r
            self._region_index[r.region] = r

    def get_region_mapping(self, region: str) -> Optional[RegionMapping]:
        return self._region_index.get(region, None)

    @property
    def actual_account_id(self) -> str:
        if isinstance(self.account_id, str) or isinstance(self.account_id, int):
            return str(self.account_id)
        elif isinstance(self.account_id, ValueFromRef):
            if self.account_id.value_from and self.account_id.value_from.module_metadata is not None:
                raise seedfarmer.errors.InvalidManifestError(
                    "Loading value from Module Metadata is not supported in the Deployment Manifest"
                )
            elif self.account_id.value_from and self.account_id.value_from.env_variable:
                account_id = os.getenv(self.account_id.value_from.env_variable, None)
                if account_id is None:
                    raise seedfarmer.errors.InvalidManifestError(
                        (
                            "Unable to resolve AccountId from Environment Variable:"
                            f" {self.account_id.value_from.env_variable}"
                        )
                    )
                return account_id
            else:
                raise seedfarmer.errors.InvalidManifestError("Unsupported valueFrom type")
        else:
            raise seedfarmer.errors.InvalidManifestError("Unsupported accountId type")

    @property
    def default_region_mapping(self) -> Optional[RegionMapping]:
        return self._default_region


class NameGenerator(CamelModel):
    """
    NameGenerator
    This class decrbites how to dynamically generate the name of a DeploymentManifest
    """

    prefix: Union[str, ValueFromRef]
    suffix: Union[str, ValueFromRef]

    def _get_value(self, value: Union[str, ValueFromRef]) -> str:  # type: ignore[override]
        if isinstance(value, str):
            return value
        elif isinstance(value, ValueFromRef):
            if value.value_from and value.value_from.module_metadata is not None:
                raise seedfarmer.errors.InvalidManifestError(
                    "Loading value from Module Metadata is not supported on a NameGenerator"
                )
            elif value.value_from and value.value_from.env_variable:
                env_value = os.getenv(value.value_from.env_variable, None)
                if env_value is None:
                    raise seedfarmer.errors.InvalidManifestError(
                        (f"Unable to resolve value from Environment Variable: {value.value_from.env_variable}")
                    )
                return env_value
            else:
                raise seedfarmer.errors.InvalidManifestError("Unsupported valueFrom type")
        else:
            raise seedfarmer.errors.InvalidManifestError("Unsupported value type")

    def generate_name(self) -> str:
        prefix = self._get_value(self.prefix)
        suffix = self._get_value(self.suffix)

        return f"{prefix}{suffix}"


class DeploymentManifest(CamelModel):
    """
    DeploymentManifest
    This represents the top layer of the Deployment definiton.
    It includes things like the name of the deployment, the groups in the deployment
    and a policy that is applied to all build roles.
    """

    name: Optional[str] = None
    name_generator: Optional[NameGenerator] = None
    toolchain_region: str
    groups: List[ModulesManifest] = []
    description: Optional[str] = None
    target_account_mappings: List[TargetAccountMapping] = []
    force_dependency_redeploy: Optional[bool] = False
    archive_secret: Optional[str] = None
    _default_account: Optional[TargetAccountMapping] = PrivateAttr(default=None)
    _account_alias_index: Dict[str, TargetAccountMapping] = PrivateAttr(default_factory=dict)
    _account_id_index: Dict[str, TargetAccountMapping] = PrivateAttr(default_factory=dict)
    _accounts_regions: Optional[List[Dict[str, str]]] = PrivateAttr(default=None)
    _module_index: Dict[Tuple[str, str], ModuleManifest] = PrivateAttr(default_factory=dict)
    _partition: Optional[str] = PrivateAttr(default="aws")

    def __init__(self, **kwargs: Any) -> None:
        from seedfarmer.utils import batch_replace_env

        kwargs = batch_replace_env(payload=kwargs)
        super().__init__(**kwargs)

        if self.name is None and self.name_generator is None:
            raise seedfarmer.errors.InvalidManifestError("One of 'name' or 'name_generator' is required")

        if self.name is not None and self.name_generator is not None:
            raise seedfarmer.errors.InvalidManifestError("Only one of 'name' or 'name_generator' can be specified")

        # Generate a name and then reset the name_generator to None so that any SerDe done later on does not
        # generate a new name
        if self.name_generator is not None:
            self.name = self.name_generator.generate_name()
            self.name_generator = None

        for ta in self.target_account_mappings:
            if ta.default:
                self._default_account = ta
            self._account_alias_index[ta.alias] = ta
            self._account_id_index[ta.actual_account_id] = ta

    def get_target_account_mapping(
        self, account_alias: Optional[str] = None, account_id: Optional[str] = None
    ) -> Optional[TargetAccountMapping]:
        if account_alias is None and account_id is None:
            raise seedfarmer.errors.InvalidManifestError("One of 'account_alias' or 'account_id' is required")
        elif account_alias is not None and account_id is not None:
            raise seedfarmer.errors.InvalidManifestError("Only one of 'account_alias' and 'account_id' is allowed")
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
                    role_prefix = region.role_prefix if region.role_prefix else target_account.role_prefix
                    policy_prefix = region.policy_prefix if region.policy_prefix else target_account.policy_prefix
                    account_region_args = {
                        "alias": target_account.alias,
                        "account_id": target_account.actual_account_id,
                        "region": region.region,
                        "network": region.network,
                        "parameters_regional": region.parameters_regional,
                        "codebuild_image": cast(str, region.codebuild_image),
                        "role_prefix": role_prefix,
                        "policy_prefix": policy_prefix,
                    }
                    self._accounts_regions.append(account_region_args)  # type: ignore
        return self._accounts_regions

    def get_parameter_value(
        self,
        parameter: str,
        *,
        account_alias: Optional[str] = None,
        account_id: Optional[str] = None,
        region: Optional[str] = None,
        default: Optional[str] = None,
    ) -> Optional[Any]:
        if account_alias is not None and account_id is not None:
            raise seedfarmer.errors.InvalidManifestError("Only one of 'account_alias' and 'account_id' is allowed")

        use_default_account = account_alias is None and account_id is None
        use_default_region = region is None

        for target_account in self.target_account_mappings:
            if (
                account_alias == target_account.alias
                or account_id == target_account.actual_account_id
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

    def get_region_codebuild_image(
        self,
        *,
        account_alias: Optional[str] = None,
        account_id: Optional[str] = None,
        region: Optional[str] = None,
    ) -> Optional[str]:
        if account_alias is not None and account_id is not None:
            raise seedfarmer.errors.InvalidManifestError("Only one of 'account_alias' and 'account_id' is allowed")

        use_default_account = account_alias is None and account_id is None
        use_default_region = region is None

        for target_account in self.target_account_mappings:
            if (
                account_alias == target_account.alias
                or account_id == target_account.actual_account_id
                or (use_default_account and target_account.default)
            ):
                # Search the region_mappings for the region, if the codebuild_image is in region
                for region_mapping in target_account.region_mappings:
                    if region == region_mapping.region or (use_default_region and region_mapping.default):
                        image = (
                            region_mapping.codebuild_image
                            if region_mapping.codebuild_image is not None
                            else target_account.codebuild_image
                        )
                        if (
                            image is None
                            and region_mapping.seedkit_metadata
                            and region_mapping.seedkit_metadata.get("CodeBuildProjectBuildImage")
                        ):
                            image = region_mapping.seedkit_metadata["CodeBuildProjectBuildImage"]

                        return image
        else:
            return None

    def get_region_runtime_overrides(
        self,
        *,
        account_alias: Optional[str] = None,
        account_id: Optional[str] = None,
        region: Optional[str] = None,
    ) -> Optional[Dict[str, str]]:
        if account_alias is not None and account_id is not None:
            raise seedfarmer.errors.InvalidManifestError("Only one of 'account_alias' and 'account_id' is allowed")

        use_default_account = account_alias is None and account_id is None
        use_default_region = region is None

        for target_account in self.target_account_mappings:
            if (
                account_alias == target_account.alias
                or account_id == target_account.actual_account_id
                or (use_default_account and target_account.default)
            ):
                # Search the region_mappings for the region, if the codebuild_image is in region
                for region_mapping in target_account.region_mappings:
                    if region == region_mapping.region or (use_default_region and region_mapping.default):
                        region_overrides = region_mapping.runtime_overrides if region_mapping.runtime_overrides else {}
                        account_overrides = target_account.runtime_overrides if target_account.runtime_overrides else {}
                        return {**account_overrides, **region_overrides}
        else:
            return None

    def get_region_npm_mirror(
        self,
        *,
        account_alias: Optional[str] = None,
        account_id: Optional[str] = None,
        region: Optional[str] = None,
    ) -> Optional[str]:
        if account_alias is not None and account_id is not None:
            raise seedfarmer.errors.InvalidManifestError("Only one of 'account_alias' and 'account_id' is allowed")

        use_default_account = account_alias is None and account_id is None
        use_default_region = region is None
        for target_account in self.target_account_mappings:
            if (
                account_alias == target_account.alias
                or account_id == target_account.actual_account_id
                or (use_default_account and target_account.default)
            ):
                # Search the region_mappings for the region, if the npm_mirror is in region
                for region_mapping in target_account.region_mappings:
                    if region == region_mapping.region or (use_default_region and region_mapping.default):
                        npm_mirror = (
                            region_mapping.npm_mirror
                            if region_mapping.npm_mirror is not None
                            else target_account.npm_mirror
                        )
                        return npm_mirror
        else:
            return None

    def get_region_pypi_mirror(
        self,
        *,
        account_alias: Optional[str] = None,
        account_id: Optional[str] = None,
        region: Optional[str] = None,
    ) -> Optional[str]:
        if account_alias is not None and account_id is not None:
            raise seedfarmer.errors.InvalidManifestError("Only one of 'account_alias' and 'account_id' is allowed")

        use_default_account = account_alias is None and account_id is None
        use_default_region = region is None
        for target_account in self.target_account_mappings:
            if (
                account_alias == target_account.alias
                or account_id == target_account.actual_account_id
                or (use_default_account and target_account.default)
            ):
                # Search the region_mappings for the region, if the pypi_mirror is in region
                for region_mapping in target_account.region_mappings:
                    if region == region_mapping.region or (use_default_region and region_mapping.default):
                        pypi_mirror = (
                            region_mapping.pypi_mirror
                            if region_mapping.pypi_mirror is not None
                            else target_account.pypi_mirror
                        )
                        return pypi_mirror
        else:
            return None

    def get_region_mirror_secret(
        self,
        *,
        mirror_type: Optional[str] = "pypi",
        account_alias: Optional[str] = None,
        account_id: Optional[str] = None,
        region: Optional[str] = None,
    ) -> Optional[str]:
        if account_alias is not None and account_id is not None:
            raise seedfarmer.errors.InvalidManifestError("Only one of 'account_alias' and 'account_id' is allowed")

        if mirror_type not in ["pypi", "npm"]:
            raise seedfarmer.errors.InvalidManifestError("Mirror type must be of type 'npm' or 'pypi'")

        use_default_account = account_alias is None and account_id is None
        use_default_region = region is None
        for target_account in self.target_account_mappings:
            if (
                account_alias == target_account.alias
                or account_id == target_account.actual_account_id
                or (use_default_account and target_account.default)
            ):
                # Search the region_mappings for the region, if the [pypi|npm]_mirror_secret is in region
                for region_mapping in target_account.region_mappings:
                    if region == region_mapping.region or (use_default_region and region_mapping.default):
                        if mirror_type == "pypi":
                            pypi_mirror_secret = (
                                region_mapping.pypi_mirror_secret
                                if region_mapping.pypi_mirror_secret is not None
                                else target_account.pypi_mirror_secret
                            )
                            return pypi_mirror_secret
                        elif mirror_type == "npm":
                            npm_mirror_secret = (
                                region_mapping.npm_mirror_secret
                                if region_mapping.npm_mirror_secret is not None
                                else target_account.npm_mirror_secret
                            )
                            return npm_mirror_secret
        else:
            return None

    def get_region_seedfarmer_bucket(
        self,
        *,
        account_alias: Optional[str] = None,
        account_id: Optional[str] = None,
        region: Optional[str] = None,
    ) -> Optional[str]:
        if account_alias is not None and account_id is not None:
            raise seedfarmer.errors.InvalidManifestError("Only one of 'account_alias' and 'account_id' is allowed")

        use_default_account = account_alias is None and account_id is None
        use_default_region = region is None
        for target_account in self.target_account_mappings:
            if (
                account_alias == target_account.alias
                or account_id == target_account.actual_account_id
                or (use_default_account and target_account.default)
            ):
                for region_mapping in target_account.region_mappings:
                    if region == region_mapping.region or (use_default_region and region_mapping.default):
                        sf_bucket = (
                            region_mapping.seedfarmer_artifact_bucket
                            if region_mapping.seedfarmer_artifact_bucket is not None
                            else None
                        )
                        return sf_bucket
        else:
            return None

    def get_region_seedfarmer_metadata(
        self,
        *,
        account_alias: Optional[str] = None,
        account_id: Optional[str] = None,
        region: Optional[str] = None,
    ) -> Optional[Dict[str, str]]:
        if account_alias is not None and account_id is not None:
            raise seedfarmer.errors.InvalidManifestError("Only one of 'account_alias' and 'account_id' is allowed")

        use_default_account = account_alias is None and account_id is None
        use_default_region = region is None
        for target_account in self.target_account_mappings:
            if (
                account_alias == target_account.alias
                or account_id == target_account.actual_account_id
                or (use_default_account and target_account.default)
            ):
                for region_mapping in target_account.region_mappings:
                    if region == region_mapping.region or (use_default_region and region_mapping.default):
                        return region_mapping.seedkit_metadata if region_mapping.seedkit_metadata else None
        else:
            return None

    def get_account_region_role_prefix(
        self,
        *,
        account_alias: Optional[str] = None,
        account_id: Optional[str] = None,
        region: Optional[str] = None,
    ) -> str:
        if account_alias is not None and account_id is not None:
            raise seedfarmer.errors.InvalidManifestError("Only one of 'account_alias' and 'account_id' is allowed")

        use_default_account = account_alias is None and account_id is None
        use_default_region = region is None
        default_prefix = "/"
        for target_account in self.target_account_mappings:
            if (
                account_alias == target_account.alias
                or account_id == target_account.actual_account_id
                or (use_default_account and target_account.default)
            ):
                for region_mapping in target_account.region_mappings:
                    if region == region_mapping.region or (use_default_region and region_mapping.default):
                        role_prefix = (
                            region_mapping.role_prefix
                            if region_mapping.role_prefix is not None
                            else target_account.role_prefix
                        )
                        return role_prefix if role_prefix else default_prefix
        else:
            return default_prefix

    def get_permission_boundary_arn(self, target_account: str, target_region: str) -> Optional[str]:
        permissions_boundary_name = self.get_parameter_value(
            "permissionsBoundaryName",
            account_id=target_account,
            region=target_region,
        )
        return (
            f"arn:{self._partition}:iam::{target_account}:policy/{permissions_boundary_name}"
            if permissions_boundary_name is not None
            else None
        )

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
                    raise seedfarmer.errors.InvalidManifestError(
                        f"Invalid target_account ({module.target_account}) for "
                        f"Module {module.name} in Group {group.name}"
                    )
                module.set_target_account_id(target_account.actual_account_id)

                module.target_region = (
                    target_account.default_region_mapping.region
                    if target_account.default_region_mapping is not None and module.target_region is None
                    else module.target_region
                )

                if target_account.get_region_mapping(region=cast(str, module.target_region)) is None:
                    raise seedfarmer.errors.InvalidManifestError(
                        f"Invalid target_region ({module.target_region}) in target_account ({target_account.alias}) "
                        f"for Module {module.name} in Group {group.name}"
                    )

    def get_module(self, group: str, module: str) -> Optional[ModuleManifest]:
        return self._module_index.get((group, module), None)

    def populate_metadata(self, account_id: str, region: str, seedkit_dict: Dict[str, Any]) -> None:
        for target_account in self.target_account_mappings:
            for region_mapping in target_account.region_mappings:
                if target_account.actual_account_id == account_id and region_mapping.region == region:
                    region_mapping.seedkit_metadata = seedkit_dict
                    region_mapping.seedfarmer_artifact_bucket = (
                        seedkit_dict.get("SeedfarmerArtifactBucket")
                        if seedkit_dict.get("SeedfarmerArtifactBucket")
                        else None
                    )
                    break
