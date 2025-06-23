#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
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

import logging
import random
import string
from typing import Any, Callable, Dict, List, Optional, Tuple, Union

from boto3 import Session

from seedfarmer.commands import _cfn_seedkit as cfn_seedkit
from seedfarmer.services import _cfn as cfn
from seedfarmer.services import _s3 as s3

_logger: logging.Logger = logging.getLogger(__name__)


def seedkit_deployed(
    seedkit_name: str, session: Optional[Union[Callable[[], Session], Session]] = None
) -> Tuple[bool, str, Dict[str, str]]:
    """Checks for existence of the Seedkit CloudFormation Stack

    If the Stack exists, then the Stack Outputs are also returned to eliminate need for another roundtrip call to
    CloudFormation.

    Parameters
    ----------
    seedkit_name : str
        Named of the seedkit to check.
    session: Optional[Union[Callable[[], Session], Session]], optional
        Optional Session or function returning a Session to use for all boto3 operations, by default None

    Returns
    -------
    Tuple[bool, str, Dict[str, str]]
        Returns a Tuple with a bool indicating existence of the Stack, the Stack name, and a dict with the
        Stack Outputs
    """
    stack_name: str = cfn.get_stack_name(seedkit_name=seedkit_name)
    stack_exists, stack_outputs = cfn.does_stack_exist(stack_name=stack_name, session=session)
    return stack_exists, stack_name, stack_outputs


def deploy_seedkit(
    seedkit_name: str,
    managed_policy_arns: Optional[List[str]] = None,
    deploy_codeartifact: bool = False,
    session: Optional[Session] = None,
    vpc_id: Optional[str] = None,
    subnet_ids: Optional[List[str]] = None,
    security_group_ids: Optional[List[str]] = None,
    permissions_boundary_arn: Optional[str] = None,
    synthesize: bool = False,
    **kwargs: Dict[str, Any],
) -> None:
    """Deploys the seedkit resources into the environment.

    Resources deployed include: S3 Bucket, CodeArtifact Domain, CodeArtifact Repository, CodeBuild Project,
    IAM Role, IAM Managed Policy, and KMS Key. All resource names will include the seedkit_name and IAM Role and Policy
    grant least privilege access to only the resources associated with this Seedkit. Seedkits are deployed to an
    AWS Region, names on global resources (S3, IAM) include a region identifier to avoid conflicts and ensure the same
    Seedkit name can be deployed to multiple regions.

    Parameters
    ----------
    seedkit_name : str
        Name of the seedkit to deploy. All resources will include this in their naming conventions
    managed_policy_arns : Optional[List[str]]
        List of Managed Policy to ARNs to attach to the default IAM Role created and used
        by the CodeBuild Project
    deploy_codeartifact : bool
        Trigger optional deployment of CodeArtifact Domain and Repository for use by the Seedkit and
        its libraries
    session: Optional[Union[Callable[[], Session], Session]], optional
        Optional Session or function returning a Session to use for all boto3 operations, by default None
    vpc_id: Optional[str]
        If deploying codebuild in a VPC, the VPC-ID to use
        (must have vpc-id, subnets, and security_group_ids)
    subnet_ids:  Optional[List[str]]
        If deploying codebuild in a VPC, a list of Subnets to use
        (must have vpc-id, subnets, and security_group_ids)
    security_group_ids: Optional[List[str]]
        If deploying codebuild in a VPC, a list of Security Group IDs to use
        (must have vpc-id, subnets, and security_group_ids)
    permissions_boundary_arn: Optional[str]
        If using a permissions boundary, the arn of that policy to be provided
    synthesize: bool
        Synthesize seedkit template only. Do not deploy. False by default.
    """
    deploy_id: Optional[str] = None
    stack_exists, stack_name, stack_outputs = seedkit_deployed(seedkit_name=seedkit_name, session=session)
    _logger.info("Deploying Seedkit %s with Stack Name %s", seedkit_name, stack_name)
    _logger.debug("Managed Policy Arns: %s", managed_policy_arns)
    _logger.debug("VPC-ID: %s", vpc_id)
    _logger.debug("Subnets: %s", subnet_ids)
    _logger.debug("Security Groups %s", security_group_ids)
    if stack_exists:
        deploy_id = stack_outputs.get("DeployId")
        _logger.info("Seedkit found with DeployId: %s", deploy_id)

    deploy_id = deploy_id if deploy_id else "".join(random.choice(string.ascii_lowercase) for i in range(6))
    template_filename: Optional[str] = cfn_seedkit.synth(
        deploy_id=deploy_id,
        synthesize=synthesize,
        **kwargs,
    )

    # Create parameters dictionary for CloudFormation
    parameters: Dict[str, str] = {
        "SeedkitName": seedkit_name,
        "DeployId": deploy_id,
        "RolePrefix": str(kwargs.get("role_prefix", "/")),
        "PolicyPrefix": str(kwargs.get("policy_prefix", "/")),
        "DeployCodeArtifact": str(deploy_codeartifact).lower(),
    }

    # Only add ManagedPolicyArns if it's not None
    if managed_policy_arns:
        parameters["ManagedPolicyArns"] = ",".join(managed_policy_arns)

    # Only add PermissionsBoundaryArn if it's not None
    if permissions_boundary_arn:
        parameters["PermissionsBoundaryArn"] = permissions_boundary_arn

    # Only add VpcId if it's not None
    if vpc_id:
        parameters["VpcId"] = vpc_id

    # Only add SecurityGroupIds if it's not None
    if security_group_ids:
        parameters["SecurityGroupIds"] = ",".join(security_group_ids)

    # Only add SubnetIds if it's not None
    if subnet_ids:
        parameters["SubnetIds"] = ",".join(subnet_ids)

    if not synthesize:
        assert template_filename is not None, "Template filename is required"
        cfn.deploy_template(
            stack_name=stack_name,
            filename=template_filename,
            seedkit_tag=f"codeseeder-{seedkit_name}",  # (LEGACY)
            session=session,
            parameters=parameters,
        )
        _logger.info("Seedkit Deployed")


def destroy_seedkit(seedkit_name: str, session: Optional[Union[Callable[[], Session], Session]] = None) -> None:
    """Destroys the resources associated with the seedkit.

    Parameters
    ----------
    seedkit_name : str
        Name of the seedkit to destroy
    session: Optional[Union[Callable[[], Session], Session]], optional
        Optional Session or function returning a Session to use for all boto3 operations, by default None
    """
    stack_exists, stack_name, stack_outputs = seedkit_deployed(seedkit_name=seedkit_name, session=session)
    _logger.info("Destroying Seedkit %s with Stack Name %s", seedkit_name, stack_name)
    if stack_exists:
        seedkit_bucket = stack_outputs.get("Bucket")
        if seedkit_bucket:
            s3.delete_bucket(bucket=seedkit_bucket, session=session)
        cfn.destroy_stack(stack_name=stack_name, session=session)
        _logger.info("Seedkit Destroyed")
    else:
        _logger.warning("Seedkit/Stack does not exist")
