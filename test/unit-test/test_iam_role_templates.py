import os

import pytest
import yaml


@pytest.fixture
def toolchain_role_template():
    """Load the toolchain role CloudFormation template."""
    template_path = os.path.join(os.path.dirname(__file__), "../../seedfarmer/resources/toolchain_role.template")
    with open(template_path, "r") as f:
        return yaml.safe_load(f)


@pytest.fixture
def deployment_role_template():
    """Load the deployment role CloudFormation template."""
    template_path = os.path.join(os.path.dirname(__file__), "../../seedfarmer/resources/deployment_role.template")
    with open(template_path, "r") as f:
        return yaml.safe_load(f)


class TestToolchainRoleTemplate:
    """Test toolchain role template for least-privilege permissions."""

    def test_template_structure(self, toolchain_role_template):
        """Verify template has required structure."""
        assert "Resources" in toolchain_role_template
        assert "ToolchainRole" in toolchain_role_template["Resources"]
        assert toolchain_role_template["Resources"]["ToolchainRole"]["Type"] == "AWS::IAM::Role"

    def test_assume_role_policy(self, toolchain_role_template):
        """Verify assume role policy is properly scoped."""
        role = toolchain_role_template["Resources"]["ToolchainRole"]
        assume_policy = role["Properties"]["AssumeRolePolicyDocument"]

        assert assume_policy["Version"] == "2012-10-17"
        assert len(assume_policy["Statement"]) == 1

        statement = assume_policy["Statement"][0]
        assert statement["Effect"] == "Allow"
        assert statement["Action"] == "sts:AssumeRole"
        assert "Principal" in statement
        assert "AWS" in statement["Principal"]

    def test_sts_permissions_scoped(self, toolchain_role_template):
        """Verify STS permissions are scoped to project resources."""
        role = toolchain_role_template["Resources"]["ToolchainRole"]
        policies = role["Properties"]["Policies"]

        sts_statement = next(s for s in policies[0]["PolicyDocument"]["Statement"] if s.get("Sid") == "ToolChainSTS")

        assert sts_statement["Effect"] == "Allow"
        assert "sts:AssumeRole" in sts_statement["Action"]

        # Verify resources are scoped to project
        resources = sts_statement["Resource"]
        for resource in resources:
            resource_str = resource.get("Fn::Sub", "") if isinstance(resource, dict) else resource
            assert "seedfarmer-${ProjectName}" in resource_str

    def test_ssm_permissions_scoped(self, toolchain_role_template):
        """Verify SSM permissions are scoped to project parameters."""
        role = toolchain_role_template["Resources"]["ToolchainRole"]
        policies = role["Properties"]["Policies"]

        ssm_statement = next(s for s in policies[0]["PolicyDocument"]["Statement"] if s.get("Sid") == "ToolChainSSM")

        assert ssm_statement["Effect"] == "Allow"
        # Verify resource is scoped to project parameters
        assert ssm_statement["Resource"] == {
            "Fn::Sub": "arn:${AWS::Partition}:ssm:*:${AWS::AccountId}:parameter/${ProjectName}/*"
        }

    def test_secrets_manager_scoped(self, toolchain_role_template):
        """Verify Secrets Manager permissions are scoped."""
        role = toolchain_role_template["Resources"]["ToolchainRole"]
        policies = role["Properties"]["Policies"]

        secrets_statement = next(
            s for s in policies[0]["PolicyDocument"]["Statement"] if s.get("Sid") == "ToolChainSecretsManager"
        )

        assert secrets_statement["Effect"] == "Allow"
        assert "secretsmanager:GetSecretValue" in secrets_statement["Action"]
        # Verify only read permissions, no write
        assert "secretsmanager:CreateSecret" not in secrets_statement["Action"]
        assert "secretsmanager:PutSecretValue" not in secrets_statement["Action"]

    def test_s3_permissions_read_only(self, toolchain_role_template):
        """Verify S3 permissions are read-only and scoped."""
        role = toolchain_role_template["Resources"]["ToolchainRole"]
        policies = role["Properties"]["Policies"]

        s3_statement = next(s for s in policies[0]["PolicyDocument"]["Statement"] if s.get("Sid") == "ToolChainS3")

        assert s3_statement["Effect"] == "Allow"
        # Verify only read permissions
        assert all("GetObject" in action for action in s3_statement["Action"])
        # Verify no write permissions
        assert not any("Put" in str(s3_statement["Action"]) for _ in [1])
        assert not any("Delete" in str(s3_statement["Action"]) for _ in [1])

    def test_no_wildcard_resources(self, toolchain_role_template):
        """Verify no overly permissive wildcard resources except for describe operations."""
        role = toolchain_role_template["Resources"]["ToolchainRole"]
        policies = role["Properties"]["Policies"]

        for statement in policies[0]["PolicyDocument"]["Statement"]:
            if "Resource" in statement:
                resources = statement["Resource"]
                if isinstance(resources, str):
                    resources = [resources]
                elif isinstance(resources, dict):
                    resources = [resources]

                # Check if this is a describe-only statement
                actions = statement.get("Action", [])
                if isinstance(actions, str):
                    actions = [actions]
                is_describe_only = all("Describe" in action or "Get" in action for action in actions)

                # Only SSM/Secrets Manager describe operations should have account-level wildcard
                for resource in resources:
                    if isinstance(resource, dict):
                        resource_str = resource.get("Fn::Sub", "")
                    else:
                        resource_str = resource

                    # Skip describe-only statements which legitimately need broader access
                    if is_describe_only and ("ssm:" in str(actions) or "secretsmanager:" in str(actions)):
                        continue

                    # Ensure resources are scoped to project or specific patterns
                    assert "${ProjectName}" in resource_str or "archive-credentials" in resource_str, (
                        f"Resource not properly scoped: {resource_str}"
                    )


class TestDeploymentRoleTemplate:
    """Test deployment role template for least-privilege permissions."""

    def test_template_structure(self, deployment_role_template):
        """Verify template has required structure."""
        assert "Resources" in deployment_role_template
        assert "DeploymentRole" in deployment_role_template["Resources"]
        assert deployment_role_template["Resources"]["DeploymentRole"]["Type"] == "AWS::IAM::Role"

    def test_assume_role_policy_scoped(self, deployment_role_template):
        """Verify assume role policy only allows toolchain role."""
        role = deployment_role_template["Resources"]["DeploymentRole"]
        assume_policy = role["Properties"]["AssumeRolePolicyDocument"]

        assert assume_policy["Version"] == "2012-10-17"
        assert len(assume_policy["Statement"]) == 1

        statement = assume_policy["Statement"][0]
        assert statement["Effect"] == "Allow"
        assert statement["Action"] == "sts:AssumeRole"
        assert statement["Principal"]["AWS"] == {"Ref": "ToolchainRoleArn"}

    def test_iam_permissions_scoped(self, deployment_role_template):
        """Verify IAM permissions are scoped to project resources."""
        role = deployment_role_template["Resources"]["DeploymentRole"]
        policies = role["Properties"]["Policies"]

        iam_statement = next(s for s in policies[0]["PolicyDocument"]["Statement"] if s.get("Sid") == "DeploymentIAM")

        assert iam_statement["Effect"] == "Allow"
        # Verify all resources are scoped to project
        for resource in iam_statement["Resource"]:
            resource_str = resource.get("Fn::Sub", "") if isinstance(resource, dict) else resource
            assert (
                "${ProjectName}" in resource_str
                or "${ProjectNameLower}" in resource_str
                or "codeseeder-${ProjectName}" in resource_str
                or "codeseeder-${ProjectNameLower}" in resource_str
            )

    def test_iam_deny_user_management(self, deployment_role_template):
        """Verify IAM user management actions are explicitly denied."""
        role = deployment_role_template["Resources"]["DeploymentRole"]
        policies = role["Properties"]["Policies"]

        deny_statement = next(
            s for s in policies[0]["PolicyDocument"]["Statement"] if s.get("Sid") == "DeploymentIAMDeny"
        )

        assert deny_statement["Effect"] == "Deny"
        assert deny_statement["Resource"] == "*"

        # Verify dangerous actions are denied
        denied_actions = deny_statement["Action"]
        assert "iam:CreateAccessKey" in denied_actions
        assert "iam:CreateLoginProfile" in denied_actions
        assert "iam:AddUserToGroup" in denied_actions
        assert "iam:AttachUserPolicy" in denied_actions

    def test_kms_permissions_scoped(self, deployment_role_template):
        """Verify KMS permissions are scoped to project resources."""
        role = deployment_role_template["Resources"]["DeploymentRole"]
        policies = role["Properties"]["Policies"]

        kms_alias_statement = next(
            s for s in policies[0]["PolicyDocument"]["Statement"] if s.get("Sid") == "DeploymentKMSAlias"
        )

        # Verify alias operations are scoped to project
        for resource in kms_alias_statement["Resource"]:
            resource_str = resource.get("Fn::Sub", "") if isinstance(resource, dict) else resource
            assert "codeseeder-${ProjectName}" in resource_str or "codeseeder-${ProjectNameLower}" in resource_str

    def test_codebuild_permissions_scoped(self, deployment_role_template):
        """Verify CodeBuild permissions are scoped to project resources."""
        role = deployment_role_template["Resources"]["DeploymentRole"]
        policies = role["Properties"]["Policies"]

        codebuild_statement = next(
            s for s in policies[0]["PolicyDocument"]["Statement"] if s.get("Sid") == "DeploymentCodeBuild"
        )

        assert codebuild_statement["Effect"] == "Allow"
        resources = codebuild_statement["Resource"]
        if isinstance(resources, dict):
            resources = [resources]

        assert any(
            "codeseeder-${ProjectName}" in (r.get("Fn::Sub", "") if isinstance(r, dict) else r)
            or "codeseeder-${ProjectNameLower}" in (r.get("Fn::Sub", "") if isinstance(r, dict) else r)
            for r in resources
        )

    def test_s3_permissions_scoped(self, deployment_role_template):
        """Verify S3 permissions are scoped to project buckets."""
        role = deployment_role_template["Resources"]["DeploymentRole"]
        policies = role["Properties"]["Policies"]

        s3_statement = next(s for s in policies[0]["PolicyDocument"]["Statement"] if s.get("Sid") == "DeploymentS3")

        assert s3_statement["Effect"] == "Allow"
        # Verify all resources are scoped to project buckets
        for resource in s3_statement["Resource"]:
            resource_str = resource.get("Fn::Sub", "") if isinstance(resource, dict) else resource
            assert (
                "codeseeder-${ProjectName}" in resource_str
                or "codeseeder-${ProjectNameLower}" in resource_str
                or "seedfarmer-${ProjectName}" in resource_str
                or "seedfarmer-${ProjectNameLower}" in resource_str
            )

    def test_cloudformation_permissions_scoped(self, deployment_role_template):
        """Verify CloudFormation permissions are scoped to project stacks."""
        role = deployment_role_template["Resources"]["DeploymentRole"]
        policies = role["Properties"]["Policies"]

        cfn_statements = [
            s
            for s in policies[0]["PolicyDocument"]["Statement"]
            if "cloudformation" in str(s.get("Action", [])).lower()
        ]

        for statement in cfn_statements:
            if "Resource" in statement and statement["Resource"] != "*":
                for resource in statement["Resource"]:
                    resource_str = resource.get("Fn::Sub", "") if isinstance(resource, dict) else resource
                    # Verify stacks are scoped to project
                    assert (
                        "${ProjectName}" in resource_str
                        or "${ProjectNameLower}" in resource_str
                        or "codeseeder-${ProjectName}" in resource_str
                        or "codeseeder-${ProjectNameLower}" in resource_str
                        or "seedfarmer-${ProjectName}" in resource_str
                        or "seedfarmer-${ProjectNameLower}" in resource_str
                    )

    def test_ssm_permissions_scoped(self, deployment_role_template):
        """Verify SSM permissions are scoped to project parameters."""
        role = deployment_role_template["Resources"]["DeploymentRole"]
        policies = role["Properties"]["Policies"]

        ssm_statements = [
            s
            for s in policies[0]["PolicyDocument"]["Statement"]
            if "ssm:" in str(s.get("Action", [])).lower() and "Resource" in s and s["Resource"] != "*"
        ]

        for statement in ssm_statements:
            resource = statement["Resource"]
            resource_str = resource.get("Fn::Sub", "") if isinstance(resource, dict) else resource
            assert "parameter/${ProjectName}/" in resource_str

    def test_sts_permissions_scoped(self, deployment_role_template):
        """Verify STS permissions are scoped to project roles."""
        role = deployment_role_template["Resources"]["DeploymentRole"]
        policies = role["Properties"]["Policies"]

        sts_statement = next(s for s in policies[0]["PolicyDocument"]["Statement"] if s.get("Sid") == "DeploymentSTS")

        assert sts_statement["Effect"] == "Allow"
        # Verify resources are scoped to project roles
        for resource in sts_statement["Resource"]:
            resource_str = resource.get("Fn::Sub", "") if isinstance(resource, dict) else resource
            assert "${ProjectName}" in resource_str

    def test_no_admin_permissions(self, deployment_role_template):
        """Verify no administrator-level permissions are granted."""
        role = deployment_role_template["Resources"]["DeploymentRole"]
        policies = role["Properties"]["Policies"]

        for statement in policies[0]["PolicyDocument"]["Statement"]:
            actions = statement.get("Action", [])
            if isinstance(actions, str):
                actions = [actions]

            # Verify no wildcard actions
            for action in actions:
                assert action != "*", "Wildcard action '*' should not be used"
                # Verify no service-level wildcards except for safe operations
                if ":" in action and action.endswith(":*"):
                    service = action.split(":")[0]
                    # Allow wildcards for services that are scoped by resource
                    # cloudformation:* is scoped to project stacks
                    # codeartifact:* is scoped to project domain/repo
                    assert service in [
                        "codeartifact",
                        "cloudformation",
                    ], f"Service-level wildcard not allowed for {service}"
