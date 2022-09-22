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

import logging
from copy import deepcopy

import pytest
import yaml

from seedfarmer.models.manifests import DeploymentManifest, ModuleManifest

# Override _stack_commands OPS_ROOT to reflect path of resource policy needed for some testing #
# _sc.OPS_ROOT = os.path.join(_sc.OPS_ROOT, "test/unit-test/mock_data")

_logger: logging.Logger = logging.getLogger(__name__)


def pytest_configure(config):
    config.addinivalue_line("markers", "models")
    config.addinivalue_line("markers", "models_deployment_manifest")


deployment_yaml = yaml.safe_load(
    """
name: test
toolchainRegion: us-west-2
groups:
  - name: optionals
    path: manifests/test/optional-modules.yaml
targetAccountMappings:
  - alias: primary
    accountId: "000000000000"
    default: true
    parametersGlobal:
      permissionsBoundaryName: policyName
      dockerCredentialsSecret: secret
    regionMappings:
      - region: us-west-2
        default: true
        parametersRegional:
          someKey: someValue
"""
)


@pytest.mark.models
@pytest.mark.models_deployment_manifest
def test_deserialize_deployment_manifest():
    manifest = DeploymentManifest(**deployment_yaml)
    assert manifest.name == "test"


@pytest.mark.models
@pytest.mark.models_deployment_manifest
def test_deployment_manifest_get_parameter_with_defaults():
    manifest = DeploymentManifest(**deployment_yaml)

    assert manifest.get_parameter_value("someKey", account_alias="primary", region="us-west-2") == "someValue"
    assert manifest.get_parameter_value("someKey", account_id="000000000000", region="us-west-2") == "someValue"
    assert (
        manifest.get_parameter_value("dockerCredentialsSecret", account_alias="primary", region="us-west-2") == "secret"
    )
    assert manifest.get_parameter_value("dockerCredentialsSecret") == "secret"
    assert manifest.get_parameter_value("noKey") is None
    assert manifest.get_parameter_value("noKey", default="noValue") == "noValue"
    with pytest.raises(ValueError):
        manifest.get_parameter_value("someKey", account_alias="primary", account_id="000000000000", region="us-west-2")

    assert manifest.get_target_account_mapping(account_alias="primary").alias == "primary"
    assert manifest.get_target_account_mapping(account_id="000000000000").alias == "primary"
    assert manifest.get_target_account_mapping(account_alias="other") is None
    assert manifest.get_target_account_mapping(account_id="other") is None
    assert manifest.default_target_account_mapping.alias == "primary"

    assert manifest.target_account_mappings[0].get_region_mapping(region="us-west-2").region == "us-west-2"
    assert manifest.target_account_mappings[0].get_region_mapping(region="other") is None
    assert manifest.target_account_mappings[0].default_region_mapping.region == "us-west-2"

    with pytest.raises(ValueError):
        manifest.get_target_account_mapping(account_alias="primary", account_id="000000000000")
    with pytest.raises(ValueError):
        manifest.get_target_account_mapping()


@pytest.mark.models
@pytest.mark.models_deployment_manifest
def test_deployment_manifest_get_parameter_without_defaults():
    # Clear targetAccountMapping and regionMapping defaults
    updated_deployment_yaml = deepcopy(deployment_yaml)
    updated_deployment_yaml["targetAccountMappings"][0]["default"] = False
    updated_deployment_yaml["targetAccountMappings"][0]["regionMappings"][0]["default"] = False
    manifest = DeploymentManifest(**updated_deployment_yaml)

    assert manifest.get_parameter_value("dockerCredentialsSecret") is None
    assert manifest.default_target_account_mapping is None
    assert manifest.target_account_mappings[0].default_region_mapping is None


@pytest.mark.models
@pytest.mark.models_module_manifest
def test_module_manifest_with_defaults():
    manifest = DeploymentManifest(**deployment_yaml)

    module_yaml = yaml.safe_load(
        """
name: test-module-1
path: modules/test-module
targetAccount: primary
targetRegion: us-west-2
"""
    )

    module = ModuleManifest(**module_yaml)
    manifest.groups[0].modules = [module]
    manifest.validate_and_set_module_defaults()

    assert module.target_account == "primary"
    assert module.target_region == "us-west-2"

    module_yaml = yaml.safe_load(
        """
name: test-module-1
path: modules/test-module
"""
    )

    module = ModuleManifest(**module_yaml)
    manifest.groups[0].modules = [module]
    manifest.validate_and_set_module_defaults()

    assert module.target_account == "primary"
    assert module.target_region == "us-west-2"

    module_yaml = yaml.safe_load(
        """
name: test-module-1
path: modules/test-module
targetAccount: other
targetRegion: us-west-2
"""
    )

    module = ModuleManifest(**module_yaml)
    manifest.groups[0].modules = [module]
    with pytest.raises(ValueError):
        manifest.validate_and_set_module_defaults()

    module_yaml = yaml.safe_load(
        """
name: test-module-1
path: modules/test-module
targetAccount: primary
targetRegion: other
"""
    )

    module = ModuleManifest(**module_yaml)
    manifest.groups[0].modules = [module]
    with pytest.raises(ValueError):
        manifest.validate_and_set_module_defaults()


@pytest.mark.models
@pytest.mark.models_module_manifest
def test_module_manifest_without_defaults():
    # Clear targetAccountMapping and regionMapping defaults
    updated_deployment_yaml = deepcopy(deployment_yaml)
    updated_deployment_yaml["targetAccountMappings"][0]["default"] = False
    updated_deployment_yaml["targetAccountMappings"][0]["regionMappings"][0]["default"] = False
    manifest = DeploymentManifest(**updated_deployment_yaml)

    module_yaml = yaml.safe_load(
        """
name: test-module-1
path: modules/test-module
targetAccount: primary
targetRegion: us-west-2
"""
    )

    module = ModuleManifest(**module_yaml)
    manifest.groups[0].modules = [module]
    manifest.validate_and_set_module_defaults()

    assert module.target_account == "primary"
    assert module.target_region == "us-west-2"

    module_yaml = yaml.safe_load(
        """
name: test-module-1
path: modules/test-module
targetAccount: primary
"""
    )

    module = ModuleManifest(**module_yaml)
    manifest.groups[0].modules = [module]

    with pytest.raises(ValueError):
        manifest.validate_and_set_module_defaults()

    module_yaml = yaml.safe_load(
        """
name: test-module-1
path: modules/test-module
targetRegion: us-west-2
"""
    )

    module = ModuleManifest(**module_yaml)
    manifest.groups[0].modules = [module]

    with pytest.raises(ValueError):
        manifest.validate_and_set_module_defaults()
