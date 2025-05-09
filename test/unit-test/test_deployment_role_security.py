import os

import pytest
import yaml

from seedfarmer import CLI_ROOT
from seedfarmer.commands._bootstrap_commands import get_deployment_template


@pytest.mark.commands
@pytest.mark.commands_bootstrap
def test_deployment_role_deny_actions():
    """Test that the deployment role template includes the required deny actions for improved security posture."""
    
    # Get the deployment template using the same function the application uses
    template = get_deployment_template(
        toolchain_role_arn="arn:aws:iam::123456789012:role/test-role",
        project_name="test-project",
        role_name="test-deployment-role",
        policy_arns=None
    )
    
    # Expected deny actions that should be in the template
    expected_deny_actions = [
        "iam:CreateAccessKey",
        "iam:CreateLoginProfile",
        "iam:UpdateLoginProfile",
        "iam:AddUserToGroup",
        "iam:AttachGroupPolicy",
        "iam:AttachUserPolicy",
        "iam:CreatePolicyVersion",
        "iam:DeleteGroupPolicy",
        "iam:DeleteUserPolicy", 
        "iam:DetachGroupPolicy",
        "iam:DetachUserPolicy",
        "iam:PutGroupPolicy",
        "iam:PutUserPolicy",
        "iam:RemoveUserFromGroup",
        "iam:SetDefaultPolicyVersion"
    ]
    
    # Extract the policy statements from the template
    statements = template["Resources"]["DeploymentRole"]["Properties"]["Policies"][0]["PolicyDocument"]["Statement"]
    
    # Find the specific IAM deny statement
    deny_statement = None
    for statement in statements:
        if statement.get("Effect") == "Deny" and statement.get("Sid") == "DeploymentIAMDeny":
            deny_statement = statement
            break
    
    # Verify the deny statement exists
    assert deny_statement is not None, "DeploymentIAMDeny statement not found in template"
    
    # Verify the deny statement has the correct resource ('*')
    assert deny_statement["Resource"] == "*", "IAM deny statement should apply to all resources ('*')"
    
    # Verify all expected deny actions are included
    actions_set = set(deny_statement["Action"])
    for action in expected_deny_actions:
        assert action in actions_set, f"Required deny action {action} missing from template"
