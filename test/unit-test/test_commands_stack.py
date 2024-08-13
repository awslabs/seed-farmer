import os

import pytest
import yaml
from moto import mock_aws

import seedfarmer.commands._stack_commands as sc
from seedfarmer.models.manifests import DeploymentManifest
from seedfarmer.services._service_utils import boto3_client
from seedfarmer.services.session_manager import SessionManager


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
    with mock_aws():
        yield boto3_client(service_name="sts", session=None)


@pytest.fixture(scope="function")
def session_manager(sts_client):
    SessionManager._instances = {}
    SessionManager().get_or_create(
        project_name="test",
        region_name="us-east-1",
        toolchain_region="us-east-1",
        enable_reaper=False,
    )


deployment_yaml = yaml.safe_load(
    """
name: test
toolchainRegion: us-east-1
groups:
  - name: optionals
    path: manifests/test/optional-modules.yaml
targetAccountMappings:
  - alias: primary
    accountId: "123456789012"
    default: true
    regionMappings:
      - region: us-east-1
        default: true
        parametersRegional:
          someKey: someValue
"""
)

manage_policy_json = {
    "Policy": {
        "PolicyName": "addf-managed-policy-ProjectPolicy-7PSXY0GVW23I",
        "PolicyId": "ANPAY667V3NQ3CYB253RG",
        "Arn": "arn:aws:iam::123456789012:policy/addf-managed-policy-ProjectPolicy-7PSXY0GVW23I",
        "Path": "/",
        "DefaultVersionId": "v1",
        "AttachmentCount": 0,
        "PermissionsBoundaryUsageCount": 0,
        "IsAttachable": True,
        "Description": "Managed Policy granting access to build a project",
        "Tags": [],
    }
}


@pytest.mark.commands
@pytest.mark.commands_stack
def test_deploy_managed_policy_stack_exists(session_manager, mocker):
    mocker.patch("seedfarmer.commands._stack_commands.services.cfn.does_stack_exist", return_value=[True, {}])
    mocker.patch("seedfarmer.commands._stack_commands.services.cfn.deploy_template", return_value=None)
    sc.deploy_managed_policy_stack(
        deployment_manifest=DeploymentManifest(**deployment_yaml), account_id="123456789012", region="us-east-1"
    )


@pytest.mark.commands
@pytest.mark.commands_stack
def test_deploy_managed_policy_stack_not_exists(session_manager, mocker):
    mocker.patch("seedfarmer.commands._stack_commands.services.cfn.does_stack_exist", return_value=[False, {}])
    mocker.patch("seedfarmer.commands._stack_commands.services.cfn.deploy_template", return_value=None)
    sc.deploy_managed_policy_stack(
        deployment_manifest=DeploymentManifest(**deployment_yaml), account_id="123456789012", region="us-east-1"
    )


@pytest.mark.commands
@pytest.mark.commands_stack
def test_destroy_managed_policy_stack_not_exists(session_manager, mocker):
    mocker.patch("seedfarmer.commands._stack_commands.services.cfn.does_stack_exist", return_value=[False, {}])
    mocker.patch("seedfarmer.commands._stack_commands.services.cfn.destroy_stack", return_value=None)
    sc.destroy_managed_policy_stack(account_id="123456789012", region="us-east-1")


@pytest.mark.commands
@pytest.mark.commands_stack
def test_destroy_managed_policy_stack(session_manager, mocker):
    mocker.patch("seedfarmer.commands._stack_commands.services.cfn.does_stack_exist", return_value=[True, {}])
    mocker.patch("seedfarmer.commands._stack_commands.services.cfn.destroy_stack", return_value=None)
    mocker.patch("seedfarmer.commands._stack_commands.iam.get_policy_info", return_value=manage_policy_json)
    sc.destroy_managed_policy_stack(account_id="123456789012", region="us-east-1")


@pytest.mark.commands
@pytest.mark.commands_stack
def test_destroy_module_stack(session_manager, mocker):
    mocker.patch("seedfarmer.commands._stack_commands.services.cfn.destroy_stack", return_value=None)
    mocker.patch("seedfarmer.commands._stack_commands.destroy_module_deployment_role", return_value=None)
    sc.destroy_module_stack(
        deployment_name="myapp",
        group_name="group",
        module_name="module",
        account_id="123456789012",
        region="us-east-1",
        docker_credentials_secret="fsfasdfsad",
    )


@pytest.mark.commands
@pytest.mark.commands_stack
def test_deploy_module_stack(session_manager, mocker):
    mocker.patch("seedfarmer.commands._stack_commands.services.cfn.deploy_template", return_value=None)
    mocker.patch("seedfarmer.commands._stack_commands.create_module_deployment_role", return_value=None)

    import mock_data.mock_deployment_manifest_huge as mock_deployment_manifest_huge

    dep = DeploymentManifest(**mock_deployment_manifest_huge.deployment_manifest)

    sc.deploy_module_stack(
        module_stack_path="test/unit-test/mock_data/modules/module-test/modulestack.yaml",
        deployment_name="myapp",
        group_name="group",
        module_name="module",
        account_id="123456789012",
        region="us-east-1",
        parameters=dep.groups[1].modules[1].parameters,
        docker_credentials_secret="fsfasdfsad",
    )


@pytest.mark.commands
@pytest.mark.commands_stack
def test_create_module_deployment_role(session_manager, mocker):
    mocker.patch(
        "seedfarmer.commands._stack_commands.services.cfn.does_stack_exist",
        return_value=(True, {"ProjectPolicyARN": "arn"}),
    )
    mocker.patch("seedfarmer.commands._stack_commands.iam.create_check_iam_role", return_value=None)
    mocker.patch(
        "seedfarmer.commands._stack_commands.commands.seedkit_deployed",
        return_value=(True, "stackname", {"SeedkitResourcesPolicyArn": "arn"}),
    )
    mocker.patch(
        "seedfarmer.commands._stack_commands.iam.attach_policy_to_role",
        return_value=["arn:aws:iam::aws:policy/AdministratorAccess", "arn:aws:iam::aws:policy/AdministratorAccess2"],
    )
    mocker.patch("seedfarmer.commands._stack_commands.iam.attach_inline_policy", return_value=None)

    sc.create_module_deployment_role(
        role_name="module-deployment-role",
        deployment_name="myapp",
        group_name="group",
        module_name="module",
        docker_credentials_secret="fsfasdfsad",
    )


@pytest.mark.commands
@pytest.mark.commands_stack
def test_destroy_module_deployment_role(session_manager, mocker):
    mocker.patch("seedfarmer.commands._stack_commands.services.cfn.does_stack_exist", return_value=[True, {}])
    mocker.patch("seedfarmer.commands._stack_commands.iam.delete_role", return_value=None)
    mocker.patch("seedfarmer.commands._stack_commands.iam.detach_inline_policy_from_role", return_value=None)
    sc.destroy_module_deployment_role(
        role_name="module-deployment-role",
        docker_credentials_secret="fsfasdfsad",
    )


@pytest.mark.commands
@pytest.mark.commands_stack
def test_destroy_seedkit(session_manager, mocker):
    mocker.patch("seedfarmer.commands._stack_commands.commands.destroy_seedkit", return_value=None)
    sc.destroy_seedkit(account_id="123456789012", region="us-east-1")


# get_module_stack_info


@pytest.mark.commands
@pytest.mark.commands_stack
def test_deploy_seedkit_exists(session_manager, mocker):
    mocker.patch(
        "seedfarmer.commands._stack_commands.commands.seedkit_deployed",
        return_value=(True, "stackname", {"CodeArtifactRepository": "asdfsfa"}),
    )
    mocker.patch("seedfarmer.commands._stack_commands.commands.deploy_seedkit", return_value=None)
    sc.deploy_seedkit(
        account_id="123456789012",
        region="us-east-1",
        vpc_id="vpc-adfsfas",
        private_subnet_ids=["subnet-234234", "subnet-657657"],
        security_group_ids=["sg-1", "sg-2"],
    )


@pytest.mark.commands
@pytest.mark.commands_stack
def test_deploy_seedkit_no_exists(session_manager, mocker):
    mocker.patch(
        "seedfarmer.commands._stack_commands.commands.seedkit_deployed",
        return_value=(False, "stackname", {"CodeArtifactRepository": "asdfsfa"}),
    )
    mocker.patch("seedfarmer.commands._stack_commands.commands.deploy_seedkit", return_value=None)
    sc.deploy_seedkit(
        account_id="123456789012",
        region="us-east-1",
        vpc_id="vpc-adfsfas",
        private_subnet_ids=["subnet-234234", "subnet-657657"],
        security_group_ids=["sg-1", "sg-2"],
    )


@pytest.mark.commands
@pytest.mark.commands_stack
def test_get_module_stack_info(session_manager, mocker):
    mocker.patch(
        "seedfarmer.commands._stack_commands.get_module_stack_names", return_value=("TheStackname", "TheRoleName")
    )
    mocker.patch("aws_codeseeder.services.cfn.does_stack_exist", return_value=(True, {}))
    sc.get_module_stack_info(
        deployment_name="myapp", group_name="group", module_name="module", account_id="123456789012", region="us-east-1"
    )
