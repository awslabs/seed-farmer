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
import os
from copy import deepcopy

from unittest import mock
import pytest
import yaml

import seedfarmer.errors
from seedfarmer.models.deploy_responses import CodeSeederMetadata
from seedfarmer.models.manifests import DeploymentManifest, ModuleManifest
from seedfarmer.errors import InvalidManifestError
from seedfarmer.models.manifests._module_manifest import DeploySpec

# Override _stack_commands OPS_ROOT to reflect path of resource policy needed for some testing #
# _sc.OPS_ROOT = os.path.join(_sc.OPS_ROOT, "test/unit-test/mock_data")

_logger: logging.Logger = logging.getLogger(__name__)


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
    with pytest.raises(seedfarmer.errors.InvalidManifestError):
        manifest.get_parameter_value("someKey", account_alias="primary", account_id="000000000000", region="us-west-2")

    assert manifest.get_target_account_mapping(account_alias="primary").alias == "primary"
    assert manifest.get_target_account_mapping(account_id="000000000000").alias == "primary"
    assert manifest.get_target_account_mapping(account_alias="other") is None
    assert manifest.get_target_account_mapping(account_id="other") is None
    assert manifest.default_target_account_mapping.alias == "primary"

    assert manifest.target_account_mappings[0].get_region_mapping(region="us-west-2").region == "us-west-2"
    assert manifest.target_account_mappings[0].get_region_mapping(region="other") is None
    assert manifest.target_account_mappings[0].default_region_mapping.region == "us-west-2"

    with pytest.raises(seedfarmer.errors.InvalidManifestError):
        manifest.get_target_account_mapping(account_alias="primary", account_id="000000000000")
    with pytest.raises(seedfarmer.errors.InvalidManifestError):
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
@pytest.mark.models_deployment_manifest
def test_deployment_manifest_name_generator():
    os.environ.setdefault("PYTEST_MODEL_USER", "TESTUSER")

    generator_yaml = yaml.safe_load(
        """
nameGenerator:
  prefix: test-
  suffix:
    valueFrom:
      envVariable: PYTEST_MODEL_USER
toolchainRegion: us-west-2
groups: []
targetAccountMappings: []
"""
    )

    deployment_manifest = DeploymentManifest(**generator_yaml)
    assert deployment_manifest.name == "test-TESTUSER"
    assert deployment_manifest.name_generator is None

    generator_yaml = yaml.safe_load(
        """
nameGenerator:
  prefix:
    valueFrom:
      envVariable: PYTEST_MODEL_USER
  suffix: -test
toolchainRegion: us-west-2
groups: []
targetAccountMappings: []
"""
    )

    deployment_manifest = DeploymentManifest(**generator_yaml)
    assert deployment_manifest.name == "TESTUSER-test"
    assert deployment_manifest.name_generator is None

    generator_yaml = yaml.safe_load(
        """
name: test-name
nameGenerator:
  prefix: test
  suffix: -test
toolchainRegion: us-west-2
groups: []
targetAccountMappings: []
"""
    )

    with pytest.raises(seedfarmer.errors.InvalidManifestError) as e:
        deployment_manifest = DeploymentManifest(**generator_yaml)
    assert str(e.value) == "Only one of 'name' or 'name_generator' can be specified"

    generator_yaml = yaml.safe_load(
        """
toolchainRegion: us-west-2
groups: []
targetAccountMappings: []
"""
    )

    with pytest.raises(seedfarmer.errors.InvalidManifestError) as e:
        deployment_manifest = DeploymentManifest(**generator_yaml)
    assert str(e.value) == "One of 'name' or 'name_generator' is required"

    generator_yaml = yaml.safe_load(
        """
nameGenerator:
  prefix: test-
  suffix:
    valueFrom:
      moduleMetadata:
        group: none
        name: none
toolchainRegion: us-west-2
groups: []
targetAccountMappings: []
"""
    )

    with pytest.raises(seedfarmer.errors.InvalidManifestError) as e:
        deployment_manifest = DeploymentManifest(**generator_yaml)
    assert str(e.value) == "Loading value from Module Metadata is not supported on a NameGenerator"

    generator_yaml = yaml.safe_load(
        """
nameGenerator:
  prefix: test-
  suffix:
    valueFrom:
      envVariable: PYTEST_NO_VAR
toolchainRegion: us-west-2
groups: []
targetAccountMappings: []
"""
    )

    with pytest.raises(seedfarmer.errors.InvalidManifestError) as e:
        deployment_manifest = DeploymentManifest(**generator_yaml)
    assert str(e.value) == "Unable to resolve value from Environment Variable: PYTEST_NO_VAR"


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
    with pytest.raises(seedfarmer.errors.InvalidManifestError):
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
    with pytest.raises(seedfarmer.errors.InvalidManifestError):
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

    with pytest.raises(seedfarmer.errors.InvalidManifestError):
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

    with pytest.raises(seedfarmer.errors.InvalidManifestError):
        manifest.validate_and_set_module_defaults()


@pytest.mark.models
@pytest.mark.models_module_manifest
def test_module_manifest_with_parameters():
    manifest = DeploymentManifest(**deployment_yaml)

    module_yaml = yaml.safe_load(
        """
name: test-module-1
path: modules/test-module
targetAccount: primary
targetRegion: us-west-2
parameters:
  - name: param1
    value: value1
"""
    )

    module = ModuleManifest(**module_yaml)
    manifest.groups[0].modules = [module]
    manifest.validate_and_set_module_defaults()

    assert module.target_account == "primary"
    assert module.target_region == "us-west-2"
    assert module.parameters[0].name == "param1"
    assert module.parameters[0].value == "value1"


@pytest.mark.models
@pytest.mark.models_module_manifest
def test_module_manifest_with_value_from_parameters():
    manifest = DeploymentManifest(**deployment_yaml)

    module_yaml = yaml.safe_load(
        """
name: test-module-1
path: modules/test-module
targetAccount: primary
targetRegion: us-west-2
parameters:
  - name: param1
    valueFrom:
      moduleMetadata:
        group: test-group
        name: test-module-1
        key: param-key
"""
    )

    module = ModuleManifest(**module_yaml)
    manifest.groups[0].modules = [module]
    manifest.validate_and_set_module_defaults()

    assert module.target_account == "primary"
    assert module.target_region == "us-west-2"
    assert module.parameters[0].name == "param1"
    assert module.parameters[0].value_from


@pytest.mark.models
@pytest.mark.models_module_manifest
def test_module_manifest_with_incorrect_value_error():
    manifest = DeploymentManifest(**deployment_yaml)

    module_yaml = yaml.safe_load(
        """
name: test-module-1
path: modules/test-module
targetAccount: primary
targetRegion: us-west-2
parameters:
  - name: param1
    value: value1
    value_from:
      moduleMetadata:
        group: test-group
        name: test-module-1
        key: param-key
"""
    )

    with pytest.raises(InvalidManifestError):
        module = ModuleManifest(**module_yaml)
        manifest.groups[0].modules = [module]
        manifest.validate_and_set_module_defaults()


@pytest.mark.models
@pytest.mark.models_module_manifest
def test_module_manifest_with_unknown_value():
    manifest = DeploymentManifest(**deployment_yaml)

    module_yaml = yaml.safe_load(
        """
name: test-module-1
path: modules/test-module
targetAccount: primary
targetRegion: us-west-2
parameters:
  - name: param1
    value: value1
    non_existent_value: fail_me
"""
    )

    with pytest.raises(InvalidManifestError):
        module = ModuleManifest(**module_yaml)
        manifest.groups[0].modules = [module]
        manifest.validate_and_set_module_defaults()


@pytest.mark.models
@pytest.mark.models_module_manifest
def test_module_manifest_with_unknown_value_config_no_fail():
    manifest = DeploymentManifest(**deployment_yaml)

    module_yaml = yaml.safe_load(
        """
name: test-module-1
path: modules/test-module
targetAccount: primary
targetRegion: us-west-2
parameters:
  - name: param1
    value: value1
    non_existent_value: fail_me
"""
    )

    with mock.patch("seedfarmer.config") as config:
        config.MANIFEST_VALIDATION_FAIL_ON_UNKNOWN_FIELDS = False

        module = ModuleManifest(**module_yaml)
        manifest.groups[0].modules = [module]
        manifest.validate_and_set_module_defaults()



@pytest.mark.models
@pytest.mark.models_module_manifest
def test_module_manifest_with_both_value_and_value_from_error():
    manifest = DeploymentManifest(**deployment_yaml)

    module_yaml = yaml.safe_load(
        """
name: test-module-1
path: modules/test-module
targetAccount: primary
targetRegion: us-west-2
parameters:
  - name: param1
"""
    )

    with pytest.raises(InvalidManifestError):
        module = ModuleManifest(**module_yaml)
        manifest.groups[0].modules = [module]
        manifest.validate_and_set_module_defaults()

@pytest.mark.models
@pytest.mark.models_deployspec
def test_deployspec():
    # Clear targetAccountMapping and regionMapping defaults
    updated_deployment_yaml = deepcopy(deployment_yaml)
    updated_deployment_yaml["targetAccountMappings"][0]["default"] = False
    updated_deployment_yaml["targetAccountMappings"][0]["regionMappings"][0]["default"] = False
    manifest = DeploymentManifest(**updated_deployment_yaml)

    deployspec_yaml = yaml.safe_load(
        """
deploy:
  phases:
    install:
      commands:
      - pip install -r requirements.txt
    build:
      commands:
      - echo "Hi
destroy:
  phases:
    install:
      commands:
      - pip install -r requirements.txt
      - npm install -g aws-cdk@2.20.0
    build:
      commands:
      - echo "Hi
build_type: BUILD_GENERAL1_SMALL
"""
    )

    deploy_spec = DeploySpec(**deployspec_yaml)

    deploy_spec_default = yaml.safe_load(
        """
deploy:
  phases:
    install:
      commands:
      - pip install -r requirements.txt
    build:
      commands:
      - echo "Hi
destroy:
  phases:
    install:
      commands:
      - pip install -r requirements.txt
      - npm install -g aws-cdk@2.20.0
    build:
      commands:
      - echo "Hi
"""
    )
    deploy_spec_default = DeploySpec(**deploy_spec_default)


### DeployResponses
@pytest.mark.models
@pytest.mark.models_deployresponses
def test_deployresponses():
    cm = CodeSeederMetadata(
        aws_account_id="123456789012",
        aws_region="us-east-1",
        codebuild_build_id="codebuild:12345",
        codebuild_log_path="/somepath",
    )
