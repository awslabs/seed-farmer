import pytest

from seedfarmer.input_validators import InputValidator


class TestQualifierValidation:
    """Test qualifier validation."""

    def test_valid_qualifier(self):
        # Should not raise
        InputValidator.validate_qualifier("abc123")

    def test_qualifier_too_long(self):
        with pytest.raises(ValueError, match=r"6 characters or less"):
            InputValidator.validate_qualifier("abcdefg")

    def test_qualifier_non_alphanumeric(self):
        with pytest.raises(ValueError, match=r"alphanumeric"):
            InputValidator.validate_qualifier("abc-12")

    def test_empty_qualifier(self):
        # Should not raise
        InputValidator.validate_qualifier("")


class TestRolePrefixValidation:
    """Test role prefix validation."""

    def test_valid_role_prefix(self):
        # Should not raise
        InputValidator.validate_role_prefix("/custom/path/")

    def test_role_prefix_no_leading_slash(self):
        with pytest.raises(ValueError, match=r"must start with '/'"):
            InputValidator.validate_role_prefix("custom/path/")

    def test_role_prefix_no_trailing_slash(self):
        with pytest.raises(ValueError, match=r"must end with '/'"):
            InputValidator.validate_role_prefix("/custom/path")

    def test_role_prefix_invalid_chars(self):
        with pytest.raises(ValueError, match=r"invalid characters"):
            InputValidator.validate_role_prefix("/custom/path!/")

    def test_role_prefix_too_long(self):
        long_prefix = "/" + "a" * 511 + "/"
        with pytest.raises(ValueError, match=r"512 characters or less"):
            InputValidator.validate_role_prefix(long_prefix)

    def test_empty_role_prefix(self):
        # Should not raise
        InputValidator.validate_role_prefix("")

    def test_root_path(self):
        # Should not raise
        InputValidator.validate_role_prefix("/")


class TestPolicyPrefixValidation:
    """Test policy prefix validation."""

    def test_valid_policy_prefix(self):
        # Should not raise
        InputValidator.validate_policy_prefix("/policy/path/")

    def test_policy_prefix_same_rules_as_role(self):
        with pytest.raises(ValueError, match=r"must start with '/'"):
            InputValidator.validate_policy_prefix("invalid")


class TestProjectNameValidation:
    """Test project name validation."""

    def test_valid_project_name(self):
        # Should not raise
        InputValidator.validate_project_name("my-project-123")

    def test_project_name_too_long(self):
        long_name = "a" * 36
        with pytest.raises(ValueError, match=r"35 characters or less"):
            InputValidator.validate_project_name(long_name)

    def test_project_name_invalid_chars(self):
        with pytest.raises(ValueError, match=r"contains invalid characters"):
            InputValidator.validate_project_name("my%project")

    def test_project_name_starts_with_hyphen(self):
        with pytest.raises(ValueError, match=r"cannot start or end with a hyphen"):
            InputValidator.validate_project_name("-myproject")

    def test_project_name_ends_with_hyphen(self):
        with pytest.raises(ValueError, match=r"cannot start or end with a hyphen"):
            InputValidator.validate_project_name("myproject-")

    def test_empty_project_name(self):
        with pytest.raises(ValueError, match=r"cannot be empty"):
            InputValidator.validate_project_name("")


class TestDeploymentNameValidation:
    """Test deployment name validation."""

    def test_valid_deployment_name(self):
        # Should not raise
        InputValidator.validate_deployment_name("my-deployment")

    def test_deployment_name_too_long(self):
        long_name = "a" * 65
        with pytest.raises(ValueError, match=r"64 characters or less"):
            InputValidator.validate_deployment_name(long_name)

    def test_empty_deployment_name(self):
        with pytest.raises(ValueError, match=r"cannot be empty"):
            InputValidator.validate_deployment_name("")


class TestGroupNameValidation:
    """Test group name validation."""

    def test_valid_group_name(self):
        # Should not raise
        InputValidator.validate_group_name("my-group")

    def test_group_name_too_long(self):
        long_name = "a" * 65
        with pytest.raises(ValueError, match=r"64 characters or less"):
            InputValidator.validate_group_name(long_name)

    def test_empty_group_name(self):
        with pytest.raises(ValueError, match=r"cannot be empty"):
            InputValidator.validate_group_name("")


class TestModuleNameValidation:
    """Test module name validation."""

    def test_valid_module_name(self):
        # Should not raise
        InputValidator.validate_module_name("my-module")

    def test_module_name_too_long(self):
        long_name = "a" * 65
        with pytest.raises(ValueError, match=r"64 characters or less"):
            InputValidator.validate_module_name(long_name)

    def test_empty_module_name(self):
        with pytest.raises(ValueError, match=r"cannot be empty"):
            InputValidator.validate_module_name("")


class TestArnValidation:
    """Test ARN validation."""

    def test_valid_arn(self):
        # Should not raise
        InputValidator.validate_arn("arn:aws:iam::123456789012:role/MyRole")

    def test_valid_arn_with_partition(self):
        # Should not raise
        InputValidator.validate_arn("arn:aws-us-gov:iam::123456789012:role/MyRole")

    def test_valid_aws_managed_policy(self):
        # Should not raise
        InputValidator.validate_arn("arn:aws:iam::aws:policy/AdministratorAccess")

    def test_valid_arn_with_wildcard(self):
        # Should not raise
        InputValidator.validate_arn("arn:aws:iam::*:role/MyRole")

    def test_invalid_arn_format(self):
        with pytest.raises(ValueError, match=r"Invalid ARN format"):
            InputValidator.validate_arn("not-an-arn")

    def test_empty_arn(self):
        with pytest.raises(ValueError, match=r"cannot be empty"):
            InputValidator.validate_arn("")


class TestSessionTimeoutValidation:
    """Test session timeout validation."""

    def test_valid_timeout(self):
        # Should not raise
        InputValidator.validate_session_timeout(900)

    def test_timeout_too_small(self):
        with pytest.raises(ValueError, match=r"at least 60 seconds"):
            InputValidator.validate_session_timeout(30)

    def test_timeout_negative(self):
        with pytest.raises(ValueError, match=r"at least 60 seconds"):
            InputValidator.validate_session_timeout(-1)

    def test_timeout_too_large(self):
        with pytest.raises(ValueError, match=r"43200 seconds"):
            InputValidator.validate_session_timeout(50000)


class TestRoleNameLengthValidation:
    """Test role name length validation."""

    def test_valid_role_name_length(self):
        # Should not raise
        InputValidator.validate_role_name_length("myproject", "abc")

    def test_role_name_too_long(self):
        long_project = "a" * 50
        with pytest.raises(ValueError, match=r"exceeding IAM limit"):
            InputValidator.validate_role_name_length(long_project, "abc123")

    def test_role_name_without_qualifier(self):
        # Should not raise
        InputValidator.validate_role_name_length("myproject")
