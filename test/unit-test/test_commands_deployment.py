import logging
import os
import boto3
import yaml, json
from typing import cast, Tuple
import pytest
import seedfarmer.commands._deployment_commands as dc

from seedfarmer.models.manifests import DeploymentManifest, ModuleManifest, ModuleParameter
from seedfarmer.models._deploy_spec import DeploySpec
from seedfarmer.services._service_utils import boto3_client
from seedfarmer.services.session_manager import SessionManager
import mock_data.mock_deployment_manifest_for_destroy as mock_deployment_manifest_for_destroy
import mock_data.mock_deployment_manifest_huge as mock_deployment_manifest_huge
import mock_data.mock_module_info_huge as mock_module_info_huge
import mock_data.mock_manifests as mock_manifests
import mock_data.mock_deployspec as mock_deployspec


from moto import mock_sts


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
 


@pytest.mark.commands
@pytest.mark.commands_deployment
def test_apply_clean(session_manager,mocker):  

    mocker.patch("seedfarmer.commands._deployment_commands.write_deployment_manifest", return_value=None)
    mocker.patch("seedfarmer.commands._deployment_commands.prime_target_accounts", return_value=None)
    mocker.patch("seedfarmer.commands._deployment_commands.du.populate_module_info_index", return_value=None)
    mocker.patch("seedfarmer.commands._deployment_commands.du.filter_deploy_destroy", return_value=None)
    mocker.patch("seedfarmer.commands._deployment_commands.write_deployment_manifest", return_value=None)
    mocker.patch("seedfarmer.commands._deployment_commands.du.validate_module_dependencies", return_value=None)
    mocker.patch("seedfarmer.commands._deployment_commands.destroy_deployment", return_value=None)
    mocker.patch("seedfarmer.commands._deployment_commands.deploy_deployment", return_value=None)
    dc.apply(deployment_manifest_path="test/unit-test/mock_data/manifests/module-test/deployment-hc.yaml",
             dryrun=True)

@pytest.mark.commands
@pytest.mark.commands_deployment
def test_apply_violations(session_manager,mocker):  

    mocker.patch("seedfarmer.commands._deployment_commands.write_deployment_manifest", return_value=None)
    mocker.patch("seedfarmer.commands._deployment_commands.prime_target_accounts", return_value=None)
    mocker.patch("seedfarmer.commands._deployment_commands.du.populate_module_info_index", return_value=None)
    mocker.patch("seedfarmer.commands._deployment_commands.du.filter_deploy_destroy", return_value=None)
    mocker.patch("seedfarmer.commands._deployment_commands.write_deployment_manifest", return_value=None)
    mocker.patch("seedfarmer.commands._deployment_commands.du.validate_module_dependencies", return_value=[{"module1":["moduleA","moduleB"]}])
    with pytest.raises(SystemExit) as pytest_wrapped_e:
        dc.apply(deployment_manifest_path="test/unit-test/mock_data/manifests/module-test/deployment-hc.yaml")
    assert pytest_wrapped_e.type == SystemExit
    

@pytest.mark.commands
@pytest.mark.commands_deployment
def test_destroy_clean(session_manager,mocker):  

    mocker.patch("seedfarmer.commands._deployment_commands.du.generate_deployed_manifest", 
                 return_value=DeploymentManifest(**mock_deployment_manifest_for_destroy.destroy_manifest))
    mocker.patch("seedfarmer.commands._deployment_commands.destroy_deployment", return_value= None)

    dc.destroy(deployment_name="myapp",dryrun=True, retain_seedkit=False)


@pytest.mark.commands
@pytest.mark.commands_deployment
def test_destroy_not_found(session_manager,mocker):  

    mocker.patch("seedfarmer.commands._deployment_commands.du.generate_deployed_manifest", return_value=None)
    mocker.patch("seedfarmer.commands._deployment_commands.destroy_deployment", return_value= None)

    dc.destroy(deployment_name="myapp",dryrun=True, retain_seedkit=False)
    
    
    
# @pytest.mark.commands
# @pytest.mark.commands_deployment
# def test_tear_down_target_accounts(session_manager,mocker):
#     mocker.patch("seedfarmer.commands._deployment_commands.tear_down_target_accounts._teardown_accounts", return_value=None)
#     # mocker.patch("seedfarmer.commands._deployment_commands.tear_down_target_accounts._teardown_accounts", 
#     #              return_value=None)
#     # with mocker.patch('seedfarmer.commands._deployment_commands.tear_down_target_accounts') as teardown:
#     #     teardown.
    ### COMMENT....I cannot get the nested threads to mock
#     dc.tear_down_target_accounts(deployment_manifest=DeploymentManifest(**mock_deployment_manifest_for_destroy.destroy_manifest))
    
    
@pytest.mark.commands
@pytest.mark.commands_deployment
def test_deploy_deployment_is_dry_run(session_manager,mocker):
    dep = DeploymentManifest(**mock_deployment_manifest_for_destroy.destroy_manifest)
    dc._deploy_deployment_is_dry_run(groups_to_deploy=dep.groups, deployment_name="myapp") 
    
    
@pytest.mark.commands
@pytest.mark.commands_deployment
def test_clone_module_repo(mocker):
    git_path_test = "git::https://github.com/awslabs/seedfarmer-modules.git//modules/dummy/blank?ref=release/1.0.0&depth=1"
    return_dir =dc._clone_module_repo(git_path=git_path_test)
    # Rerun it so all methods are hit
    return_dir =dc._clone_module_repo(git_path=git_path_test)
    
    
    
@pytest.mark.commands
@pytest.mark.commands_deployment
def test_execute_deploy_invalid_spec(session_manager,mocker):
    mocker.patch("seedfarmer.commands._deployment_commands.load_parameter_values",return_value=None)
    mocker.patch("seedfarmer.commands._deployment_commands.commands.deploy_module_stack", return_value=("stack_name","role_name"))
    mocker.patch("seedfarmer.commands._deployment_commands.get_module_metadata",return_value=None)
    mocker.patch("seedfarmer.commands._deployment_commands.du.prepare_ssm_for_deploy",return_value=None)
    dep = DeploymentManifest(**mock_deployment_manifest_huge.deployment_manifest)
    group = dep.groups[0]
    with pytest.raises( ValueError):
        dc._execute_deploy(group_name=group.name,
                        module_manifest=group.modules[0],
                        deployment_manifest = dep,
                        docker_credentials_secret=None,
                        permissions_boundary_arn=None,
                        codebuild_image=None)
        
@pytest.mark.commands
@pytest.mark.commands_deployment
def test_execute_deploy(session_manager,mocker):
    mocker.patch("seedfarmer.commands._deployment_commands.load_parameter_values",return_value=None)
    mocker.patch("seedfarmer.commands._deployment_commands.commands.deploy_module_stack", return_value=("stack_name","role_name"))
    mocker.patch("seedfarmer.commands._deployment_commands.get_module_metadata",return_value=None)
    mocker.patch("seedfarmer.commands._deployment_commands.du.prepare_ssm_for_deploy",return_value=None)
    mocker.patch("seedfarmer.commands._deployment_commands.commands.deploy_module",return_value=None)
    dep = DeploymentManifest(**mock_deployment_manifest_huge.deployment_manifest)
    group = dep.groups[0]
    module_manifest=group.modules[0]
    module_manifest.deploy_spec=DeploySpec(**mock_deployspec.dummy_deployspec)
    dc._execute_deploy(group_name=group.name,
                       module_manifest=module_manifest,
                       deployment_manifest = dep,
                       docker_credentials_secret=None,
                       permissions_boundary_arn=None,
                       codebuild_image=None)  
    
    
    
@pytest.mark.commands
@pytest.mark.commands_deployment
def test_execute_destroy_invalid_spec(session_manager,mocker):
    from seedfarmer.models.deploy_responses import ModuleDeploymentResponse
    dep = DeploymentManifest(**mock_deployment_manifest_huge.deployment_manifest)
    group = dep.groups[0]
    module_manifest=group.modules[0]
    mod_resp = ModuleDeploymentResponse(deployment="myapp", group="optionals",module="metworking", status="SUCCESS")

    
    mocker.patch("seedfarmer.commands._deployment_commands.get_module_metadata",return_value=None)
    mocker.patch("seedfarmer.commands._deployment_commands.commands.get_module_stack_info",
                 return_value=("stack_name","role_name"))
    mocker.patch("seedfarmer.commands._deployment_commands.commands.destroy_module",return_value=mod_resp)
    with pytest.raises( ValueError):
        dc._execute_destroy(group_name=group.name,
                        module_manifest=module_manifest,
                        module_path="to/my/module",
                        deployment_manifest = dep,
                        docker_credentials_secret=None,
                        codebuild_image=None)  

@pytest.mark.commands
@pytest.mark.commands_deployment
def test_execute_destroy(session_manager,mocker):
    from seedfarmer.models.deploy_responses import ModuleDeploymentResponse
    dep = DeploymentManifest(**mock_deployment_manifest_huge.deployment_manifest)
    group = dep.groups[0]
    module_manifest=group.modules[0]
    mod_resp = ModuleDeploymentResponse(deployment="myapp", group="optionals",module="metworking", status="SUCCESS")
    mocker.patch("seedfarmer.commands._deployment_commands.get_module_metadata",return_value=None)
    mocker.patch("seedfarmer.commands._deployment_commands.commands.get_module_stack_info",
                 return_value=("stack_name","role_name"))
    mocker.patch("seedfarmer.commands._deployment_commands.commands.destroy_module",return_value=mod_resp)
    mocker.patch("seedfarmer.commands._deployment_commands.commands.destroy_module_stack",return_value=None)
    module_manifest.deploy_spec=DeploySpec(**mock_deployspec.dummy_deployspec)
    dc._execute_destroy(group_name=group.name,
                    module_manifest=module_manifest,
                    module_path="to/my/module",
                    deployment_manifest = dep,
                    docker_credentials_secret=None,
                    codebuild_image=None)  


    
@pytest.mark.commands
@pytest.mark.commands_deployment
def test_deploy_deployment(session_manager,mocker):
    import hashlib
    mock_hashlib = hashlib.md5(json.dumps({"hey":"yp"}, sort_keys=True).encode("utf-8"))
    
    import seedfarmer.mgmt.deploy_utils as du
    mocker.patch("seedfarmer.mgmt.deploy_utils.mi.get_parameter_data_cache",return_value=mock_module_info_huge.module_index_info_huge)
    module_info_index=du.populate_module_info_index(deployment_manifest=DeploymentManifest(**mock_manifests.deployment_manifest))
    
    
    
    dep = DeploymentManifest(**mock_deployment_manifest_huge.deployment_manifest)
    mocker.patch("seedfarmer.commands._deployment_commands.print_manifest_inventory",return_value=None)
    mocker.patch("seedfarmer.commands._deployment_commands.du.validate_group_parameters",return_value=None)
    mocker.patch("seedfarmer.commands._deployment_commands.get_deployspec_path", 
                 return_value='test/unit-test/mock_data/mock_deployspec.yaml')
    mocker.patch("seedfarmer.commands._deployment_commands.checksum.get_module_md5",return_value="asfsadfsdfa")
    mocker.patch("seedfarmer.commands._deployment_commands.hashlib.md5",return_value=mock_hashlib)
    
    
    mocker.patch("seedfarmer.commands._deployment_commands._deploy_deployment_is_not_dry_run",return_value=None)
    mocker.patch("seedfarmer.commands._deployment_commands.du.need_to_build",
                 return_value=None)
    # mocker.patch("seedfarmer.commands._deployment_commands.module_info_index.get_module_info",
    #              return_value=None)
    mocker.patch("seedfarmer.commands._deployment_commands.print_bolded",return_value=None)
    dc.deploy_deployment(deployment_manifest=dep,module_info_index=module_info_index)