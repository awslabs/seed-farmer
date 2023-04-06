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
import boto3
import yaml

import pytest
import seedfarmer.mgmt.deploy_utils as du
from seedfarmer.models.manifests import DeploymentManifest, ModulesManifest
from seedfarmer.services._service_utils import boto3_client
from seedfarmer.services.session_manager import SessionManager
import mock_manifests
from moto import mock_sts

_logger: logging.Logger = logging.getLogger(__name__)


@pytest.fixture(scope="function")
def aws_credentials():
    """Mocked AWS Credentials for moto."""
    os.environ["AWS_ACCESS_KEY_ID"] = "testing"
    os.environ["AWS_SECRET_ACCESS_KEY"] = "testing"
    os.environ["AWS_SECURITY_TOKEN"] = "testing"
    os.environ["AWS_SESSION_TOKEN"] = "testing"
    os.environ["AWS_DEFAULT_REGION"] = "us-east-1"
    os.environ["MOTO_ACCOUNT_ID"] = "123456789012"


@pytest.fixture(scope="function")
def sts_client(aws_credentials):
    with mock_sts():
        yield boto3_client(service_name="sts", session=None)

@pytest.fixture(scope="function")       
def session_manager(sts_client):
    SessionManager._instances={}
    SessionManager().get_or_create(
        project_name="test",
        region_name="us-east-1",
        toolchain_region="us-east-1",
        enable_reaper=False,
    )

    
    
      


@pytest.mark.mgmt
@pytest.mark.mgmt_deployment_utils
def test_dependency_maps():
    module_depends_on, module_dependencies = du.generate_dependency_maps(DeploymentManifest(**mock_manifests.deployment_manifest))
    assert 'optionals-networking' in list(module_depends_on['core-eks'])
    assert 'core-eks' in list(module_dependencies['optionals-networking'])
    
@pytest.mark.mgmt
@pytest.mark.mgmt_deployment_utils
def test_validate_group_parameters():
    manifest = DeploymentManifest(**mock_manifests.deployment_manifest)
    du.validate_group_parameters(manifest.groups[1])
    
@pytest.mark.mgmt
@pytest.mark.mgmt_deployment_utils
def test_validate_group_parameters_failure():
    manifest = ModulesManifest(**mock_manifests.modules_manifest_duplicate)
    with pytest.raises(SystemExit) as dupe_error:
        du.validate_group_parameters(manifest)
        
    assert dupe_error.value.code == 1
    
  
@pytest.mark.mgmt
@pytest.mark.mgmt_deployment_utils
def test_need_to_build(mocker,session_manager):
    manifest = DeploymentManifest(**mock_manifests.deployment_manifest)
    module_manifest= manifest.groups[1].modules[0]
    mocker.patch("seedfarmer.mgmt.deploy_utils.mi.does_md5_match", return_value=True)
    needed = du.need_to_build(deployment_name='test',
                              group_name='group',
                              module_manifest=module_manifest,deployment_params_cache=None)
    assert needed == False
 
@pytest.mark.mgmt
@pytest.mark.mgmt_deployment_utils
def test_need_to_build_yes(mocker,session_manager):
    manifest = DeploymentManifest(**mock_manifests.deployment_manifest)
    module_manifest= manifest.groups[1].modules[0]
    mocker.patch("seedfarmer.mgmt.deploy_utils.mi.does_md5_match", return_value=False)
    needed = du.need_to_build(deployment_name='test',
                              group_name='group',
                              module_manifest=module_manifest,deployment_params_cache=None)
    assert needed == True 
 
    
#---------------------------------
# Test SSM methods in deploy_utils
#---------------------------------
@pytest.mark.mgmt
@pytest.mark.mgmt_deployment_utils
def test_write_deployed_deployment_manifest(mocker,session_manager):
    mocker.patch("seedfarmer.mgmt.deploy_utils.mi.write_deployed_deployment_manifest", return_value=None)
    du.write_deployed_deployment_manifest(DeploymentManifest(**mock_manifests.deployment_manifest))
    
@pytest.mark.mgmt
@pytest.mark.mgmt_deployment_utils
def test_prepare_ssm_for_deploy(mocker,session_manager):
    mocker.patch("seedfarmer.mgmt.deploy_utils.mi.write_module_manifest", return_value=None)
    mocker.patch("seedfarmer.mgmt.deploy_utils.mi.write_deployspec", return_value=None)
    mocker.patch("seedfarmer.mgmt.deploy_utils.mi.write_module_md5", return_value=None)
    mocker.patch("seedfarmer.mgmt.deploy_utils.mi.remove_module_md5", return_value=None)
    manifest = DeploymentManifest(**mock_manifests.deployment_manifest)
    module_manifest= manifest.groups[1].modules[0]
    du.prepare_ssm_for_deploy(deployment_name='test',
                              group_name='group',
                              module_manifest=module_manifest,
                              account_id='123456789012',
                              region='us-east-1')




@pytest.mark.mgmt
@pytest.mark.mgmt_deployment_utils
def test_generate_deployed_manifest_already_deployed(mocker,session_manager):
    mocker.patch("seedfarmer.mgmt.deploy_utils.mi.get_deployed_deployment_manifest", return_value=mock_manifests.deployment_manifest)
    mocker.patch("seedfarmer.mgmt.deploy_utils.mi.get_deployment_manifest", return_value=mock_manifests.deployment_manifest)
    mocker.patch("seedfarmer.mgmt.deploy_utils.populate_module_info_index", return_value=None)
    mocker.patch("seedfarmer.mgmt.deploy_utils._populate_group_modules_from_index",return_value=mock_manifests.deployment_manifest['groups'])
    du.generate_deployed_manifest(deployment_name="myapp",
                                  skip_deploy_spec=True,
                                  ignore_deployed=True)
    
@pytest.mark.mgmt
@pytest.mark.mgmt_deployment_utils
def test_generate_deployed_manifest(mocker,session_manager):
    mocker.patch("seedfarmer.mgmt.deploy_utils.mi.get_deployed_deployment_manifest", return_value=None)
    mocker.patch("seedfarmer.mgmt.deploy_utils.mi.get_deployment_manifest", return_value=mock_manifests.deployment_manifest)
    mocker.patch("seedfarmer.mgmt.deploy_utils.populate_module_info_index", return_value=None)
    mocker.patch("seedfarmer.mgmt.deploy_utils._populate_group_modules_from_index",return_value=mock_manifests.deployment_manifest['groups'])
    du.generate_deployed_manifest(deployment_name="myapp",
                                  skip_deploy_spec=True,
                                  ignore_deployed=False)
    
    
@pytest.mark.mgmt
@pytest.mark.mgmt_deployment_utils
def test_get_deployed_group_ordering_not_deployed(mocker,session_manager):
    mocker.patch("seedfarmer.mgmt.deploy_utils.mi.get_deployed_deployment_manifest", return_value=None)
    mocker.patch("seedfarmer.mgmt.deploy_utils.mi.get_deployment_manifest", return_value=mock_manifests.deployment_manifest)
    mocker.patch("seedfarmer.mgmt.deploy_utils.populate_module_info_index", return_value=None)
    mocker.patch("seedfarmer.mgmt.deploy_utils._populate_group_modules_from_index",return_value=mock_manifests.deployment_manifest['groups'])
    du.get_deployed_group_ordering(deployment_name="myapp") 
    
@pytest.mark.mgmt
@pytest.mark.mgmt_deployment_utils
def test_get_deployed_group_ordering_deployed(mocker,session_manager):
    mocker.patch("seedfarmer.mgmt.deploy_utils.mi.get_deployed_deployment_manifest", return_value=mock_manifests.deployment_manifest)
    mocker.patch("seedfarmer.mgmt.deploy_utils.mi.get_deployment_manifest", return_value=mock_manifests.deployment_manifest)
    mocker.patch("seedfarmer.mgmt.deploy_utils.populate_module_info_index", return_value=None)
    mocker.patch("seedfarmer.mgmt.deploy_utils._populate_group_modules_from_index",return_value=mock_manifests.deployment_manifest['groups'])
    du.get_deployed_group_ordering(deployment_name="myapp")