from seedfarmer.input_validators import InputValidator


class TestQualifierValidation:
    """Test qualifier validation."""

    def test_valid_qualifier(self):
        valid, error = InputValidator.validate_qualifier("abc123")
        assert valid is True
        assert error is None

    def test_qualifier_too_long(self):
        valid, error = InputValidator.validate_qualifier("abcdefg")
        assert valid is False
        assert "6 characters or less" in error

    def test_qualifier_non_alphanumeric(self):
        valid, error = InputValidator.validate_qualifier("abc-12")
        assert valid is False
        assert "alphanumeric" in error

    def test_empty_qualifier(self):
        valid, error = InputValidator.validate_qualifier("")
        assert valid is True
        assert error is None


class TestRolePrefixValidation:
    """Test role prefix validation."""

    def test_valid_role_prefix(self):
        valid, error = InputValidator.validate_role_prefix("/custom/path/")
        assert valid is True
        assert error is None

    def test_role_prefix_no_leading_slash(self):
        valid, error = InputValidator.validate_role_prefix("custom/path/")
        assert valid is False
        assert "must start with '/'" in error

    def test_role_prefix_no_trailing_slash(self):
        valid, error = InputValidator.validate_role_prefix("/custom/path")
        assert valid is False
        assert "must end with '/'" in error

    def test_role_prefix_invalid_chars(self):
        valid, error = InputValidator.validate_role_prefix("/custom/path!/")
        assert valid is False
        assert "invalid characters" in error

    def test_role_prefix_too_long(self):
        long_prefix = "/" + "a" * 511 + "/"
        valid, error = InputValidator.validate_role_prefix(long_prefix)
        assert valid is False
        assert "512 characters or less" in error

    def test_empty_role_prefix(self):
        valid, error = InputValidator.validate_role_prefix("")
        assert valid is True
        assert error is None

    def test_root_path(self):
        valid, error = InputValidator.validate_role_prefix("/")
        assert valid is True
        assert error is None


class TestPolicyPrefixValidation:
    """Test policy prefix validation."""

    def test_valid_policy_prefix(self):
        valid, error = InputValidator.validate_policy_prefix("/policy/path/")
        assert valid is True
        assert error is None

    def test_policy_prefix_same_rules_as_role(self):
        valid, error = InputValidator.validate_policy_prefix("invalid")
        assert valid is False


class TestProjectNameValidation:
    """Test project name validation."""

    def test_valid_project_name(self):
        valid, error = InputValidator.validate_project_name("my-project-123")
        assert valid is True
        assert error is None

    def test_project_name_too_long(self):
        long_name = "a" * 36
        valid, error = InputValidator.validate_project_name(long_name)
        assert valid is False
        assert "35 characters or less" in error

    def test_project_name_invalid_chars(self):
        valid, error = InputValidator.validate_project_name("my%project")
        assert valid is False
        assert "contains invalid characters" in error

    def test_project_name_starts_with_hyphen(self):
        valid, error = InputValidator.validate_project_name("-myproject")
        assert valid is False
        assert "cannot start or end with a hyphen" in error

    def test_project_name_ends_with_hyphen(self):
        valid, error = InputValidator.validate_project_name("myproject-")
        assert valid is False
        assert "cannot start or end with a hyphen" in error

    def test_empty_project_name(self):
        valid, error = InputValidator.validate_project_name("")
        assert valid is False
        assert "cannot be empty" in error


class TestDeploymentNameValidation:
    """Test deployment name validation."""

    def test_valid_deployment_name(self):
        valid, error = InputValidator.validate_deployment_name("my-deployment")
        assert valid is True
        assert error is None

    def test_deployment_name_too_long(self):
        long_name = "a" * 65
        valid, error = InputValidator.validate_deployment_name(long_name)
        assert valid is False
        assert "64 characters or less" in error

    def test_empty_deployment_name(self):
        valid, error = InputValidator.validate_deployment_name("")
        assert valid is False
        assert "cannot be empty" in error


class TestGroupNameValidation:
    """Test group name validation."""

    def test_valid_group_name(self):
        valid, error = InputValidator.validate_group_name("my-group")
        assert valid is True
        assert error is None

    def test_group_name_too_long(self):
        long_name = "a" * 65
        valid, error = InputValidator.validate_group_name(long_name)
        assert valid is False
        assert "64 characters or less" in error

    def test_empty_group_name(self):
        valid, error = InputValidator.validate_group_name("")
        assert valid is False
        assert "cannot be empty" in error


class TestModuleNameValidation:
    """Test module name validation."""

    def test_valid_module_name(self):
        valid, error = InputValidator.validate_module_name("my-module")
        assert valid is True
        assert error is None

    def test_module_name_too_long(self):
        long_name = "a" * 65
        valid, error = InputValidator.validate_module_name(long_name)
        assert valid is False
        assert "64 characters or less" in error

    def test_empty_module_name(self):
        valid, error = InputValidator.validate_module_name("")
        assert valid is False
        assert "cannot be empty" in error


class TestArnValidation:
    """Test ARN validation."""

    def test_valid_arn(self):
        valid, error = InputValidator.validate_arn("arn:aws:iam::123456789012:role/MyRole")
        assert valid is True
        assert error is None

    def test_valid_arn_with_partition(self):
        valid, error = InputValidator.validate_arn("arn:aws-us-gov:iam::123456789012:role/MyRole")
        assert valid is True
        assert error is None

    def test_valid_aws_managed_policy(self):
        valid, error = InputValidator.validate_arn("arn:aws:iam::aws:policy/AdministratorAccess")
        assert valid is True
        assert error is None

    def test_valid_arn_with_wildcard(self):
        valid, error = InputValidator.validate_arn("arn:aws:iam::*:role/MyRole")
        assert valid is True
        assert error is None

    def test_invalid_arn_format(self):
        valid, error = InputValidator.validate_arn("not-an-arn")
        assert valid is False
        assert "Invalid ARN format" in error

    def test_empty_arn(self):
        valid, error = InputValidator.validate_arn("")
        assert valid is False
        assert "cannot be empty" in error


class TestSessionTimeoutValidation:
    """Test session timeout validation."""

    def test_valid_timeout(self):
        valid, error = InputValidator.validate_session_timeout(900)
        assert valid is True
        assert error is None

    def test_timeout_too_small(self):
        valid, error = InputValidator.validate_session_timeout(30)
        assert valid is False
        assert "at least 60 seconds" in error

    def test_timeout_negative(self):
        valid, error = InputValidator.validate_session_timeout(-1)
        assert valid is False
        assert "positive integer" in error

    def test_timeout_too_large(self):
        valid, error = InputValidator.validate_session_timeout(50000)
        assert valid is False
        assert "43200 seconds" in error


class TestRoleNameLengthValidation:
    """Test role name length validation."""

    def test_valid_role_name_length(self):
        valid, error = InputValidator.validate_role_name_length("myproject", "abc")
        assert valid is True
        assert error is None

    def test_role_name_too_long(self):
        long_project = "a" * 50
        valid, error = InputValidator.validate_role_name_length(long_project, "abc123")
        assert valid is False
        assert "exceeding IAM limit" in error

    def test_role_name_without_qualifier(self):
        valid, error = InputValidator.validate_role_name_length("myproject")
        assert valid is True
        assert error is None
