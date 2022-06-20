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
from typing import Any, Dict, List, Optional, cast

from seedfarmer.services._service_utils import boto3_client, boto3_resource, get_region

_logger: logging.Logger = logging.getLogger(__name__)


def get_role(role_name: str) -> Optional[Dict[str, Any]]:
    _logger.debug(f"Getting Role: {role_name}")

    iam_client = boto3_client("iam")
    try:
        return cast(Dict[str, Any], iam_client.get_role(RoleName=role_name))
    except iam_client.exceptions.NoSuchEntityException:
        return None


def create_check_iam_role(trust_policy: Dict[str, Any], role_name: str, permission_boundary_arn: Optional[str]) -> None:
    _logger.debug(f"Creating IAM Role with name: {role_name}")
    iam_client = boto3_client("iam")
    try:
        iam_client.get_role(RoleName=role_name)
    except iam_client.exceptions.NoSuchEntityException:
        args = {
            "RoleName": role_name,
            "AssumeRolePolicyDocument": json.dumps(trust_policy),
            "Description": f"deployment-role for {role_name}",
            "Tags": [{"Key": "Region", "Value": get_region()}],
        }
        if permission_boundary_arn:
            args["PermissionsBoundary"] = permission_boundary_arn
        iam_client.create_role(**args)


def attach_policy_to_role(role_name: str, policies: List[str]) -> None:
    iam_client = boto3_client("iam")
    try:
        response = iam_client.list_attached_role_policies(RoleName=role_name)
        attached_policies = [i["PolicyArn"] for i in response["AttachedPolicies"] if response["AttachedPolicies"]]
        _logger.debug(f"List of Attached Policie(s) are: {attached_policies}")
        if attached_policies:
            to_be_attached = list(set(policies) - set(attached_policies))
            _logger.debug(f"To be attached policie(s) are: {to_be_attached}")
            for policy in to_be_attached:
                iam_client.attach_role_policy(RoleName=role_name, PolicyArn=policy)
                _logger.debug(f"Attached the policy: {policy}")
        else:
            _logger.debug(f"First time deployment, attaching the policies: {policies}")
            for policy in policies:
                iam_client.attach_role_policy(RoleName=role_name, PolicyArn=policy)
                _logger.debug(f"Attached the policy: {policy}")
    except Exception as e:
        raise e


def attach_inline_policy(role_name: str, policy_body: str, policy_name: str) -> None:
    iam_client = boto3_client("iam")
    _logger.debug(f"Attaching the Inline policy {policy_name} to the IAM Role: {role_name}")
    try:
        iam_client.put_role_policy(RoleName=role_name, PolicyName=policy_name, PolicyDocument=policy_body)
    except Exception as e:
        _logger.debug(f"Failed to attach the Inline policy {policy_name} to the IAM Role: {role_name}")
        raise e


def detach_policy_from_role(role_name: str, policy_arn: str) -> None:
    _logger.debug(f"Detatching policy: {policy_arn} from the IAM Role: {role_name}")
    iam_client = boto3_client("iam")
    try:
        iam_client.detach_role_policy(RoleName=role_name, PolicyArn=policy_arn)
    except Exception as e:
        _logger.info(f"Could not delete policy : {policy_arn}")
        _logger.info(f"Caught exception: {e}")


def delete_role(role_name: str) -> None:
    iam_client = boto3_client("iam")
    try:
        iam_client.delete_role(RoleName=role_name)
    except iam_client.exceptions.NoSuchEntityException as e:
        _logger.info(f"Could not delete role : {role_name}")
        _logger.info(f"Caught exception: {e}")


def detach_inline_policy_from_role(role_name: str, policy_name: str) -> None:
    iam_resource = boto3_resource("iam")
    try:
        iam_resource.RolePolicy(role_name, policy_name).delete()
    except Exception as e:
        raise e
