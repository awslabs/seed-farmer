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
from typing import Any, Dict, List, Optional, Tuple, cast

import boto3
from cfn_tools import load_yaml

import seedfarmer.commands._seedkit_commands as sk_commands
import seedfarmer.errors
import seedfarmer.services._cfn as cfn
import seedfarmer.services._iam as iam
import seedfarmer.services._s3 as s3
from seedfarmer import config
from seedfarmer.mgmt.bundle_support import BUNDLE_PREFIX
from seedfarmer.mgmt.module_info import get_module_stack_names
from seedfarmer.models.manifests import DeploymentManifest, ModuleParameter
from seedfarmer.services import get_sts_identity_info
from seedfarmer.services.session_manager import SessionManager
from seedfarmer.types.parameter_types import EnvVar, EnvVarType
from seedfarmer.utils import generate_hash, upper_snake_case

_logger: logging.Logger = logging.getLogger(__name__)


class StackInfo(object):
    _PROJECT_MANAGED_POLICY_CFN_NAME: Optional[str] = None
    _SEEDFARMER_BUCKET_CFN_NAME: Optional[str] = None
    _region: Optional[str] = None
    _account_id: Optional[str] = None

    def __init__(self, account_id: Optional[str] = None, region: Optional[str] = None) -> None:
        self._account_id = account_id
        self._region = region

    @property
    def PROJECT_MANAGED_POLICY_CFN_NAME(self) -> str:
        if self._PROJECT_MANAGED_POLICY_CFN_NAME is None:
            self._PROJECT_MANAGED_POLICY_CFN_NAME = f"{config.PROJECT.lower()}-managed-policy"
        return self._PROJECT_MANAGED_POLICY_CFN_NAME

    @property
    def SEEDFARMER_BUCKET_STACK_NAME(self) -> str:
        return f"seedfarmer-{config.PROJECT.lower()}-artifacts"


info = StackInfo()


def _get_project_managed_policy_arn(session: Optional[boto3.Session]) -> str:
    def _check_stack_status() -> Tuple[bool, Dict[str, str]]:
        return cfn.does_stack_exist(stack_name=info.PROJECT_MANAGED_POLICY_CFN_NAME, session=session)

    retries = 3
    while retries > 0:
        project_managed_policy_stack_exists, stack_outputs = _check_stack_status()
        if project_managed_policy_stack_exists:
            if stack_outputs.get("StackStatus") and "_IN_PROGRESS" in stack_outputs.get("StackStatus"):  # type: ignore
                _logger.info("The managed policy stack is not complete, waiting 30 seconds")
                time.sleep(30)
                retries -= 1
            else:
                _logger.debug("project_managed_policy_output is : %s", stack_outputs)
                project_managed_policy_arn = stack_outputs.get("ProjectPolicyARN", None)
                retries = -1
        else:
            _logger.debug("project_managed_policy_output does not exist")
            retries = -1

    if not project_managed_policy_arn:
        raise seedfarmer.errors.InvalidConfigurationError(
            "Project Managed Stack is missing the export `ProjectPolicyARN`"
        )
    else:
        return project_managed_policy_arn


def _get_seedkit_resources_policy_arn(session: Optional[boto3.Session]) -> Optional[str]:
    seedkit_stack_exists, seedkit_stack_name, stack_outputs = sk_commands.seedkit_deployed(
        seedkit_name=config.PROJECT, session=session
    )
    if seedkit_stack_exists:
        return cast(str, stack_outputs.get("SeedkitResourcesPolicyArn"))
    return None


def _get_docker_secret_inline_policy(docker_credentials_secret: str, session: Optional[boto3.Session]) -> str:
    account_id, region, partition = get_sts_identity_info(session=session)
    return json.dumps(
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
                        f"arn:{partition}:secretsmanager:{region}:{account_id}:secret:{docker_credentials_secret}*"
                    ),
                },
                {"Effect": "Allow", "Action": ["secretsmanager:ListSecrets"], "Resource": "*"},
            ],
        }
    )


def create_module_deployment_role(
    role_name: str,
    deployment_name: str,
    group_name: Optional[str] = None,
    module_name: Optional[str] = None,
    docker_credentials_secret: Optional[str] = None,
    permissions_boundary_arn: Optional[str] = None,
    session: Optional[boto3.Session] = None,
    role_prefix: Optional[str] = None,
) -> None:
    iam.create_check_iam_role(
        project_name=config.PROJECT,
        deployment_name=deployment_name,
        group_name=group_name,
        module_name=module_name,
        trust_policy={
            "Version": "2012-10-17",
            "Statement": [
                {"Effect": "Allow", "Principal": {"Service": "codebuild.amazonaws.com"}, "Action": "sts:AssumeRole"}
            ],
        },
        role_name=role_name,
        permissions_boundary_arn=permissions_boundary_arn,
        session=session,
        role_prefix=role_prefix,
    )

    policies = []
    seedkit_resources_policy_arn = _get_seedkit_resources_policy_arn(session=session)
    if seedkit_resources_policy_arn:
        policies.append(seedkit_resources_policy_arn)

    project_managed_policy_arn = _get_project_managed_policy_arn(session=session)
    policies.append(project_managed_policy_arn)

    _logger.debug(
        f"seedkit_resources_policy {seedkit_resources_policy_arn}  project_managed_policy {project_managed_policy_arn}"
    )

    policies_attached = iam.attach_policy_to_role(role_name, policies, session=session)
    if policies.sort() == policies_attached.sort():
        _logger.info("Delaying deployment to allow %s IAM Role and Policies to take effect", role_name)
        time.sleep(12)

    if docker_credentials_secret:
        policy_body = _get_docker_secret_inline_policy(
            docker_credentials_secret=docker_credentials_secret, session=session
        )
        iam.attach_inline_policy(
            role_name=role_name, policy_body=policy_body, policy_name=docker_credentials_secret, session=session
        )


def destroy_module_deployment_role(
    role_name: str,
    docker_credentials_secret: Optional[str] = None,
    session: Optional[boto3.Session] = None,
) -> None:
    policies = []
    seedkit_resources_policy_arn = _get_seedkit_resources_policy_arn(session=session)
    if seedkit_resources_policy_arn:
        policies.append(seedkit_resources_policy_arn)

    # Extract Project Managed policy name
    project_managed_policy_stack_exists, stack_outputs = cfn.does_stack_exist(
        stack_name=info.PROJECT_MANAGED_POLICY_CFN_NAME, session=session
    )
    if project_managed_policy_stack_exists:
        project_managed_policy_arn = stack_outputs.get("ProjectPolicyARN")
        policies.append(str(project_managed_policy_arn))

    _logger.debug(
        f"seedkit_resources_policy {seedkit_resources_policy_arn}  project_managed_policy {project_managed_policy_arn}"
    )

    for policy_arn in policies:
        iam.detach_policy_from_role(role_name=role_name, policy_arn=policy_arn, session=session)

    # Detach Docker secret policy
    if docker_credentials_secret:
        iam.detach_inline_policy_from_role(role_name=role_name, policy_name=docker_credentials_secret, session=session)

    iam.delete_role(role_name=role_name, session=session)


def deploy_bucket_storage_stack(
    account_id: str,
    region: str,
    **kwargs: Any,
) -> str:
    """
    deploy_bucket_storage_stack
        This function deploys the account/region bucket for storing artifacts

    Parameters
    ----------
    account_id: str
        The Account Id where the module is deployed
    region: str
        The region where the module is deployed

    Returns
    -------
    str
        the bucket name
    """

    session = SessionManager().get_or_create().get_deployment_session(account_id=account_id, region_name=region)
    info = StackInfo(account_id=account_id, region=region)
    bucket_stack_name = info.SEEDFARMER_BUCKET_STACK_NAME

    stack_exists, output = cfn.does_stack_exist(stack_name=bucket_stack_name, session=session)

    if not stack_exists:
        _logger.info("Deploying the bucket storage stack %s", bucket_stack_name)
        hash = generate_hash(string=f"{account_id}-{region}", length=6)
        bucket_name = f"seedfarmer-{config.PROJECT.lower()}-{region}-{account_id}-{hash}-no-delete"
        if len(bucket_name) > 63:
            limit = len(f"seedfarmer--{config.PROJECT.lower()}-no-delete")
            sm_hash = generate_hash(string=f"{config.PROJECT.lower()}-{region}-{account_id}", length=63 - limit)
            bucket_name = f"seedfarmer-{config.PROJECT.lower()}-{sm_hash}-no-delete"
        cfn.deploy_template(
            stack_name=bucket_stack_name,
            filename=config.BUCKET_STORAGE_PATH,
            seedkit_tag=config.PROJECT.lower(),
            parameters={"ProjectName": config.PROJECT.lower(), "BucketName": bucket_name[:63]},
            session=session,
        )
        stack_exists, output = cfn.does_stack_exist(stack_name=bucket_stack_name, session=session)
    return str(output.get("Bucket"))


def deploy_managed_policy_stack(
    deployment_manifest: DeploymentManifest,
    account_id: str,
    region: str,
    update_project_policy: Optional[bool] = False,
    **kwargs: Any,
) -> None:
    """
    deploy_managed_policy_stack
        This function deploys the deployment-specific policy

    Parameters
    ----------
    deployment_manifest : DeploymentManifest
        The DeploymentManifest object of the deploy
    account_id: str
        The Account Id where the module is deployed
    region: str
        The region where the module is deployed
    update_project_policy: bool
        Force update the project policy if already deployed
    """
    # Determine if managed policy stack already deployed
    session = SessionManager().get_or_create().get_deployment_session(account_id=account_id, region_name=region)
    project_managed_policy_stack_exists, _ = cfn.does_stack_exist(
        stack_name=info.PROJECT_MANAGED_POLICY_CFN_NAME, session=session
    )
    if not project_managed_policy_stack_exists or update_project_policy:
        project_managed_policy_template = config.PROJECT_POLICY_PATH
        _logger.info("Resolved the ProjectPolicyPath %s", project_managed_policy_template)
        if not os.path.exists(project_managed_policy_template):
            raise seedfarmer.errors.InvalidPathError(
                f"Unable to find the Project Managed Policy Template: {project_managed_policy_template}"
            )
        _logger.info(
            "Deploying %s from the path %s", info.PROJECT_MANAGED_POLICY_CFN_NAME, project_managed_policy_template
        )
        cfn.deploy_template(
            stack_name=info.PROJECT_MANAGED_POLICY_CFN_NAME,
            filename=project_managed_policy_template,
            seedkit_tag=deployment_manifest.name,
            parameters={"ProjectName": config.PROJECT.lower(), "DeploymentName": str(deployment_manifest.name)},
            session=session,
        )


def destroy_bucket_storage_stack(
    account_id: str,
    region: str,
    **kwargs: Any,
) -> None:
    """
    destroy_bucket_storage_stack
        This function destroys the bucket stack for SeedFarmer

    Parameters
    ----------
    account_id: str
        The Account Id where the module is deployed
    region: str
        The region where deployed
    """

    # Determine if managed policy stack already deployed
    session = SessionManager().get_or_create().get_deployment_session(account_id=account_id, region_name=region)
    info = StackInfo(account_id=account_id, region=region)
    bucket_stack_name = info.SEEDFARMER_BUCKET_STACK_NAME
    bucket_stack_exists, outputs = cfn.does_stack_exist(stack_name=bucket_stack_name, session=session)
    if bucket_stack_exists and outputs is not None:
        bucket_name = str(outputs.get("Bucket"))
        bucket_empty = s3.is_bucket_empty(bucket=bucket_name, folder=BUNDLE_PREFIX, session=session)
        if bucket_empty:
            _logger.info("Destroying Stack %s in Account/Region: %s/%s", bucket_stack_name, account_id, region)
            import botocore.exceptions

            try:
                s3.delete_objects(bucket=bucket_name, session=session)
                cfn.destroy_stack(
                    stack_name=bucket_stack_name,
                    session=session,
                )
            except (botocore.exceptions.WaiterError, botocore.exceptions.ClientError):
                _logger.info(f"Failed to delete project stack {bucket_stack_name}, ignoring and moving on")
        else:
            _logger.info("Stack %s left, S3 bucket %s not empty", bucket_stack_name, bucket_name)
            return


def destroy_managed_policy_stack(account_id: str, region: str, **kwargs: Any) -> None:
    """
    destroy_managed_policy_stack
        This function destroys the deployment-specific policy.

    Parameters
    ----------
    account_id: str
        The Account Id where the module is deployed
    region: str
        The region where the module is deployed
    """
    # Determine if managed policy stack already deployed
    session = SessionManager().get_or_create().get_deployment_session(account_id=account_id, region_name=region)
    project_managed_policy_stack_exists, stack_outputs = cfn.does_stack_exist(
        stack_name=info.PROJECT_MANAGED_POLICY_CFN_NAME, session=session
    )
    _logger.debug("project_managed_policy_output is : %s", stack_outputs)
    has_roles_attached = False
    if project_managed_policy_stack_exists:
        project_managed_policy_arn = stack_outputs.get("ProjectPolicyARN")
        policy = iam.get_policy_info(policy_arn=str(project_managed_policy_arn), session=session)
        has_roles_attached = True if policy and policy["Policy"]["AttachmentCount"] > 0 else False

    if project_managed_policy_stack_exists and not has_roles_attached:
        _logger.info(
            "Destroying Stack %s in Account/Region: %s/%s", info.PROJECT_MANAGED_POLICY_CFN_NAME, account_id, region
        )
        import botocore.exceptions

        try:
            cfn.destroy_stack(
                stack_name=info.PROJECT_MANAGED_POLICY_CFN_NAME,
                session=session,
            )
        except (botocore.exceptions.WaiterError, botocore.exceptions.ClientError):
            _logger.info(
                f"Failed to delete project stack {info.PROJECT_MANAGED_POLICY_CFN_NAME}, ignoring and moving on"
            )
    else:
        _logger.info(
            "Stack %s in Account/Region: %s/%s is either not deployed or has roles attached",
            info.PROJECT_MANAGED_POLICY_CFN_NAME,
            account_id,
            region,
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
    module_stack_name, module_role_name = get_module_stack_names(
        deployment_name, group_name, module_name, session=session
    )

    cfn.destroy_stack(module_stack_name, session=session)

    destroy_module_deployment_role(
        role_name=module_role_name,
        docker_credentials_secret=docker_credentials_secret,
        session=session,
    )


def deploy_module_stack(
    module_stack_path: str,
    deployment_name: str,
    group_name: str,
    module_name: str,
    account_id: str,
    region: str,
    parameters: List[ModuleParameter],
    docker_credentials_secret: Optional[str] = None,
    permissions_boundary_arn: Optional[str] = None,
    role_prefix: Optional[str] = None,
) -> Tuple[str, str]:
    """
    deploy_module_stack
        This function deploys the module stack (modulestack.yaml) to support the module
        for deployment

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
    permissions_boundary_arn: str
        OPTIONAL parameter with Name of PermissionBoundary ManagedPolicy
    """

    _logger.debug(module_stack_path)

    session = (
        SessionManager()
        .get_or_create(role_prefix=role_prefix)
        .get_deployment_session(account_id=account_id, region_name=region)
    )
    module_stack_name, module_role_name = get_module_stack_names(
        deployment_name, group_name, module_name, session=session
    )

    create_module_deployment_role(
        role_name=module_role_name,
        deployment_name=deployment_name,
        group_name=group_name,
        module_name=module_name,
        docker_credentials_secret=docker_credentials_secret,
        permissions_boundary_arn=permissions_boundary_arn,
        session=session,
        role_prefix=role_prefix,
    )

    _logger.debug("module_role_name %s", module_role_name)

    with open(module_stack_path, "r") as file:
        template = load_yaml(file)
        template_parameters = template.get("Parameters", {})

    stack_parameters = {}
    group_module_name = f"{group_name}-{module_name}"
    upper_snake_case_parameters = {
        **{p.upper_snake_case: p.value for p in parameters},
        **{
            "PROJECT_NAME": config.PROJECT,
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
            elif isinstance(value, EnvVar):
                if (
                    value.type in [EnvVarType.PARAMETER_STORE.value, EnvVarType.SECRETS_MANAGER.value]
                    and ":" in value.value
                ):
                    stack_parameters[k] = value.value.split(":")[0]
                else:
                    stack_parameters[k] = value.value
            else:
                json.dumps(value)
    _logger.debug("stack_parameters: %s", stack_parameters)

    # Create/Update Module IAM Policy
    _logger.info("Deploying Module Stack for %s", group_module_name)
    cfn.deploy_template(
        stack_name=module_stack_name,
        filename=module_stack_path,
        seedkit_tag=module_stack_name,
        parameters=stack_parameters,
        session=session,
    )

    return module_stack_name, module_role_name


def get_module_stack_info(
    deployment_name: str,
    group_name: str,
    module_name: str,
    account_id: str,
    region: str,
) -> Tuple[str, str, bool]:
    """
    get_module_stack_info
        This function returns the name of the role and the name of the stack associated with the
        module deployment role

    Parameters
    ----------
    deployment_name : str
        Deployment Name
    group_name : str
        Group name
    module_name : str
        Module Name
    account_id : str
        The account id where deployed
    region : str
        The region where deployed

    Returns
    -------
    Tuple[str, str]
        A tuple with the  module_stack_name and  module_role_name
        [ module_stack_name, module_role_name ]
    """

    session = SessionManager().get_or_create().get_deployment_session(account_id=account_id, region_name=region)
    module_stack_name, module_role_name = get_module_stack_names(
        deployment_name, group_name, module_name, session=session
    )
    stack_exists, _ = cfn.does_stack_exist(stack_name=module_stack_name, session=session)
    return module_stack_name, module_role_name, stack_exists


def deploy_seedkit(
    account_id: str,
    region: str,
    vpc_id: Optional[str] = None,
    private_subnet_ids: Optional[List[str]] = None,
    security_group_ids: Optional[List[str]] = None,
    update_seedkit: Optional[bool] = False,
    role_prefix: Optional[str] = None,
    policy_prefix: Optional[str] = None,
    permissions_boundary_arn: Optional[str] = None,
    deploy_codeartifact: Optional[bool] = False,
    **kwargs: Any,
) -> Dict[str, Any]:
    """
    deploy_seedkit
        Deploy the SeedKit if not deployed

    Parameters
    ----------
    account_id: str
        The Account Id where the seedkit is deployed
    region: str
        The region where seedkit is deployed
    vpc_id: Optional[str]
        The VPC to associate seedkit with (codebuild)
    private_subnet_ids: Optional[List[str]]
        The Subnet IDs to associate seedkit with (codebuild)
    security_group_ids: Optional[List[str]]
        The Security Group IDs to associate seedkit with (codebuild)
    role_prefix: Optional[str]
        The IAM Path Prefix to use for seedkit role
    policy_prefix: Optional[str]
        The IAM Path Prefix to use for seedkit policy
    permissions_boundary_arn: Optional[str]
        The ARN of the permissions boundary to attach to seedkit role
    """
    session = SessionManager().get_or_create().get_deployment_session(account_id=account_id, region_name=region)
    stack_exists, _, stack_outputs = sk_commands.seedkit_deployed(seedkit_name=config.PROJECT, session=session)
    deploy_codeartifact = bool(stack_outputs.get("CodeArtifactRepository")) or bool(deploy_codeartifact)

    if stack_exists and not update_seedkit:
        _logger.debug("SeedKit exists and not updating for Account/Region: %s/%s", account_id, region)
    else:
        _logger.debug("Initializing / Updating SeedKit for Account/Region: %s/%s", account_id, region)

        seedkit_args = {
            "seedkit_name": config.PROJECT,
            "deploy_codeartifact": deploy_codeartifact,
            "session": session,
            "vpc_id": vpc_id,
            "subnet_ids": private_subnet_ids,
            "security_group_ids": security_group_ids,
        }

        if role_prefix:
            seedkit_args["role_prefix"] = role_prefix
        if policy_prefix:
            seedkit_args["policy_prefix"] = policy_prefix
        if permissions_boundary_arn:
            seedkit_args["permissions_boundary_arn"] = permissions_boundary_arn

        sk_commands.deploy_seedkit(**seedkit_args)  # type: ignore [arg-type]
        # Go get the outputs and return them
        _, _, stack_outputs = sk_commands.seedkit_deployed(seedkit_name=config.PROJECT, session=session)
    return dict(stack_outputs)


def destroy_seedkit(account_id: str, region: str) -> None:
    """
    destroy_seedkit
        Destroy the SeedKit if deployed

    Parameters
    ----------
    account_id: str
        The Account Id where the module is deployed
    region: str
        The region where the module is deployed
    """
    session = SessionManager().get_or_create().get_deployment_session(account_id=account_id, region_name=region)
    _logger.debug("Destroying SeedKit for Account/Region: %s/%s", account_id, region)
    sk_commands.destroy_seedkit(seedkit_name=config.PROJECT, session=session)


def force_manage_policy_attach(
    deployment_name: str,
    group_name: str,
    module_name: str,
    account_id: str,
    region: str,
    module_role_name: Optional[str] = None,
) -> None:
    session = SessionManager().get_or_create().get_deployment_session(account_id=account_id, region_name=region)
    if not module_role_name:
        module_stack_name, module_role_name = get_module_stack_names(
            deployment_name, group_name, module_name, session=session
        )

    project_managed_policy_arn = _get_project_managed_policy_arn(session=session)

    policies = [project_managed_policy_arn]
    iam.attach_policy_to_role(module_role_name, policies, session=session)
