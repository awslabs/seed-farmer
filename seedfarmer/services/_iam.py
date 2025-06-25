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

import json
import logging
from typing import Any, Callable, Dict, List, Optional, Union, cast

from boto3 import Session

import seedfarmer.errors
from seedfarmer.services._service_utils import boto3_client, boto3_resource, get_region

_logger: logging.Logger = logging.getLogger(__name__)


def get_role(
    role_name: str, session: Optional[Union[Callable[[], Session], Session]] = None
) -> Optional[Dict[str, Any]]:
    _logger.debug("Getting Role: %s", role_name)

    iam_client = boto3_client("iam", session=session)
    try:
        return cast(Dict[str, Any], iam_client.get_role(RoleName=role_name))
    except iam_client.exceptions.NoSuchEntityException:
        return None


def get_role_arn(role_name: str, session: Optional[Union[Callable[[], Session], Session]] = None) -> str:
    role = get_role(role_name=role_name, session=session)

    if not role:
        raise seedfarmer.errors.InvalidConfigurationError(f"Role {role_name} does not exist")

    return cast(str, role["Role"]["Arn"])


def create_check_iam_role(
    project_name: str,
    deployment_name: str,
    trust_policy: Dict[str, Any],
    role_name: str,
    permissions_boundary_arn: Optional[str],
    group_name: Optional[str] = None,
    module_name: Optional[str] = None,
    session: Optional[Union[Callable[[], Session], Session]] = None,
    role_prefix: Optional[str] = None,
) -> None:
    _logger.debug("Creating IAM Role with name: %s ", role_name)
    iam_client = boto3_client("iam", session=session)
    try:
        iam_client.get_role(RoleName=role_name)
    except iam_client.exceptions.NoSuchEntityException:
        args: Dict[str, Any] = {
            "RoleName": role_name,
            "Path": role_prefix if role_prefix else "/",
            "AssumeRolePolicyDocument": json.dumps(trust_policy),
            "Description": f"deployment-role for {role_name}",
            "Tags": [
                {"Key": "Region", "Value": get_region(session=session)},
                {"Key": "SeedFarmerProject", "Value": project_name},
                {"Key": "SeedFarmerDeployment", "Value": deployment_name},
            ],
        }
        if group_name and module_name:
            args["Tags"].append({"Key": "SeedFarmerModule", "Value": f"{group_name}-{module_name}"})
        if permissions_boundary_arn:
            args["PermissionsBoundary"] = permissions_boundary_arn
        iam_client.create_role(**args)


def attach_policy_to_role(
    role_name: str, policies: List[str], session: Optional[Union[Callable[[], Session], Session]] = None
) -> List[str]:
    iam_client = boto3_client("iam", session=session)
    try:
        response = iam_client.list_attached_role_policies(RoleName=role_name)
        attached_policies = [i["PolicyArn"] for i in response["AttachedPolicies"] if response["AttachedPolicies"]]
        _logger.debug("List of Attached Policie(s) are: %s ", attached_policies)
        to_be_attached = list(set(policies) - set(attached_policies))
        # if attached_polices is empty, to_bo_attached == policies

        if attached_policies:
            _logger.debug("To be attached policie(s) are %s ", to_be_attached)
        else:
            _logger.debug("First time deployment, attaching all policies: %s ", to_be_attached)

        for policy in to_be_attached:
            iam_client.attach_role_policy(RoleName=role_name, PolicyArn=policy)
            _logger.debug("Attached the policy: %s ", policy)
        return to_be_attached
    except Exception as e:
        raise e


def attach_inline_policy(
    role_name: str, policy_body: str, policy_name: str, session: Optional[Union[Callable[[], Session], Session]] = None
) -> None:
    iam_client = boto3_client("iam", session=session)
    _logger.debug("Attaching the Inline policy %s to the IAM Role: %s", policy_name, role_name)
    try:
        iam_client.put_role_policy(RoleName=role_name, PolicyName=policy_name, PolicyDocument=policy_body)
    except Exception as e:
        _logger.debug("ailed to attach the Inline policy %s to the IAM Role: %s", policy_name, role_name)
        raise e


def detach_policy_from_role(
    role_name: str, policy_arn: str, session: Optional[Union[Callable[[], Session], Session]] = None
) -> None:
    _logger.debug("Detatching policy: %s  from the IAM Role: %s ", policy_arn, role_name)
    iam_client = boto3_client("iam", session=session)
    try:
        iam_client.detach_role_policy(RoleName=role_name, PolicyArn=policy_arn)
    except Exception as e:
        _logger.info("Could not delete policy %s", policy_arn)
        _logger.info("Caught exception: %s ", e)


def delete_role(role_name: str, session: Optional[Union[Callable[[], Session], Session]] = None) -> None:
    iam_client = boto3_client("iam", session=session)
    try:
        iam_client.delete_role(RoleName=role_name)
    except iam_client.exceptions.NoSuchEntityException as e:
        _logger.info("Could not delete role %s", role_name)
        _logger.info("Caught exception: %s ", e)


def detach_inline_policy_from_role(
    role_name: str, policy_name: str, session: Optional[Union[Callable[[], Session], Session]] = None
) -> None:
    iam_resource = boto3_resource("iam", session)
    try:
        iam_resource.RolePolicy(role_name, policy_name).delete()
    except Exception as e:
        raise e


def get_policy_info(policy_arn: str, session: Optional[Union[Callable[[], Session], Session]] = None) -> Dict[str, Any]:
    iam_client = boto3_client("iam", session=session)
    try:
        return cast(Dict[str, Any], iam_client.get_policy(PolicyArn=policy_arn))
    except iam_client.exceptions.NoSuchEntityException as ne:
        _logger.info("Policy does not exist: %s ", policy_arn)
        raise ne
    except Exception as e:
        raise e
