from typing import Any, Dict, List, Optional, cast

import seedfarmer.errors
from seedfarmer.models._base import CamelModel
from seedfarmer.models.manifests._deployment_manifest import DeploymentManifest
from seedfarmer.models.manifests._module_manifest import ModuleManifest, ModuleParameter


class ModuleDeployObject(CamelModel):
    deployment_manifest: DeploymentManifest
    group_name: Optional[str] = None
    module_name: Optional[str] = None
    module_manifest: Optional[ModuleManifest] = None
    parameters: Optional[List[ModuleParameter]] = None
    module_metadata: Optional[str] = None
    docker_credentials_secret: Optional[str] = None
    permissions_boundary_arn: Optional[str] = None
    module_role_name: Optional[str] = None
    module_role_arn: Optional[str] = None
    codebuild_image: Optional[str] = None
    runtime_overrides: Optional[Dict[str, str]] = None
    npm_mirror: Optional[str] = None
    npm_mirror_secret: Optional[str] = None
    pypi_mirror: Optional[str] = None
    pypi_mirror_secret: Optional[str] = None
    seedfarmer_bucket: Optional[str] = None

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)

        if (
            (self.group_name and self.module_name and self.module_manifest)
            or ((self.group_name and not self.module_name) or (self.module_name and not self.group_name))
            or (not self.group_name and not self.module_name and not self.module_manifest)
        ):
            raise seedfarmer.errors.InvalidConfigurationError(
                "You must provide EITHER both 'group_name' and 'module_name', OR 'module_manifest'"
            )

        if self.group_name and self.module_name:
            _module = cast(ModuleManifest, self.deployment_manifest.get_module(self.group_name, self.module_name))

            pba = self.deployment_manifest.get_permission_boundary_arn(
                target_account=cast(str, _module.get_target_account_id()),
                target_region=cast(str, _module.target_region),
            )
            codebuild_image = self.deployment_manifest.get_region_codebuild_image(
                account_alias=_module.target_account, region=_module.target_region
            )
            region_runtime_overrides = self.deployment_manifest.get_region_runtime_overrides(
                account_alias=_module.target_account, region=_module.target_region
            )
            runtime_overrides = {
                **(region_runtime_overrides if region_runtime_overrides else {}),
                **(_module.runtime_overrides if _module.runtime_overrides else {}),
            }
            dcs = self.deployment_manifest.get_parameter_value(
                "dockerCredentialsSecret",
                account_alias=_module.target_account,
                region=_module.target_region,
            )
            npm_mirror = self.deployment_manifest.get_region_npm_mirror(
                account_alias=_module.target_account, region=_module.target_region
            )

            npm_mirror_secret = self.deployment_manifest.get_region_mirror_secret(
                account_alias=_module.target_account, region=_module.target_region, mirror_type="npm"
            )

            pypi_mirror = self.deployment_manifest.get_region_pypi_mirror(
                account_alias=_module.target_account, region=_module.target_region
            )

            pypi_mirror_secret = self.deployment_manifest.get_region_mirror_secret(
                account_alias=_module.target_account, region=_module.target_region, mirror_type="pypi"
            )

            sf_bucket = self.deployment_manifest.get_region_seedfarmer_bucket(
                account_alias=_module.target_account, region=_module.target_region
            )

            self.permissions_boundary_arn = pba
            self.codebuild_image = codebuild_image
            self.runtime_overrides = runtime_overrides
            self.docker_credentials_secret = dcs
            self.npm_mirror = npm_mirror
            self.npm_mirror_secret = npm_mirror_secret
            self.pypi_mirror = pypi_mirror
            self.pypi_mirror_secret = pypi_mirror_secret
            self.seedfarmer_bucket = sf_bucket

        elif self.module_manifest:
            # Placeholder for single modules
            pass
