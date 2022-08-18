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

import pytest
import yaml

from seedfarmer.models.manifests import DeploymentManifest

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
      permissionBoundaryArn: arn
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
def test_get_parameter_with_defaults():
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
        manifest.get_parameter_value(
            "someKey", account_alias="primary", account_id="000000000000", region="us-west-2"
        ) == "someValue"


@pytest.mark.models
@pytest.mark.models_deployment_manifest
def test_get_parameter_without_defaults():
    manifest = DeploymentManifest(**deployment_yaml)
    # Clear targetAccountMapping and regionMapping defaults
    manifest.target_account_mappings[0].default = False
    manifest.target_account_mappings[0].region_mappings[0].default = False

    assert manifest.get_parameter_value("someKey", account_alias="primary", region="us-west-2") == "someValue"
    assert manifest.get_parameter_value("someKey", account_id="000000000000", region="us-west-2") == "someValue"
    assert (
        manifest.get_parameter_value("dockerCredentialsSecret", account_alias="primary", region="us-west-2") == "secret"
    )
    assert manifest.get_parameter_value("dockerCredentialsSecret") is None
    assert manifest.get_parameter_value("noKey") is None
    assert manifest.get_parameter_value("noKey", default="noValue") == "noValue"
    with pytest.raises(ValueError):
        manifest.get_parameter_value(
            "someKey", account_alias="primary", account_id="000000000000", region="us-west-2"
        ) == "someValue"
