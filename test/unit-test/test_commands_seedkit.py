import os

import pytest
from moto import mock_aws

import seedfarmer.commands._seedkit_commands as sc
from seedfarmer.services._service_utils import boto3_client


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


@pytest.mark.commands
@pytest.mark.commands_seedkit
def test_seedkit_deployed(mocker):
    """Test the seedkit_deployed function."""
    # Mock the CloudFormation stack existence check
    mocker.patch(
        "seedfarmer.services._cfn.does_stack_exist",
        return_value=(True, {"Bucket": "test-bucket", "DeployId": "abc123"}),
    )

    # Call the function
    exists, stack_name, outputs = sc.seedkit_deployed("test-seedkit")

    # Verify the results
    assert exists is True
    assert stack_name == "aws-codeseeder-test-seedkit"
    assert outputs == {"Bucket": "test-bucket", "DeployId": "abc123"}


@pytest.mark.commands
@pytest.mark.commands_seedkit
def test_deploy_seedkit_existing(mocker):
    """Test deploying a seedkit that already exists."""
    # Mock the seedkit_deployed function
    mocker.patch(
        "seedfarmer.commands._seedkit_commands.seedkit_deployed",
        return_value=(True, "seedkit-test-stack", {"DeployId": "abc123"}),
    )

    # Mock the synth function
    mocker.patch("seedfarmer.commands._cfn_seedkit.synth", return_value="/tmp/template.yaml")

    # Mock the deploy_template function
    mock_deploy = mocker.patch("seedfarmer.services._cfn.deploy_template")

    # Call the function
    sc.deploy_seedkit(
        seedkit_name="test-seedkit",
        managed_policy_arns=["arn:aws:iam::aws:policy/ReadOnlyAccess"],
        deploy_codeartifact=True,
    )

    # Verify the deploy_template was called with correct parameters
    mock_deploy.assert_called_once()
    args, kwargs = mock_deploy.call_args
    assert kwargs["stack_name"] == "seedkit-test-stack"
    assert kwargs["filename"] == "/tmp/template.yaml"
    assert kwargs["seedkit_tag"] == "codeseeder-test-seedkit"

    # Verify parameters dictionary contains expected values
    parameters = kwargs["parameters"]
    assert parameters["SeedkitName"] == "test-seedkit"
    assert parameters["DeployId"] == "abc123"
    assert parameters["DeployCodeArtifact"] == "true"
    assert parameters["ManagedPolicyArns"] == "arn:aws:iam::aws:policy/ReadOnlyAccess"


@pytest.mark.commands
@pytest.mark.commands_seedkit
def test_deploy_seedkit_new(mocker):
    """Test deploying a new seedkit."""
    # Mock the seedkit_deployed function
    mocker.patch(
        "seedfarmer.commands._seedkit_commands.seedkit_deployed", return_value=(False, "seedkit-test-stack", {})
    )

    # Mock the synth function
    mocker.patch("seedfarmer.commands._cfn_seedkit.synth", return_value="/tmp/template.yaml")

    # Mock random.choice to return predictable values
    mocker.patch("random.choice", side_effect=lambda x: x[0])

    # Mock the deploy_template function
    mock_deploy = mocker.patch("seedfarmer.services._cfn.deploy_template")

    # Call the function
    sc.deploy_seedkit(
        seedkit_name="test-seedkit",
        vpc_id="vpc-12345",
        subnet_ids=["subnet-1", "subnet-2"],
        security_group_ids=["sg-1", "sg-2"],
        permissions_boundary_arn="arn:aws:iam::123456789012:policy/boundary",
    )

    # Verify the deploy_template was called with correct parameters
    mock_deploy.assert_called_once()
    args, kwargs = mock_deploy.call_args

    # Verify parameters dictionary contains expected values
    parameters = kwargs["parameters"]
    assert parameters["SeedkitName"] == "test-seedkit"
    assert len(parameters["DeployId"]) == 6  # Random ID should be 6 chars
    assert parameters["DeployCodeArtifact"] == "false"
    assert parameters["VpcId"] == "vpc-12345"
    assert parameters["SubnetIds"] == "subnet-1,subnet-2"
    assert parameters["SecurityGroupIds"] == "sg-1,sg-2"
    assert parameters["PermissionsBoundaryArn"] == "arn:aws:iam::123456789012:policy/boundary"


@pytest.mark.commands
@pytest.mark.commands_seedkit
def test_deploy_seedkit_synthesize(mocker):
    """Test synthesizing a seedkit template without deploying."""
    # Mock the seedkit_deployed function
    mocker.patch(
        "seedfarmer.commands._seedkit_commands.seedkit_deployed", return_value=(False, "seedkit-test-stack", {})
    )

    # Mock the synth function
    mock_synth = mocker.patch("seedfarmer.commands._cfn_seedkit.synth", return_value=None)

    # Mock the deploy_template function
    mock_deploy = mocker.patch("seedfarmer.services._cfn.deploy_template")

    # Call the function
    sc.deploy_seedkit(seedkit_name="test-seedkit", synthesize=True)

    # Verify synth was called with synthesize=True
    mock_synth.assert_called_once()
    args, kwargs = mock_synth.call_args
    assert kwargs["synthesize"] is True

    # Verify deploy_template was not called
    mock_deploy.assert_not_called()


@pytest.mark.commands
@pytest.mark.commands_seedkit
def test_destroy_seedkit_existing(mocker):
    """Test destroying an existing seedkit."""
    # Mock the seedkit_deployed function
    mocker.patch(
        "seedfarmer.commands._seedkit_commands.seedkit_deployed",
        return_value=(True, "seedkit-test-stack", {"Bucket": "test-bucket"}),
    )

    # Mock the S3 bucket deletion
    mock_delete_bucket = mocker.patch("seedfarmer.services._s3.delete_bucket")

    # Mock the CloudFormation stack deletion
    mock_destroy_stack = mocker.patch("seedfarmer.services._cfn.destroy_stack")

    # Call the function
    sc.destroy_seedkit("test-seedkit")

    # Verify the bucket was deleted
    mock_delete_bucket.assert_called_once_with(bucket="test-bucket", session=None)

    # Verify the stack was destroyed
    mock_destroy_stack.assert_called_once_with(stack_name="seedkit-test-stack", session=None)


@pytest.mark.commands
@pytest.mark.commands_seedkit
def test_destroy_seedkit_nonexistent(mocker):
    """Test attempting to destroy a non-existent seedkit."""
    # Mock the seedkit_deployed function
    mocker.patch(
        "seedfarmer.commands._seedkit_commands.seedkit_deployed", return_value=(False, "seedkit-test-stack", {})
    )

    # Mock the S3 bucket deletion
    mock_delete_bucket = mocker.patch("seedfarmer.services._s3.delete_bucket")

    # Mock the CloudFormation stack deletion
    mock_destroy_stack = mocker.patch("seedfarmer.services._cfn.destroy_stack")

    # Call the function
    sc.destroy_seedkit("test-seedkit")

    # Verify neither the bucket nor stack were deleted
    mock_delete_bucket.assert_not_called()
    mock_destroy_stack.assert_not_called()


@pytest.mark.commands
@pytest.mark.commands_seedkit
def test_deploy_seedkit_uppercase_name(mocker):
    """Test deploying a seedkit with uppercase name - should be lowercased."""
    # Mock the seedkit_deployed function
    mocker.patch(
        "seedfarmer.commands._seedkit_commands.seedkit_deployed", return_value=(False, "seedkit-test-stack", {})
    )

    # Mock the synth function
    mocker.patch("seedfarmer.commands._cfn_seedkit.synth", return_value="/tmp/template.yaml")

    # Mock the deploy_template function
    mock_deploy = mocker.patch("seedfarmer.services._cfn.deploy_template")

    # Call the function with uppercase seedkit name
    sc.deploy_seedkit(seedkit_name="TEST-SeedKit")

    # Verify the deploy_template was called
    mock_deploy.assert_called_once()
    args, kwargs = mock_deploy.call_args

    # Verify SeedkitName parameter is lowercased
    parameters = kwargs["parameters"]
    assert parameters["SeedkitName"] == "test-seedkit", "SeedkitName should be lowercased for valid S3 bucket names"


@pytest.mark.commands
@pytest.mark.commands_seedkit
def test_deploy_seedkit_mixed_case_name(mocker):
    """Test deploying a seedkit with mixed case name - should be lowercased."""
    mocker.patch(
        "seedfarmer.commands._seedkit_commands.seedkit_deployed", return_value=(False, "seedkit-test-stack", {})
    )
    mocker.patch("seedfarmer.commands._cfn_seedkit.synth", return_value="/tmp/template.yaml")
    mock_deploy = mocker.patch("seedfarmer.services._cfn.deploy_template")

    sc.deploy_seedkit(seedkit_name="MiXeD-CaSe")

    mock_deploy.assert_called_once()
    parameters = mock_deploy.call_args[1]["parameters"]
    assert parameters["SeedkitName"] == "mixed-case"


@pytest.mark.commands
@pytest.mark.commands_seedkit
def test_deploy_seedkit_name_with_numbers(mocker):
    """Test deploying a seedkit with numbers in name - should be lowercased."""
    mocker.patch(
        "seedfarmer.commands._seedkit_commands.seedkit_deployed", return_value=(False, "seedkit-test-stack", {})
    )
    mocker.patch("seedfarmer.commands._cfn_seedkit.synth", return_value="/tmp/template.yaml")
    mock_deploy = mocker.patch("seedfarmer.services._cfn.deploy_template")

    sc.deploy_seedkit(seedkit_name="Project123-Test456")

    mock_deploy.assert_called_once()
    parameters = mock_deploy.call_args[1]["parameters"]
    assert parameters["SeedkitName"] == "project123-test456"
