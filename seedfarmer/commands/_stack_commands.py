#    Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License").
#    You may not use this file except in compliance with the License.
#    You may obtain a copy of the License at
#
#        http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS,
#    WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#    See the License for the specific language governing permissions and
#    limitations under the License.

import json
import logging
import os
import time
from typing import List, Optional

from aws_codeseeder import codeseeder, commands, services
from cfn_tools import load_yaml

import seedfarmer.services._iam as iam
from seedfarmer import OPS_ROOT, PROJECT
from seedfarmer.mgmt.module_info import _get_module_stack_names
from seedfarmer.models.manifests import DeploymentManifest, ModuleParameter
from seedfarmer.services._service_utils import get_account_id, get_region
from seedfarmer.utils import upper_snake_case

PROJECT_MANAGED_POLICY_CFN_NAME = f"{PROJECT.lower()}-managed-policy"
PROJECT_POLICY_PATH = "resources/projectpolicy.yaml"

ACCOUNT_ID = get_account_id()
REGION = get_region()

_logger: logging.Logger = logging.getLogger(__name__)


def deploy_managed_policy_stack(deployment_name: str, deployment_manifest: DeploymentManifest) -> None:
    """
    deploy_managed_policy_stack
        This function deployes the deployment-specific policy to allow CodeSeeder to deploy.

    Parameters
    ----------
    deployment_name : str
        The name of the deployment
    deployment_manifest : DeploymentManifest
        The DeploymentManifest object of the deploy

    """
    # Determine if managed policy stack already deployed
    project_managed_policy_stack_exists, _ = services.cfn.does_stack_exist(stack_name=PROJECT_MANAGED_POLICY_CFN_NAME)
    if not project_managed_policy_stack_exists:
        project_managed_policy_template = (
            deployment_manifest.project_policy if deployment_manifest.project_policy else PROJECT_POLICY_PATH
        )
        project_managed_policy_template = os.path.join(OPS_ROOT, project_managed_policy_template)
        if not os.path.exists(project_managed_policy_template):
            raise Exception(f"Unable to find the Project Managed Policy Template: {project_managed_policy_template}")
        _logger.debug(
            f"Validated the existence of Project Managed Policy Template at:{project_managed_policy_template}"
        )
        _logger.info("Deploying %s", PROJECT_MANAGED_POLICY_CFN_NAME)
        services.cfn.deploy_template(
            stack_name=PROJECT_MANAGED_POLICY_CFN_NAME,
            filename=project_managed_policy_template,
            seedkit_tag=deployment_name,
            parameters={"ProjectName": PROJECT.lower(), "DeploymentName": deployment_name},
        )


def destroy_module_stack(
    deployment_name: str,
    group_name: str,
    module_name: str,
    docker_credentials_secret: Optional[str] = None,
) -> None:
    """
    destroy_module_stack
        This function destroys the module-specific stack created to support deployment

    Parameters
    ----------
    deployment : str
        The name of the deployment
    group : str
        The name of the group
    module : str
        The name of the module
    """
    module_stack_name, module_role_name = _get_module_stack_names(deployment_name, group_name, module_name)
    # Detach the Project Policy
    seedkit_stack_exists, seedkit_stack_name, stack_outputs = commands.seedkit_deployed(seedkit_name=PROJECT)

    policies_arn = []
    if seedkit_stack_exists:
        _logger.debug("Seedkit stack exists - %s", seedkit_stack_name)
        seedkit_managed_policy_arn = stack_outputs.get("SeedkitResourcesPolicyArn")
        policies_arn.append(seedkit_managed_policy_arn)

    # Extract Project Managed policy name
    project_managed_policy_stack_exists, stack_outputs = services.cfn.does_stack_exist(
        stack_name=PROJECT_MANAGED_POLICY_CFN_NAME
    )
    if project_managed_policy_stack_exists:
        project_managed_policy_arn = stack_outputs.get("ProjectPolicyARN")
        policies_arn.append(project_managed_policy_arn)

    _logger.debug(
        f"seedkit_managed_policy {seedkit_managed_policy_arn}  project_managed_policy {project_managed_policy_arn}"
    )
    _logger.debug("module_role_name %s", module_role_name)

    for policy_arn in policies_arn:
        iam.detach_policy_from_role(role_name=module_role_name, policy_arn=policy_arn)

    if not codeseeder.EXECUTING_REMOTELY:
        services.cfn.destroy_stack(module_stack_name)

    if docker_credentials_secret:
        iam.detach_inline_policy_from_role(role_name=module_role_name, policy_name=docker_credentials_secret)
    iam.delete_role(role_name=module_role_name)


def deploy_module_stack(
    module_stack_path: str,
    deployment_name: str,
    group_name: str,
    module_name: str,
    parameters: List[ModuleParameter],
    docker_credentials_secret: Optional[str] = None,
    permission_boundary_arn: Optional[str] = None,
) -> None:
    """
    deploy_module_stack
        This function deploys the module stack (modulestack.yaml) to support the module
        for deployment with CodeSeeder

    Parameters
    ----------
    module_stack_path : str
        The path to the modulestack.yaml
    deployment : str
        The name of the deployment
    group : str
        The name of the group
    module : str
        The name of the module
    parameters : List[ModuleParameter]
        A ModuleParameter object with any necessary parameters from other deployed modules
    docker_credentials_secret: str
        OPTIONAL parameter with name of SecrestManager of docker credentials
    permission_boundary_arn: str
        OPTIONAL parameter with ARN of PermissionBoundary ManagedPolicy
    """

    if module_stack_path:
        _logger.debug(module_stack_path)

    module_stack_name, module_role_name = _get_module_stack_names(deployment_name, group_name, module_name)

    # Create IAM Role
    trust_policy = {
        "Version": "2012-10-17",
        "Statement": [
            {"Effect": "Allow", "Principal": {"Service": "codebuild.amazonaws.com"}, "Action": "sts:AssumeRole"}
        ],
    }

    iam.create_check_iam_role(trust_policy, module_role_name, permission_boundary_arn)

    group_module_name = f"{group_name}-{module_name}"

    if module_stack_path:
        with open(module_stack_path, "r") as file:
            template_parameters = load_yaml(file).get("Parameters", {})

        stack_parameters = {}
        upper_snake_case_parameters = {
            **{p.upper_snake_case: p.value for p in parameters},
            **{
                "DEPLOYMENT_NAME": deployment_name,
                "MODULE_NAME": group_module_name,
                "ROLE_NAME": module_role_name,
            },
        }
        for k in template_parameters.keys():
            upper_snake_case_key = upper_snake_case(k)
            if upper_snake_case_key in upper_snake_case_parameters:
                value = upper_snake_case_parameters[upper_snake_case_key]
                if isinstance(value, str):
                    stack_parameters[k] = value
                elif isinstance(value, list):
                    stack_parameters[k] = ",".join(value)
                else:
                    json.dumps(value)
        _logger.debug("stack_parameters: %s", stack_parameters)

        # Create/Update Module IAM Policy
        _logger.info("Deploying Module Stack for %s", group_module_name)
        services.cfn.deploy_template(
            stack_name=module_stack_name,
            filename=module_stack_path,
            seedkit_tag=module_stack_name,
            parameters=stack_parameters,
        )

    # Attaching managed IAM Policies
    _logger.debug("Extracting the Codeseeder Managed policy")
    seedkit_stack_exists, seedkit_stack_name, stack_outputs = commands.seedkit_deployed(seedkit_name=PROJECT)
    if seedkit_stack_exists:
        _logger.debug("Seedkit stack exists - %s", seedkit_stack_name)
        seedkit_managed_policy_arn = stack_outputs.get("SeedkitResourcesPolicyArn")

    # Extract Project Managed policy name
    project_managed_policy_stack_exists, stack_outputs = services.cfn.does_stack_exist(
        stack_name=PROJECT_MANAGED_POLICY_CFN_NAME
    )

    _logger.debug("project_managed_policy_output is : %s", stack_outputs)
    if project_managed_policy_stack_exists:
        project_managed_policy_arn = stack_outputs.get("ProjectPolicyARN")

    if not project_managed_policy_arn:
        raise ValueError("Project Managed Stack is missing the export `ProjectPolicyARN`")

    policies = [seedkit_managed_policy_arn, project_managed_policy_arn]
    policies_attached = iam.attach_policy_to_role(module_role_name, policies)
    if policies.sort() == policies_attached.sort():
        _logger.info("Delaying module %s deployment to allow IAM Roles and Policies to take effect", group_module_name)
        time.sleep(10)  # on first deployment roles and policy attachments need time to take effect

    # Attaching Docker Credentials Secret Optionally
    policy_body = json.dumps(
        {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Action": [
                        "secretsmanager:GetSecretValue",
                        "secretsmanager:DescribeSecret",
                        "secretsmanager:ListSecretVersionIds",
                    ],
                    "Resource": f"arn:aws:secretsmanager:{REGION}:{ACCOUNT_ID}:secret:{docker_credentials_secret}*",
                },
                {"Effect": "Allow", "Action": ["secretsmanager:ListSecrets"], "Resource": "*"},
            ],
        }
    )

    if docker_credentials_secret:
        iam.attach_inline_policy(
            role_name=module_role_name,
            policy_body=policy_body,
            policy_name=docker_credentials_secret,
        )


def deploy_seedkit() -> None:
    """
    deploy_seedkit
        Accessor method to CodeSeeder to deploy the SeedKit if not deployed
    """
    stack_exists, _, _ = commands.seedkit_deployed(seedkit_name=PROJECT)
    if not stack_exists:
        commands.deploy_seedkit(seedkit_name=PROJECT)
