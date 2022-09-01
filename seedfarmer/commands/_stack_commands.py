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
from typing import List, Optional, cast

from aws_codeseeder import codeseeder, commands, services
from cfn_tools import load_yaml

import seedfarmer.services._iam as iam
from seedfarmer import config
from seedfarmer.mgmt.module_info import _get_module_stack_names
from seedfarmer.models.manifests import DeploymentManifest, ModuleParameter
from seedfarmer.services._service_utils import get_account_id, get_region
from seedfarmer.services.session_manager import SessionManager
from seedfarmer.utils import upper_snake_case

_logger: logging.Logger = logging.getLogger(__name__)


class StackInfo(object):
    _PROJECT_MANAGED_POLICY_CFN_NAME: Optional[str] = None
    PROJECT_POLICY_PATH = "resources/projectpolicy.yaml"

    @property
    def PROJECT_MANAGED_POLICY_CFN_NAME(self) -> str:
        if self._PROJECT_MANAGED_POLICY_CFN_NAME is None:
            self._PROJECT_MANAGED_POLICY_CFN_NAME = f"{config.PROJECT.lower()}-managed-policy"
        return self._PROJECT_MANAGED_POLICY_CFN_NAME


info = StackInfo()


def deploy_managed_policy_stack(
    deployment_name: str, deployment_manifest: DeploymentManifest, account_id: str, region: str
) -> None:
    """
    deploy_managed_policy_stack
        This function deploys the deployment-specific policy to allow CodeSeeder to deploy.

    Parameters
    ----------
    deployment_name : str
        The name of the deployment
    deployment_manifest : DeploymentManifest
        The DeploymentManifest object of the deploy
    account_id: str
        The Account Id where the module is deployed
    region: str
        The region wher
    """
    # Determine if managed policy stack already deployed
    session = SessionManager().get_or_create().get_deployment_session(account_id=account_id, region_name=region)
    project_managed_policy_stack_exists, _ = services.cfn.does_stack_exist(
        stack_name=info.PROJECT_MANAGED_POLICY_CFN_NAME, session=session
    )
    if not project_managed_policy_stack_exists:
        project_managed_policy_template = cast(
            str,
            deployment_manifest.get_parameter_value(
                "projectPolicy", account_id=account_id, region=region, default=info.PROJECT_POLICY_PATH
            ),
        )
        project_managed_policy_template = os.path.join(config.OPS_ROOT, project_managed_policy_template)
        if not os.path.exists(project_managed_policy_template):
            raise Exception(f"Unable to find the Project Managed Policy Template: {project_managed_policy_template}")
        _logger.debug(
            f"Validated the existence of Project Managed Policy Template at: {project_managed_policy_template}"
        )
        _logger.info("Deploying %s", info.PROJECT_MANAGED_POLICY_CFN_NAME)
        services.cfn.deploy_template(
            stack_name=info.PROJECT_MANAGED_POLICY_CFN_NAME,
            filename=project_managed_policy_template,
            seedkit_tag=deployment_name,
            parameters={"ProjectName": config.PROJECT.lower(), "DeploymentName": deployment_name},
            session=session,
        )


def destroy_managed_policy_stack(account_id: str, region: str) -> None:
    """
    destroy_managed_policy_stack
        This function destroys the deployment-specific policy.

    Parameters
    ----------
    account_id: str
        The Account Id where the module is deployed
    region: str
        The region wher
    """
    # Determine if managed policy stack already deployed
    session = SessionManager().get_or_create().get_deployment_session(account_id=account_id, region_name=region)
    project_managed_policy_stack_exists, _ = services.cfn.does_stack_exist(
        stack_name=info.PROJECT_MANAGED_POLICY_CFN_NAME, session=session
    )
    if project_managed_policy_stack_exists:
        _logger.info(
            "Destroying Stack %s in Account/Region: %s/%s", info.PROJECT_MANAGED_POLICY_CFN_NAME, account_id, region
        )
        services.cfn.destroy_stack(
            stack_name=info.PROJECT_MANAGED_POLICY_CFN_NAME,
            session=session,
        )


def destroy_module_stack(
    deployment_name: str,
    group_name: str,
    module_name: str,
    account_id: str,
    region: str,
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
    module_name : str
        The name of the module
    account_id: str
        The Account Id where the module is deployed
    region: str
        The region where the module is deployed
    """
    session = SessionManager().get_or_create().get_deployment_session(account_id=account_id, region_name=region)
    module_stack_name, module_role_name = _get_module_stack_names(
        deployment_name, group_name, module_name, session=session
    )
    # Detach the Project Policy
    seedkit_stack_exists, seedkit_stack_name, stack_outputs = commands.seedkit_deployed(
        seedkit_name=config.PROJECT, session=session
    )

    policies_arn = []
    if seedkit_stack_exists:
        _logger.debug("Seedkit stack exists - %s", seedkit_stack_name)
        seedkit_managed_policy_arn = stack_outputs.get("SeedkitResourcesPolicyArn")
        policies_arn.append(seedkit_managed_policy_arn)

    # Extract Project Managed policy name
    project_managed_policy_stack_exists, stack_outputs = services.cfn.does_stack_exist(
        stack_name=info.PROJECT_MANAGED_POLICY_CFN_NAME, session=session
    )
    if project_managed_policy_stack_exists:
        project_managed_policy_arn = stack_outputs.get("ProjectPolicyARN")
        policies_arn.append(project_managed_policy_arn)

    _logger.debug(
        f"seedkit_managed_policy {seedkit_managed_policy_arn}  project_managed_policy {project_managed_policy_arn}"
    )
    _logger.debug("module_role_name %s", module_role_name)

    for policy_arn in policies_arn:
        iam.detach_policy_from_role(role_name=module_role_name, policy_arn=policy_arn, session=session)

    if not codeseeder.EXECUTING_REMOTELY:
        services.cfn.destroy_stack(module_stack_name, session=session)

    if docker_credentials_secret:
        iam.detach_inline_policy_from_role(
            role_name=module_role_name, policy_name=docker_credentials_secret, session=session
        )
    iam.delete_role(role_name=module_role_name, session=session)


def deploy_module_stack(
    module_stack_path: str,
    deployment_name: str,
    group_name: str,
    module_name: str,
    account_id: str,
    region: str,
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
    account_id: str
        The Account Id where the module is deployed
    region: str
        The region where the module is deployed
    docker_credentials_secret: str
        OPTIONAL parameter with name of SecrestManager of docker credentials
    permission_boundary_arn: str
        OPTIONAL parameter with ARN of PermissionBoundary ManagedPolicy
    """

    if module_stack_path:
        _logger.debug(module_stack_path)

    session = SessionManager().get_or_create().get_deployment_session(account_id=account_id, region_name=region)
    module_stack_name, module_role_name = _get_module_stack_names(
        deployment_name, group_name, module_name, session=session
    )

    # Create IAM Role
    trust_policy = {
        "Version": "2012-10-17",
        "Statement": [
            {"Effect": "Allow", "Principal": {"Service": "codebuild.amazonaws.com"}, "Action": "sts:AssumeRole"}
        ],
    }

    iam.create_check_iam_role(trust_policy, module_role_name, permission_boundary_arn, session=session)

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
            session=session,
        )

    # Attaching managed IAM Policies
    _logger.debug("Extracting the Codeseeder Managed policy")
    seedkit_stack_exists, seedkit_stack_name, stack_outputs = commands.seedkit_deployed(
        seedkit_name=config.PROJECT, session=session
    )
    if seedkit_stack_exists:
        _logger.debug("Seedkit stack exists - %s", seedkit_stack_name)
        seedkit_managed_policy_arn = stack_outputs.get("SeedkitResourcesPolicyArn")

    # Extract Project Managed policy name
    project_managed_policy_stack_exists, stack_outputs = services.cfn.does_stack_exist(
        stack_name=info.PROJECT_MANAGED_POLICY_CFN_NAME, session=session
    )

    _logger.debug("project_managed_policy_output is : %s", stack_outputs)
    if project_managed_policy_stack_exists:
        project_managed_policy_arn = stack_outputs.get("ProjectPolicyARN")

    if not project_managed_policy_arn:
        raise ValueError("Project Managed Stack is missing the export `ProjectPolicyARN`")

    policies = [seedkit_managed_policy_arn, project_managed_policy_arn]
    policies_attached = iam.attach_policy_to_role(module_role_name, policies, session=session)
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
                    "Resource": (
                        f"arn:aws:secretsmanager:{get_region(session=session)}:{get_account_id(session=session)}"
                        f":secret:{docker_credentials_secret}*"
                    ),
                },
                {"Effect": "Allow", "Action": ["secretsmanager:ListSecrets"], "Resource": "*"},
            ],
        }
    )

    if docker_credentials_secret:
        iam.attach_inline_policy(
            role_name=module_role_name, policy_body=policy_body, policy_name=docker_credentials_secret, session=session
        )


def deploy_seedkit(account_id: str, region: str) -> None:
    """
    deploy_seedkit
        Accessor method to CodeSeeder to deploy the SeedKit if not deployed

    Parameters
    ----------
    account_id: str
        The Account Id where the module is deployed
    region: str
        The region wher"""
    session = SessionManager().get_or_create().get_deployment_session(account_id=account_id, region_name=region)
    stack_exists, _, stack_outputs = commands.seedkit_deployed(seedkit_name=config.PROJECT, session=session)
    deploy_codeartifact = "CodeArtifactRepository" in stack_outputs
    if stack_exists:
        _logger.debug("Updating SeedKit for Account/Region: %s/%s", account_id, region)
    else:
        _logger.debug("Initializing SeedKit for Account/Region: %s/%s", account_id, region)
    commands.deploy_seedkit(seedkit_name=config.PROJECT, deploy_codeartifact=deploy_codeartifact, session=session)


def destroy_seedkit(account_id: str, region: str) -> None:
    """
    destroy_seedkit
        Accessor method to CodeSeeder to destroy the SeedKit if deployed

    Parameters
    ----------
    account_id: str
        The Account Id where the module is deployed
    region: str
        The region wher"""
    session = SessionManager().get_or_create().get_deployment_session(account_id=account_id, region_name=region)
    _logger.debug("Destroying SeedKit for Account/Region: %s/%s", account_id, region)
    commands.destroy_seedkit(seedkit_name=config.PROJECT, session=session)
