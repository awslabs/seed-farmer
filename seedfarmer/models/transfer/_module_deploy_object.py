from typing import Any, List, Optional, cast

from seedfarmer.models._base import CamelModel
from seedfarmer.models.manifests._deployment_manifest import DeploymentManifest
from seedfarmer.models.manifests._module_manifest import ModuleManifest, ModuleParameter


class ModuleDeployObject(CamelModel):
    deployment_manifest: DeploymentManifest
    group_name: str
    module_name: str
    parameters: Optional[List[ModuleParameter]] = None
    module_metadata: Optional[str] = None
    docker_credentials_secret: Optional[str] = None
    permissions_boundary_arn: Optional[str] = None
    module_role_name: Optional[str] = None
    codebuild_image: Optional[str] = None
    npm_mirror: Optional[str] = None
    npm_mirror_secret: Optional[str] = None
    pypi_mirror: Optional[str] = None
    pypi_mirror_secret: Optional[str] = None
    seedfarmer_bucket: Optional[str] = None

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        _module = cast(ModuleManifest, self.deployment_manifest.get_module(self.group_name, self.module_name))

        pba = self.deployment_manifest.get_permission_boundary_arn(
            target_account=cast(str, _module.get_target_account_id()),
            target_region=cast(str, _module.target_region),
        )
        codebuild_image = self.deployment_manifest.get_region_codebuild_image(
            account_alias=_module.target_account, region=_module.target_region
        )
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

        self.permissions_boundary_arn = pba if pba is not None else None
        self.codebuild_image = codebuild_image if codebuild_image is not None else None
        self.docker_credentials_secret = dcs if dcs else None
        self.npm_mirror = npm_mirror if npm_mirror is not None else None
        self.npm_mirror_secret = npm_mirror_secret if npm_mirror_secret is not None else None
        self.pypi_mirror = pypi_mirror if pypi_mirror is not None else None
        self.pypi_mirror_secret = pypi_mirror_secret if pypi_mirror_secret is not None else None
        self.seedfarmer_bucket = sf_bucket if sf_bucket is not None else None
