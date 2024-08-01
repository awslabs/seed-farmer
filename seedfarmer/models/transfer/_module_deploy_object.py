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
    pypi_mirror: Optional[str] = None
    pypi_mirror_secret: Optional[str] = None
    seedfarmer_bucket: Optional[str] = None

    def _render_permissions_boundary_arn(
        self, account_id: Optional[str], partition: Optional[str], permissions_boundary_name: Optional[str]
    ) -> Optional[str]:
        return (
            f"arn:{partition}:iam::{account_id}:policy/{permissions_boundary_name}"
            if permissions_boundary_name is not None
            else None
        )

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        _module = cast(ModuleManifest, self.deployment_manifest.get_module(self.group_name, self.module_name))

        pba = self._render_permissions_boundary_arn(
            account_id=str(_module.get_target_account_id()),
            partition=self.deployment_manifest._partition,
            permissions_boundary_name=self.deployment_manifest.get_parameter_value(
                "permissionsBoundaryName", account_alias=_module.target_account, region=_module.target_region
            ),
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

        pypi_mirror = self.deployment_manifest.get_region_pypi_mirror(
            account_alias=_module.target_account, region=_module.target_region
        )

        pypi_mirror_secret = self.deployment_manifest.get_region_pypi_mirror_secret(
            account_alias=_module.target_account, region=_module.target_region
        )

        sf_bucket = self.deployment_manifest.get_region_seedfarmer_bucket(
            account_alias=_module.target_account, region=_module.target_region
        )

        self.permissions_boundary_arn = pba if pba is not None else None
        self.codebuild_image = codebuild_image if codebuild_image is not None else None
        self.docker_credentials_secret = dcs if dcs else None
        self.npm_mirror = npm_mirror if npm_mirror is not None else None
        self.pypi_mirror = pypi_mirror if pypi_mirror is not None else None
        self.pypi_mirror_secret = pypi_mirror_secret if pypi_mirror_secret is not None else None
        self.seedfarmer_bucket = sf_bucket if sf_bucket is not None else None
