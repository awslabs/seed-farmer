import os
from typing import Any, Dict

import pytest
import yaml


@pytest.fixture
def projectpolicy_template() -> Dict[str, Any]:
    """Load the project policy CloudFormation template."""
    template_path = os.path.join(os.path.dirname(__file__), "../../seedfarmer/resources/projectpolicy.yaml")
    with open(template_path, "r") as f:
        return yaml.safe_load(f)


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

        # Verify resources are scoped to project (lowercase — deployment roles are generated lowercase)
        resources = sts_statement["Resource"]
        for resource in resources:
            resource_str = resource.get("Fn::Sub", "") if isinstance(resource, dict) else resource
            assert "seedfarmer-${ProjectNameLower}" in resource_str

    def test_sts_permissions_cross_account_assume_exact_patterns(self, toolchain_role_template):
        """Verify ToolChainSTS supports cross-account assume-role using exact lowercase deployment-role patterns."""
        role = toolchain_role_template["Resources"]["ToolchainRole"]
        policies = role["Properties"]["Policies"]
        sts_statement = next(s for s in policies[0]["PolicyDocument"]["Statement"] if s.get("Sid") == "ToolChainSTS")

        resource_strs = [(r.get("Fn::Sub", "") if isinstance(r, dict) else r) for r in sts_statement["Resource"]]
        assert set(resource_strs) == {
            "arn:${AWS::Partition}:iam::*:role/seedfarmer-${ProjectNameLower}*",
            "arn:${AWS::Partition}:iam::*:role/*/seedfarmer-${ProjectNameLower}*",
        }
        # Cross-account assume is required (account wildcard), and deployment roles are lowercase
        assert all(":iam::*:" in r for r in resource_strs)
        assert not any("${ProjectName}" in r.replace("${ProjectNameLower}", "") for r in resource_strs)

    def test_ssm_permissions_scoped(self, toolchain_role_template):
        """Verify SSM permissions are scoped to project parameters."""
        role = toolchain_role_template["Resources"]["ToolchainRole"]
        policies = role["Properties"]["Policies"]

        ssm_statement = next(s for s in policies[0]["PolicyDocument"]["Statement"] if s.get("Sid") == "ToolChainSSM")

        assert ssm_statement["Effect"] == "Allow"
        # Verify resource is scoped to project parameters (lowercase — no SCP requirement for SSM)
        assert ssm_statement["Resource"] == {
            "Fn::Sub": "arn:${AWS::Partition}:ssm:*:${AWS::AccountId}:parameter/${ProjectNameLower}/*"
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
        assert "Put" not in str(s3_statement["Action"])
        assert "Delete" not in str(s3_statement["Action"])

    def test_s3_permissions_exact_project_prefixes(self, toolchain_role_template):
        """Verify ToolChainS3 reads only seedfarmer/codeseeder lowercase project buckets."""
        role = toolchain_role_template["Resources"]["ToolchainRole"]
        policies = role["Properties"]["Policies"]
        s3_statement = next(s for s in policies[0]["PolicyDocument"]["Statement"] if s.get("Sid") == "ToolChainS3")

        resource_strs = [(r.get("Fn::Sub", "") if isinstance(r, dict) else r) for r in s3_statement["Resource"]]
        assert set(resource_strs) == {
            "arn:${AWS::Partition}:s3:::seedfarmer-${ProjectNameLower}-*/*",
            "arn:${AWS::Partition}:s3:::codeseeder-${ProjectNameLower}-*/*",
        }
        # Guard against the old wrong prefix / wrong case pattern.
        assert not any(":::${ProjectName}-*/*" in r for r in resource_strs)

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
                    assert "${ProjectNameLower}" in resource_str or "archive-credentials" in resource_str, (
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
        # Verify all resources are scoped to project:
        # module IAM uses ${ProjectName} (preserve case for SCP), codeseeder IAM uses ${ProjectNameLower}
        for resource in iam_statement["Resource"]:
            resource_str = resource.get("Fn::Sub", "") if isinstance(resource, dict) else resource
            assert "${ProjectName}" in resource_str or "codeseeder-${ProjectNameLower}" in resource_str
        # Verify no dead cross-patterns exist
        resource_strs = [(r.get("Fn::Sub", "") if isinstance(r, dict) else r) for r in iam_statement["Resource"]]
        assert not any("${ProjectNameLower}-*" in r and "codeseeder" not in r for r in resource_strs)
        assert not any("codeseeder-${ProjectName}-*" in r for r in resource_strs)

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

    def test_kms_alias_permissions_exact_lowercase_resource(self, deployment_role_template):
        """Verify KMS alias permissions use a single lowercase codeseeder alias pattern."""
        role = deployment_role_template["Resources"]["DeploymentRole"]
        policies = role["Properties"]["Policies"]
        kms_alias_statement = next(
            s for s in policies[0]["PolicyDocument"]["Statement"] if s.get("Sid") == "DeploymentKMSAlias"
        )

        resource_strs = [(r.get("Fn::Sub", "") if isinstance(r, dict) else r) for r in kms_alias_statement["Resource"]]
        assert resource_strs == ["arn:${AWS::Partition}:kms:*:${AWS::AccountId}:alias/codeseeder-${ProjectNameLower}-*"]
        assert not any("${ProjectName}" in r.replace("${ProjectNameLower}", "") for r in resource_strs)

    def test_codebuild_permissions_exact_lowercase_resource(self, deployment_role_template):
        """Verify CodeBuild permissions use a single lowercase codeseeder project pattern."""
        role = deployment_role_template["Resources"]["DeploymentRole"]
        policies = role["Properties"]["Policies"]
        codebuild_statement = next(
            s for s in policies[0]["PolicyDocument"]["Statement"] if s.get("Sid") == "DeploymentCodeBuild"
        )

        resource_strs = [(r.get("Fn::Sub", "") if isinstance(r, dict) else r) for r in codebuild_statement["Resource"]]
        assert resource_strs == [
            "arn:${AWS::Partition}:codebuild:*:${AWS::AccountId}:project/codeseeder-${ProjectNameLower}*"
        ]
        assert not any("${ProjectName}" in r.replace("${ProjectNameLower}", "") for r in resource_strs)

    def test_s3_permissions_scoped(self, deployment_role_template):
        """Verify S3 permissions are scoped to project buckets."""
        role = deployment_role_template["Resources"]["DeploymentRole"]
        policies = role["Properties"]["Policies"]

        s3_statement = next(s for s in policies[0]["PolicyDocument"]["Statement"] if s.get("Sid") == "DeploymentS3")

        assert s3_statement["Effect"] == "Allow"
        # Verify all resources are scoped to project buckets (lowercase — S3 buckets are always lowercase)
        for resource in s3_statement["Resource"]:
            resource_str = resource.get("Fn::Sub", "") if isinstance(resource, dict) else resource
            assert "codeseeder-${ProjectNameLower}" in resource_str or "seedfarmer-${ProjectNameLower}" in resource_str

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
                    # Verify stacks are scoped to project (all CF stacks are lowercase)
                    assert "${ProjectNameLower}" in resource_str

    def test_cloudformation_create_execute_delete_exact_service_stack_patterns(self, deployment_role_template):
        """Verify CF create/execute/delete is restricted to lowercase service stacks (including aws-codeseeder)."""
        role = deployment_role_template["Resources"]["DeploymentRole"]
        policies = role["Properties"]["Policies"]

        cfn_mutation_stmt = next(
            s
            for s in policies[0]["PolicyDocument"]["Statement"]
            if set(s.get("Action", []))
            == {"cloudformation:Create*", "cloudformation:Execute*", "cloudformation:DeleteStack"}
        )

        resource_strs = [(r.get("Fn::Sub", "") if isinstance(r, dict) else r) for r in cfn_mutation_stmt["Resource"]]
        assert set(resource_strs) == {
            "arn:${AWS::Partition}:cloudformation:*:${AWS::AccountId}:stack/aws-codeseeder-${ProjectNameLower}*/*",
            "arn:${AWS::Partition}:cloudformation:*:${AWS::AccountId}:stack/seedfarmer-${ProjectNameLower}*/*",
        }
        assert not any("${ProjectName}" in r.replace("${ProjectNameLower}", "") for r in resource_strs)

    def test_cloudformation_wildcard_statement_exact_patterns(self, deployment_role_template):
        """Verify cloudformation:* statement uses lowercase-only module/service stack patterns."""
        role = deployment_role_template["Resources"]["DeploymentRole"]
        policies = role["Properties"]["Policies"]

        cfn_wildcard_stmt = next(
            s for s in policies[0]["PolicyDocument"]["Statement"] if s.get("Action") == ["cloudformation:*"]
        )
        resource_strs = [(r.get("Fn::Sub", "") if isinstance(r, dict) else r) for r in cfn_wildcard_stmt["Resource"]]
        assert set(resource_strs) == {
            "arn:${AWS::Partition}:cloudformation:*:${AWS::AccountId}:stack/${ProjectNameLower}-*",
            "arn:${AWS::Partition}:cloudformation:*:${AWS::AccountId}:stack/aws-codeseeder-${ProjectNameLower}/*",
            "arn:${AWS::Partition}:cloudformation:*:${AWS::AccountId}:stack/seedfarmer-${ProjectNameLower}/*",
        }
        assert not any("${ProjectName}" in r.replace("${ProjectNameLower}", "") for r in resource_strs)

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
            assert "parameter/${ProjectNameLower}/" in resource_str

    def test_ssm_permissions_exact_lowercase_resource(self, deployment_role_template):
        """Verify deployment SSM statement uses a single lowercase parameter path resource."""
        role = deployment_role_template["Resources"]["DeploymentRole"]
        policies = role["Properties"]["Policies"]

        ssm_stmt = next(
            s
            for s in policies[0]["PolicyDocument"]["Statement"]
            if "ssm:Put*" in s.get("Action", []) and s.get("Resource") != "*"
        )
        assert ssm_stmt["Resource"] == {
            "Fn::Sub": "arn:${AWS::Partition}:ssm:*:${AWS::AccountId}:parameter/${ProjectNameLower}/*"
        }

    def test_cloudwatch_logs_exact_lowercase_resource(self, deployment_role_template):
        """Verify CloudWatch log group resources use ${ProjectNameLower} only (1.2.7)."""
        role = deployment_role_template["Resources"]["DeploymentRole"]
        policies = role["Properties"]["Policies"]

        logs_stmt = next(
            s for s in policies[0]["PolicyDocument"]["Statement"] if "logs:PutLogEvents" in s.get("Action", [])
        )
        resources = logs_stmt["Resource"]
        if isinstance(resources, dict):
            resources = [resources]
        resource_strs = [r.get("Fn::Sub", r) if isinstance(r, dict) else r for r in resources]
        assert len(resource_strs) == 1
        assert resource_strs[0] == (
            "arn:${AWS::Partition}:logs:*:${AWS::AccountId}:log-group:/aws/codebuild/codeseeder-${ProjectNameLower}*"
        )
        # No preserve-case variant
        assert not any("codeseeder-${ProjectName}*" in r and "Lower" not in r for r in resource_strs)

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

    def test_sts_permissions_cross_account_assume_exact_patterns(self, deployment_role_template):
        """Verify DeploymentSTS supports cross-account assume-role for module roles (preserve-case project token)."""
        role = deployment_role_template["Resources"]["DeploymentRole"]
        policies = role["Properties"]["Policies"]
        sts_statement = next(s for s in policies[0]["PolicyDocument"]["Statement"] if s.get("Sid") == "DeploymentSTS")

        resource_strs = [(r.get("Fn::Sub", "") if isinstance(r, dict) else r) for r in sts_statement["Resource"]]
        assert set(resource_strs) == {
            "arn:${AWS::Partition}:iam::*:role/${ProjectName}-*",
            "arn:${AWS::Partition}:iam::*:role/*/${ProjectName}-*",
        }
        assert all(":iam::*:" in r for r in resource_strs)
        assert not any("${ProjectNameLower}" in r for r in resource_strs)

    def test_codeartifact_permissions_exact_lowercase_resources(self, deployment_role_template):
        """Verify CodeArtifact resources are scoped to lowercase aws-codeseeder domain/repo names."""
        role = deployment_role_template["Resources"]["DeploymentRole"]
        policies = role["Properties"]["Policies"]

        codeartifact_stmt = next(
            s for s in policies[0]["PolicyDocument"]["Statement"] if s.get("Action") == ["codeartifact:*"]
        )
        resource_strs = [(r.get("Fn::Sub", "") if isinstance(r, dict) else r) for r in codeartifact_stmt["Resource"]]
        assert set(resource_strs) == {
            "arn:${AWS::Partition}:codeartifact:*:${AWS::AccountId}:domain/aws-codeseeder-${ProjectNameLower}",
            "arn:${AWS::Partition}:codeartifact:*:${AWS::AccountId}:repository/aws-codeseeder-${ProjectNameLower}*",
        }
        assert not any("${ProjectName}" in r.replace("${ProjectNameLower}", "") for r in resource_strs)

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


class TestProjectPolicyTemplate:
    """Test projectpolicy.yaml for correct case tokens after Phase 1 cleanup."""

    def _statements(self, projectpolicy_template: Dict[str, Any]):
        return projectpolicy_template["Resources"]["ProjectPolicy"]["Properties"]["PolicyDocument"]["Statement"]

    def test_template_structure(self, projectpolicy_template):
        """Verify template has required structure."""
        assert "Resources" in projectpolicy_template
        assert "ProjectPolicy" in projectpolicy_template["Resources"]
        assert projectpolicy_template["Resources"]["ProjectPolicy"]["Type"] == "AWS::IAM::ManagedPolicy"

    def test_managed_policy_name_uses_preserve_case(self, projectpolicy_template):
        """ManagedPolicyName uses ${ProjectName} so it matches policy/${ProjectName}-* in deployment role."""
        props = projectpolicy_template["Resources"]["ProjectPolicy"]["Properties"]
        assert "ManagedPolicyName" in props
        name_sub = props["ManagedPolicyName"]["Fn::Sub"]
        assert "${ProjectName}-managed-policy" == name_sub

    def test_ssm_uses_lowercase_only(self, projectpolicy_template):
        """SSM resources use ${ProjectNameLower} — no SCP requirement, lowercase for consistency."""
        stmts = self._statements(projectpolicy_template)
        ssm_stmt = next(
            s for s in stmts if "ssm:PutParameter" in s.get("Action", []) or "ssm:Get*" in s.get("Action", [])
        )
        resources = ssm_stmt["Resource"]
        resource_strs = [r.get("Fn::Sub", r) if isinstance(r, dict) else r for r in resources]
        for r in resource_strs:
            assert "${ProjectNameLower}" in r, f"SSM resource should use ProjectNameLower: {r}"
            assert "${ProjectName}" not in r.replace("${ProjectNameLower}", ""), (
                f"SSM resource has dead preserve-case entry: {r}"
            )

    def test_logs_uses_lowercase_only(self, projectpolicy_template):
        """Log group resources use ${ProjectNameLower} — log groups are always lowercase."""
        stmts = self._statements(projectpolicy_template)
        logs_stmt = next(s for s in stmts if "logs:PutLogEvents" in s.get("Action", []))
        resources = logs_stmt["Resource"]
        resource_strs = [r.get("Fn::Sub", r) if isinstance(r, dict) else r for r in resources]
        for r in resource_strs:
            assert "${ProjectNameLower}" in r, f"Logs resource should use ProjectNameLower: {r}"
            assert "${ProjectName}" not in r.replace("${ProjectNameLower}", ""), (
                f"Logs resource has dead preserve-case entry: {r}"
            )

    def test_iam_update_assume_role_uses_preserve_case(self, projectpolicy_template):
        """iam:UpdateAssumeRolePolicy uses ${ProjectName} — module roles preserve case for SCP."""
        stmts = self._statements(projectpolicy_template)
        iam_stmt = next(s for s in stmts if "iam:UpdateAssumeRolePolicy" in s.get("Action", []))
        resources = iam_stmt["Resource"]
        resource_strs = [r.get("Fn::Sub", r) if isinstance(r, dict) else r for r in resources]
        assert len(resource_strs) == 1, "UpdateAssumeRolePolicy should have exactly one resource entry"
        assert "${ProjectName}" in resource_strs[0]
        # Verify no duplicate lowercase variant
        assert "${ProjectNameLower}" not in resource_strs[0]

    def test_s3_uses_lowercase_only(self, projectpolicy_template):
        """S3 resources use ${ProjectNameLower} — S3 buckets are always lowercase."""
        stmts = self._statements(projectpolicy_template)
        s3_stmt = next(s for s in stmts if "s3:Put*" in s.get("Action", []))
        resources = s3_stmt["Resource"]
        resource_strs = [r.get("Fn::Sub", r) if isinstance(r, dict) else r for r in resources]
        for r in resource_strs:
            assert "${ProjectNameLower}" in r, f"S3 resource should use ProjectNameLower: {r}"
            assert "${ProjectName}" not in r.replace("${ProjectNameLower}", ""), (
                f"S3 resource has dead preserve-case entry: {r}"
            )
        # Verify no duplicate preserve-case variants remain (was 4 entries, now 2)
        assert len(resource_strs) == 2
