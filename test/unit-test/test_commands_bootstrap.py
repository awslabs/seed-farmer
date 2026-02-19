import os

import boto3
import pytest
from botocore.exceptions import WaiterError
from moto import mock_aws

import seedfarmer
import seedfarmer.commands._bootstrap_commands as bc
import seedfarmer.errors
from seedfarmer.services._service_utils import boto3_client
from seedfarmer.services.session_manager import (
    SessionManager,
    SessionManagerRemoteImpl,
)


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
    SessionManager._real_instance = None
    real_instance = SessionManagerRemoteImpl()
    SessionManager.bind(real_instance)
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
def test_get_template_invalid_yaml(mocker):
    """Test that get_template raises TypeError when YAML is not a dictionary."""
    # Mock open to return a non-dictionary YAML
    mocker.patch("builtins.open", mocker.mock_open(read_data="- item1\n- item2"))

    # Mock yaml.safe_load to return a list instead of a dict
    mocker.patch("yaml.safe_load", return_value=["item1", "item2"])

    # Verify that TypeError is raised
    with pytest.raises(TypeError, match="Expected dictionary from YAML file, got list"):
        bc.get_template("toolchain_role")


@pytest.mark.commands
@pytest.mark.commands_bootstrap
def test_write_template(mocker):
    """Test that write_template correctly outputs the template to stdout."""
    # Mock yaml.dump
    mock_dump = mocker.patch("yaml.dump")

    # Mock print
    mock_print = mocker.patch("builtins.print")

    # Call the function
    template = {"Resources": {"TestResource": {"Type": "AWS::S3::Bucket"}}}
    bc.write_template(template)

    # Verify yaml.dump was called with the template and sys.stdout
    mock_dump.assert_called_once_with(template, mocker.ANY)

    # Verify print was called with an empty string
    mock_print.assert_called_once_with("")


@pytest.mark.commands
@pytest.mark.commands_bootstrap
def test_deploy_template(session_manager, mocker):
    mocker.patch("seedfarmer.commands._bootstrap_commands.role_deploy_status", return_value={"RoleName": "BLAHBLAH"})
    mocker.patch("seedfarmer.commands._bootstrap_commands.cfn.deploy_template", return_value=None)
    template = bc.get_template("toolchain_role")
    parameters = {
        "ProjectName": "myapp",
        "RoleName": "seedfarmer-test-toolchain-role",
        "PrincipalArn": "arn:aws:iam::123456789012:role/AdminRole",
    }

    bc.deploy_template(template=template, stack_name="UnitTest", session=None, parameters=parameters)


@pytest.mark.commands
@pytest.mark.commands_bootstrap
def test_deploy_template_waiter_error(mocker):
    """Test that deploy_template handles WaiterError correctly."""
    # Mock os.makedirs
    mocker.patch("os.makedirs")

    # Mock open
    mocker.patch("builtins.open", mocker.mock_open())

    # Mock yaml.dump
    mocker.patch("yaml.dump")

    # Mock cfn.deploy_template to raise WaiterError
    mocker.patch("seedfarmer.services._cfn.deploy_template", side_effect=WaiterError("waiter_name", "reason", {}))

    # Mock os.remove
    mock_remove = mocker.patch("os.remove")

    # Call the function and verify it raises ModuleDeploymentError
    template = {"Resources": {"TestResource": {"Type": "AWS::S3::Bucket"}}}
    with pytest.raises(seedfarmer.errors.ModuleDeploymentError):
        bc.deploy_template(template=template, stack_name="test-stack", session=None, parameters={"Param1": "Value1"})

    # Verify os.remove was called (cleanup happens in finally block)
    mock_remove.assert_called_once()


@pytest.mark.commands
@pytest.mark.commands_bootstrap
def test_apply_deploy_logic(session_manager, mocker):
    mocker.patch(
        "seedfarmer.commands._bootstrap_commands.role_deploy_status",
        return_value=({"RoleName": "BLAHBLAH"}, ["exists"]),
    )
    mocker.patch("seedfarmer.commands._bootstrap_commands.cfn.deploy_template", return_value=None)
    template = bc.get_template("toolchain_role")
    parameters = {
        "ProjectName": "myapp",
        "RoleName": "seedfarmer-test-toolchain-role",
        "PrincipalArn": "arn:aws:iam::123456789012:role/AdminRole",
    }

    bc.apply_deploy_logic(
        template=template, role_name="toolchain-role", stack_name="toolchain-stack", session=None, parameters=parameters
    )


@pytest.mark.commands
@pytest.mark.commands_bootstrap
def test_apply_deploy_logic_role_not_exists(session_manager, mocker):
    mocker.patch("seedfarmer.commands._bootstrap_commands.role_deploy_status", return_value=(None, ["exists"]))
    mocker.patch("seedfarmer.commands._bootstrap_commands.cfn.deploy_template", return_value=None)
    template = bc.get_template("toolchain_role")
    parameters = {
        "ProjectName": "myapp",
        "RoleName": "seedfarmer-test-toolchain-role",
        "PrincipalArn": "arn:aws:iam::123456789012:role/AdminRole",
    }

    bc.apply_deploy_logic(
        template=template, role_name="toolchain-role", stack_name="toolchain-stack", session=None, parameters=parameters
    )


@pytest.mark.commands
@pytest.mark.commands_bootstrap
def test_apply_deploy_logic_stack_not_exists(session_manager, mocker):
    mocker.patch("seedfarmer.commands._bootstrap_commands.role_deploy_status", return_value=(None, None))
    mocker.patch("seedfarmer.commands._bootstrap_commands.cfn.deploy_template", return_value=None)
    template = bc.get_template("toolchain_role")
    parameters = {
        "ProjectName": "myapp",
        "RoleName": "seedfarmer-test-toolchain-role",
        "PrincipalArn": "arn:aws:iam::123456789012:role/AdminRole",
    }

    bc.apply_deploy_logic(
        template=template, role_name="toolchain-role", stack_name="toolchain-stack", session=None, parameters=parameters
    )


@pytest.mark.commands
@pytest.mark.commands_bootstrap
@pytest.mark.parametrize("session", [boto3.Session()])
def test_bootstrap_toolchain_account(mocker, session):
    mocker.patch("seedfarmer.commands._bootstrap_commands.apply_deploy_logic", return_value="")
    mocker.patch("seedfarmer.commands._bootstrap_commands.bootstrap_target_account", return_value="")
    mocker.patch(
        "seedfarmer.commands._bootstrap_commands.get_sts_identity_info",
        return_value=("1234566789012", "arn:aws", "aws"),
    )
    bc.bootstrap_toolchain_account(
        project_name="testing",
        principal_arns=["arn:aws:iam::123456789012:role/AdminRole"],
        permissions_boundary_arn=None,
        region_name="us-east-1",
        synthesize=False,
        as_target=False,
    )


@pytest.mark.commands
@pytest.mark.commands_bootstrap
@pytest.mark.parametrize("session", [boto3.Session()])
def test_bootstrap_toolchain_account_synth(mocker, session):
    mocker.patch("seedfarmer.commands._bootstrap_commands.apply_deploy_logic", return_value="")
    bc.bootstrap_toolchain_account(
        project_name="testing",
        principal_arns=["arn:aws:iam::123456789012:role/AdminRole"],
        permissions_boundary_arn=None,
        region_name="us-east-1",
        synthesize=True,
        as_target=False,
    )


@pytest.mark.commands
@pytest.mark.commands_bootstrap
@pytest.mark.parametrize("session", [boto3.Session()])
def test_bootstrap_toolchain_account_synth_with_qualifier(mocker, session):
    mocker.patch("seedfarmer.commands._bootstrap_commands.apply_deploy_logic", return_value="")
    bc.bootstrap_toolchain_account(
        project_name="testing",
        principal_arns=["arn:aws:iam::123456789012:role/AdminRole"],
        permissions_boundary_arn=None,
        region_name="us-east-1",
        qualifier="asdfgh",
        synthesize=True,
        as_target=False,
    )


@pytest.mark.commands
@pytest.mark.commands_bootstrap
@pytest.mark.parametrize("session", [boto3.Session()])
def test_bootstrap_toolchain_account_synth_with_qualifier_fail(mocker, session):
    mocker.patch("seedfarmer.commands._bootstrap_commands.apply_deploy_logic", return_value="")

    with pytest.raises(seedfarmer.errors.InvalidConfigurationError):
        bc.bootstrap_toolchain_account(
            project_name="testing",
            principal_arns=["arn:aws:iam::123456789012:role/AdminRole"],
            permissions_boundary_arn=None,
            region_name="us-east-1",
            qualifier="asdfghdd",
            synthesize=True,
            as_target=False,
        )


@pytest.mark.commands
@pytest.mark.commands_bootstrap
@pytest.mark.parametrize("session", [boto3.Session()])
def test_bootstrap_toolchain_account_synth_with_invalid_principal(mocker, session):
    mocker.patch("seedfarmer.commands._bootstrap_commands.apply_deploy_logic", return_value="")

    with pytest.raises(seedfarmer.errors.InvalidConfigurationError):
        bc.bootstrap_toolchain_account(
            project_name="testing",
            principal_arns=["arn:aws:iam::foobar:role/AdminRole"],
            permissions_boundary_arn=None,
            region_name="us-east-1",
            qualifier="asdfghdd",
            synthesize=True,
            as_target=False,
        )


@pytest.mark.commands
@pytest.mark.commands_bootstrap
@pytest.mark.parametrize("session", [boto3.Session()])
def test_bootstrap_toolchain_account_with_policies(mocker, session):
    mocker.patch("seedfarmer.commands._bootstrap_commands.apply_deploy_logic", return_value="")
    mocker.patch("seedfarmer.commands._bootstrap_commands.bootstrap_target_account", return_value="")
    mocker.patch(
        "seedfarmer.commands._bootstrap_commands.get_sts_identity_info",
        return_value=("1234566789012", "arn:aws", "aws"),
    )

    bc.bootstrap_toolchain_account(
        project_name="testing",
        principal_arns=["arn:aws:iam::123456789012:role/AdminRole"],
        policy_arns=["arn:aws:iam::aws:policy/AdministratorAccess", "arn:aws:iam::aws:policy/ReadOnlyAccess"],
        permissions_boundary_arn=None,
        region_name="us-east-1",
        synthesize=False,
        as_target=False,
    )


@pytest.mark.commands
@pytest.mark.commands_bootstrap
def test_bootstrap_toolchain_account_as_target(mocker):
    """Test bootstrap_toolchain_account with as_target=True."""
    # Mock apply_deploy_logic
    mock_apply = mocker.patch("seedfarmer.commands._bootstrap_commands.apply_deploy_logic")

    # Mock bootstrap_target_account
    mock_bootstrap_target = mocker.patch("seedfarmer.commands._bootstrap_commands.bootstrap_target_account")

    # Mock get_sts_identity_info
    mocker.patch(
        "seedfarmer.commands._bootstrap_commands.get_sts_identity_info",
        return_value=("123456789012", "arn:aws:iam::123456789012:role/test", "aws"),
    )

    # Call the function
    bc.bootstrap_toolchain_account(
        project_name="test-project",
        principal_arns=["arn:aws:iam::123456789012:role/AdminRole"],
        permissions_boundary_arn="arn:aws:iam::123456789012:policy/boundary",
        policy_arns=["arn:aws:iam::aws:policy/ReadOnlyAccess"],
        qualifier="test",
        role_prefix="/custom/",
        policy_prefix="/custom/",
        region_name="us-east-1",
        synthesize=False,
        as_target=True,
    )

    # Verify apply_deploy_logic was called
    mock_apply.assert_called_once()

    # Verify bootstrap_target_account was called with the correct parameters
    mock_bootstrap_target.assert_called_once()
    args, kwargs = mock_bootstrap_target.call_args
    assert kwargs["toolchain_account_id"] == "123456789012"
    assert kwargs["project_name"] == "test-project"
    assert kwargs["qualifier"] == "test"
    assert kwargs["role_prefix"] == "/custom/"
    assert kwargs["policy_prefix"] == "/custom/"
    assert kwargs["permissions_boundary_arn"] == "arn:aws:iam::123456789012:policy/boundary"
    assert kwargs["region_name"] == "us-east-1"
    assert kwargs["policy_arns"] == ["arn:aws:iam::aws:policy/ReadOnlyAccess"]


@pytest.mark.commands
@pytest.mark.commands_bootstrap
def test_bootstrap_toolchain_account_as_target_synthesize(mocker):
    """Test bootstrap_toolchain_account with as_target=True and synthesize=True."""
    # Mock write_template
    mock_write = mocker.patch("seedfarmer.commands._bootstrap_commands.write_template")

    # Mock bootstrap_target_account
    mock_bootstrap_target = mocker.patch("seedfarmer.commands._bootstrap_commands.bootstrap_target_account")

    # Call the function
    bc.bootstrap_toolchain_account(
        project_name="test-project",
        principal_arns=["arn:aws:iam::123456789012:role/AdminRole"],
        permissions_boundary_arn="arn:aws:iam::123456789012:policy/boundary",
        policy_arns=["arn:aws:iam::aws:policy/ReadOnlyAccess"],
        qualifier="test",
        role_prefix="/custom/",
        policy_prefix="/custom/",
        profile="default",
        region_name="us-east-1",
        synthesize=True,
        as_target=True,
    )

    # Verify write_template was called
    mock_write.assert_called_once()

    # Verify bootstrap_target_account was called with the correct parameters
    mock_bootstrap_target.assert_called_once()
    args, kwargs = mock_bootstrap_target.call_args
    assert kwargs["toolchain_account_id"] == "123456789012"
    assert kwargs["project_name"] == "test-project"
    assert kwargs["qualifier"] == "test"
    assert kwargs["permissions_boundary_arn"] == "arn:aws:iam::123456789012:policy/boundary"
    assert kwargs["policy_arns"] == ["arn:aws:iam::aws:policy/ReadOnlyAccess"]
    assert kwargs["profile"] == "default"
    assert kwargs["region_name"] == "us-east-1"
    assert kwargs["synthesize"] is True


@pytest.mark.commands
@pytest.mark.commands_bootstrap
@pytest.mark.parametrize("session", [boto3.Session()])
def test_bootstrap_target_account(mocker, session):
    mocker.patch("seedfarmer.commands._bootstrap_commands.apply_deploy_logic", return_value="")
    mocker.patch(
        "seedfarmer.commands._bootstrap_commands.get_sts_identity_info",
        return_value=("1234566789012", "arn:aws", "aws"),
    )

    bc.bootstrap_target_account(
        toolchain_account_id="123456789012",
        project_name="testing",
        permissions_boundary_arn=None,
        region_name="us-east-1",
        synthesize=False,
        session=session,
    )


@pytest.mark.commands
@pytest.mark.commands_bootstrap
@pytest.mark.parametrize("session", [boto3.Session()])
def test_bootstrap_target_account_with_qualifier(mocker, session):
    mocker.patch("seedfarmer.commands._bootstrap_commands.apply_deploy_logic", return_value="")
    mocker.patch(
        "seedfarmer.commands._bootstrap_commands.get_sts_identity_info",
        return_value=("1234566789012", "arn:aws", "aws"),
    )

    bc.bootstrap_target_account(
        toolchain_account_id="123456789012",
        project_name="testing",
        permissions_boundary_arn=None,
        region_name="us-east-1",
        qualifier="asdfgh",
        synthesize=False,
        session=session,
    )


@pytest.mark.commands
@pytest.mark.commands_bootstrap
@pytest.mark.parametrize("session", [boto3.Session()])
def test_bootstrap_target_account_with_qualifier_fail(mocker, session):
    mocker.patch("seedfarmer.commands._bootstrap_commands.apply_deploy_logic", return_value="")
    with pytest.raises(seedfarmer.errors.InvalidConfigurationError):
        bc.bootstrap_target_account(
            toolchain_account_id="123456789012",
            project_name="testing",
            permissions_boundary_arn=None,
            region_name="us-east-1",
            qualifier="asdfghsds",
            synthesize=False,
            session=session,
        )


@pytest.mark.commands
@pytest.mark.commands_bootstrap
@pytest.mark.parametrize("session", [boto3.Session()])
def test_bootstrap_target_account_with_policies(mocker, session):
    mocker.patch("seedfarmer.commands._bootstrap_commands.apply_deploy_logic", return_value="")
    mocker.patch(
        "seedfarmer.commands._bootstrap_commands.get_sts_identity_info",
        return_value=("1234566789012", "arn:aws", "aws"),
    )

    bc.bootstrap_target_account(
        toolchain_account_id="123456789012",
        project_name="testing",
        policy_arns=["arn:aws:iam::aws:policy/AdministratorAccess", "arn:aws:iam::aws:policy/ReadOnlyAccess"],
        permissions_boundary_arn=None,
        region_name="us-east-1",
        synthesize=False,
        session=session,
    )


@pytest.mark.commands
@pytest.mark.commands_bootstrap
def test_bootstrap_uppercase_project_name(mocker):
    """Test that bootstrap passes ProjectNameLower parameter for uppercase project names."""
    mock_apply = mocker.patch("seedfarmer.commands._bootstrap_commands.apply_deploy_logic", return_value="")
    mocker.patch("seedfarmer.commands._bootstrap_commands.bootstrap_target_account", return_value="")
    mocker.patch(
        "seedfarmer.commands._bootstrap_commands.get_sts_identity_info",
        return_value=("123456789012", "arn:aws:iam::123456789012:root", "aws"),
    )

    bc.bootstrap_toolchain_account(
        project_name="FalconProject",
        principal_arns=["arn:aws:iam::123456789012:root"],
        permissions_boundary_arn=None,
        region_name="us-east-1",
        synthesize=False,
        as_target=False,
    )

    # Verify apply_deploy_logic was called with ProjectNameLower in parameters
    assert mock_apply.called
    call_kwargs = mock_apply.call_args[1]
    parameters = call_kwargs["parameters"]
    assert parameters["ProjectName"] == "FalconProject"
    assert parameters["ProjectNameLower"] == "falconproject"
    assert parameters["RoleName"] == "seedfarmer-falconproject-toolchain-role"
