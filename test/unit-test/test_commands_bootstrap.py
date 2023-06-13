import logging
import os
import boto3
import yaml

import pytest
import seedfarmer
import seedfarmer.commands._bootstrap_commands as bc

from seedfarmer.models.manifests import DeploymentManifest, ModuleManifest, ModulesManifest
from seedfarmer.services._service_utils import boto3_client
from seedfarmer.services.session_manager import SessionManager

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
 
# deployment_yaml = yaml.safe_load(
#     """
# name: test
# toolchainRegion: us-east-1
# groups:
#   - name: optionals
#     path: manifests/test/optional-modules.yaml
# targetAccountMappings:
#   - alias: primary
#     accountId: "123456789012"
#     default: true
#     regionMappings:
#       - region: us-east-1
#         default: true
#         parametersRegional:
#           someKey: someValue
# """
# )
 
    
@pytest.mark.commands
@pytest.mark.commands_bootstrap
def test_deploy_template(session_manager, mocker):
    mocker.patch("seedfarmer.commands._bootstrap_commands.role_deploy_status",return_value={"RoleName":"BLAHBLAH"})
    mocker.patch("seedfarmer.commands._bootstrap_commands.cs_services.cfn.deploy_template",return_value=None)
    template = bc.get_toolchain_template(project_name="myapp",
                                         role_name="seedfarmer-test-toolchain-role",
                                         principal_arn=['arn:aws:iam::123456789012:role/AdminRole']
                                         )
    
    bc.deploy_template(template=template,stack_name="UnitTest",session=None)

@pytest.mark.commands
@pytest.mark.commands_bootstrap
def test_apply_deploy_logic(session_manager, mocker):
    mocker.patch("seedfarmer.commands._bootstrap_commands.role_deploy_status",return_value=({"RoleName":"BLAHBLAH"},["exists"]))
    mocker.patch("seedfarmer.commands._bootstrap_commands.cs_services.cfn.deploy_template",return_value=None)
    template = bc.get_toolchain_template(project_name="myapp",
                                         role_name="seedfarmer-test-toolchain-role",
                                         principal_arn=['arn:aws:iam::123456789012:role/AdminRole']
                                         )
    
    bc.apply_deploy_logic(template=template,
                          role_name="toolchain-role",
                          stack_name="toolchain-stack",
                          session=None)

@pytest.mark.commands
@pytest.mark.commands_bootstrap
def test_apply_deploy_logic_role_not_exists(session_manager, mocker):
    mocker.patch("seedfarmer.commands._bootstrap_commands.role_deploy_status",return_value=(None,["exists"]))
    mocker.patch("seedfarmer.commands._bootstrap_commands.cs_services.cfn.deploy_template",return_value=None)
    template = bc.get_toolchain_template(project_name="myapp",
                                         role_name="seedfarmer-test-toolchain-role",
                                         principal_arn=['arn:aws:iam::123456789012:role/AdminRole']
                                         )
    
    bc.apply_deploy_logic(template=template,
                          role_name="toolchain-role",
                          stack_name="toolchain-stack",
                          session=None)

@pytest.mark.commands
@pytest.mark.commands_bootstrap
def test_apply_deploy_logic_stack_not_exists(session_manager, mocker):
    mocker.patch("seedfarmer.commands._bootstrap_commands.role_deploy_status",return_value=(None,None))
    mocker.patch("seedfarmer.commands._bootstrap_commands.cs_services.cfn.deploy_template",return_value=None)
    template = bc.get_toolchain_template(project_name="myapp",
                                         role_name="seedfarmer-test-toolchain-role",
                                         principal_arn=['arn:aws:iam::123456789012:role/AdminRole']
                                         )
    
    bc.apply_deploy_logic(template=template,
                          role_name="toolchain-role",
                          stack_name="toolchain-stack",
                          session=None)
    
    
    
    
    
@pytest.mark.commands
@pytest.mark.commands_bootstrap
@pytest.mark.parametrize("session", [boto3.Session()])
def test_bootstrap_toolchain_account(mocker, session):
    #template = bc.get_toolchain_template(project_name="myapp",principal_arn=['arn:aws:iam::123456789012:role/AdminRole']
                                         
    mocker.patch("seedfarmer.commands._bootstrap_commands.apply_deploy_logic",return_value="")
    mocker.patch("seedfarmer.commands._bootstrap_commands.bootstrap_target_account",return_value="")
    bc.bootstrap_toolchain_account(project_name="testing",
                                   principal_arns=['arn:aws:iam::123456789012:role/AdminRole'],
                                   permissions_boundary_arn=None,
                                   region_name="us-east-1",
                                   synthesize=False,
                                   as_target=False)

@pytest.mark.commands
@pytest.mark.commands_bootstrap
@pytest.mark.parametrize("session", [boto3.Session()])
def test_bootstrap_toolchain_account_synth(mocker, session):
    #template = bc.get_toolchain_template(project_name="myapp",principal_arn=['arn:aws:iam::123456789012:role/AdminRole']
                                         
    mocker.patch("seedfarmer.commands._bootstrap_commands.apply_deploy_logic",return_value="")
    bc.bootstrap_toolchain_account(project_name="testing",
                                   principal_arns=['arn:aws:iam::123456789012:role/AdminRole'],
                                   permissions_boundary_arn=None,
                                   region_name="us-east-1",
                                   synthesize=True,
                                   as_target=False)
    
    
@pytest.mark.commands
@pytest.mark.commands_bootstrap
@pytest.mark.parametrize("session", [boto3.Session()])
def test_bootstrap_target_account(mocker, session):
    #template = bc.get_toolchain_template(project_name="myapp",principal_arn=['arn:aws:iam::123456789012:role/AdminRole']
                                         
    mocker.patch("seedfarmer.commands._bootstrap_commands.apply_deploy_logic",return_value="")
    bc.bootstrap_target_account(toolchain_account_id="123456789012",
                                project_name="testing",
                                permissions_boundary_arn=None,
                                region_name="us-east-1",
                                synthesize=False,
                                session=session)