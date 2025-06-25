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

import datetime as dt
import logging
import os
import time
from typing import TYPE_CHECKING, Any, Callable, Dict, Optional, Tuple, Union, cast

import botocore.exceptions
from boto3 import Session

import seedfarmer.services._s3 as s3
from seedfarmer.services._service_utils import boto3_client

_logger: logging.Logger = logging.getLogger(__name__)


if TYPE_CHECKING:
    from mypy_boto3_cloudformation.waiter import StackCreateCompleteWaiter, StackUpdateCompleteWaiter

CHANGESET_PREFIX = "aws-codeseeder-"


def _wait_for_changeset(
    changeset_id: str, stack_name: str, session: Optional[Union[Callable[[], Session], Session]] = None
) -> bool:
    waiter = boto3_client("cloudformation", session=session).get_waiter("change_set_create_complete")
    try:
        waiter.wait(ChangeSetName=changeset_id, StackName=stack_name, WaiterConfig={"Delay": 1})
    except botocore.exceptions.WaiterError as ex:
        resp = ex.last_response
        status = resp["Status"]
        reason = resp["StatusReason"]
        if status == "FAILED" and (
            "The submitted information didn't contain changes." in reason or "No updates are to be performed" in reason
        ):
            _logger.debug(f"No changes for {stack_name} CloudFormation stack.")
            return False
        raise RuntimeError(f"Failed to create the changeset: {ex}. Status: {status}. Reason: {reason}")
    return True


def _create_changeset(
    stack_name: str,
    template_str: str,
    seedkit_tag: Optional[str] = None,
    template_path: str = "",
    parameters: Optional[Dict[str, str]] = None,
    session: Optional[Union[Callable[[], Session], Session]] = None,
) -> Tuple[str, str]:
    now: str = dt.datetime.now(tz=dt.timezone.utc).isoformat()
    description = f"Created by SeedFarmer at {now} UTC"
    changeset_name = CHANGESET_PREFIX + str(int(time.time()))
    stack_exist, _ = does_stack_exist(stack_name=stack_name, session=session)
    changeset_type = "UPDATE" if stack_exist else "CREATE"
    kwargs: Dict[str, Any] = {
        "ChangeSetName": changeset_name,
        "StackName": stack_name,
        "ChangeSetType": changeset_type,
        "Capabilities": ["CAPABILITY_IAM", "CAPABILITY_NAMED_IAM"],
        "Description": description,
    }
    if seedkit_tag:
        kwargs.update({"Tags": [{"Key": "codeseeder-seedkit", "Value": seedkit_tag}]})
    if template_str:
        kwargs.update({"TemplateBody": template_str})
    elif template_path:
        _logger.info(f"template_path={template_path}")
        kwargs.update({"TemplateURL": template_path})
    if parameters:
        kwargs.update({"Parameters": [{"ParameterKey": k, "ParameterValue": v} for k, v in parameters.items()]})
    resp = boto3_client("cloudformation", session=session).create_change_set(**kwargs)
    return str(resp["Id"]), changeset_type


def _execute_changeset(
    changeset_id: str, stack_name: str, session: Optional[Union[Callable[[], Session], Session]] = None
) -> None:
    boto3_client("cloudformation", session=session).execute_change_set(ChangeSetName=changeset_id, StackName=stack_name)


def _wait_for_execute(
    stack_name: str, changeset_type: str, session: Optional[Union[Callable[[], Session], Session]] = None
) -> None:
    waiter: Union["StackCreateCompleteWaiter", "StackUpdateCompleteWaiter"]
    if changeset_type == "CREATE":
        waiter = boto3_client("cloudformation", session=session).get_waiter("stack_create_complete")
    elif changeset_type == "UPDATE":
        waiter = boto3_client("cloudformation", session=session).get_waiter("stack_update_complete")
    else:
        raise RuntimeError(f"Invalid changeset type {changeset_type}")

    waiter.wait(
        StackName=stack_name,
        WaiterConfig={
            "Delay": 5,
            "MaxAttempts": 480,
        },
    )


def get_stack_name(seedkit_name: str) -> str:
    """Helper function to calculate the name of a CloudFormation Stack for a given Seedkit

    Parameters
    ----------
    seedkit_name : str
        Name of the Seedkit

    Returns
    -------
    str
        Name of the Stack Name associated with the Seedkit
    """
    return f"aws-codeseeder-{seedkit_name}"


def get_stack_status(stack_name: str, session: Optional[Union[Callable[[], Session], Session]] = None) -> str:
    """Retrieve the status of a CloudFormation Stack

    Parameters
    ----------
    stack_name : str
        Name of the CloudFormation Stack to query
    session: Optional[Union[Callable[[], Session], Session]], optional
        Optional Session or function returning a Session to use for all boto3 operations, by default None

    Returns
    -------
    str
        The status of the CloudFormation Stack, see official ``boto3`` documentation for potential status values:
        https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/cloudformation.html#CloudFormation.Client.describe_stacks

    Raises
    ------
    ValueError
        If the Stack is not found
    """
    client = boto3_client("cloudformation", session=session)
    try:
        resp = client.describe_stacks(StackName=stack_name)
        if len(resp["Stacks"]) < 1:
            raise ValueError(f"CloudFormation stack {stack_name} not found.")
    except botocore.exceptions.ClientError:
        raise
    return cast(str, resp["Stacks"][0]["StackStatus"])


def does_stack_exist(
    stack_name: str, session: Optional[Union[Callable[[], Session], Session]] = None
) -> Tuple[bool, Dict[str, str]]:
    """Checks for existence of a CloudFormation Stack while also returning Stack Outputs if it does exist

    Parameters
    ----------
    stack_name : str
        Name of the CloudFormation Stack to query
    session: Optional[Union[Callable[[], Session], Session]], optional
        Optional Session or function returning a Session to use for all boto3 operations, by default None

    Returns
    -------
    Tuple[bool, Dict[str, str]]
        Tuple2 with a boolean indicating Stack existence and a dict of any Stack Outputs
    """
    client = boto3_client("cloudformation", session=session)
    try:
        resp = client.describe_stacks(StackName=stack_name)
        if len(resp["Stacks"]) < 1:
            return (False, {})
        else:
            output = {o["OutputKey"]: o["OutputValue"] for o in resp["Stacks"][0].get("Outputs", [])}
            output["StackStatus"] = resp["Stacks"][0]["StackStatus"]
            return (True, output)
    except botocore.exceptions.ClientError as ex:
        error = ex.response["Error"]
        if error["Code"] == "ValidationError" and f"Stack with id {stack_name} does not exist" in error["Message"]:
            return (False, {})
        raise


def deploy_template(
    stack_name: str,
    filename: str,
    seedkit_tag: Optional[str] = None,
    s3_bucket: Optional[str] = None,
    parameters: Optional[Dict[str, str]] = None,
    session: Optional[Union[Callable[[], Session], Session]] = None,
) -> None:
    """Deploy a local CloudFormation Template

    The function will automatically calculate a ChangeSet if the Stack already exists and update accordingly. If the
    local template file is too large, it will be uploaded to the optional ``s3_buckeet`` and deployed from there.

    Parameters
    ----------
    stack_name : str
        Name of the CloudFormation Stack to deploy
    filename : str
        Name of the local CloudFormation template file
    seedkit_tag : Optional[str], optional
        Name of the Seedkit to Tag resources in the Stack with, by default None
    s3_bucket : Optional[str], optional
        S3 Bucket to upload the template file to if it is too large (> 51200), by default None
    parameters: Optional[Dict[str, str]], optional
        Key/Value set of Input Parameters to pass to the CloudFormation stack, by default None
    session: Optional[Union[Callable[[], Session], Session]], optional
        Optional Session or function returning a Session to use for all boto3 operations, by default None

    Raises
    ------
    FileNotFoundError
        If the local template file is not found
    ValueError
        If the S3 Bucket is not found
    """
    _logger.debug("Deploying template %s", filename)
    if not os.path.isfile(filename):
        raise FileNotFoundError(f"CloudFormation template not found at {filename}")
    template_size = os.path.getsize(filename)
    if template_size > 51_200:
        if s3_bucket is None:
            raise ValueError("s3_bucket argument is required when template size > 51 200 bytes")
        _logger.info(f"The CloudFormation template ({filename}) is too big to be deployed, using s3 bucket.")
        local_template_path = filename
        s3_file_name = filename.split("/")[-1]
        key = f"cli/remote/demo/{s3_file_name}"
        s3_template_path = f"https://s3.amazonaws.com/{s3_bucket}/{key}"
        _logger.debug("s3_template_path: %s", s3_template_path)
        s3.upload_file(src=local_template_path, bucket=s3_bucket, key=key, session=session)
        changeset_id, changeset_type = _create_changeset(
            stack_name=stack_name,
            template_str="",
            seedkit_tag=seedkit_tag,
            template_path=s3_template_path,
            parameters=parameters,
            session=session,
        )
    else:
        with open(filename, "r") as handle:
            template_str = handle.read()
        changeset_id, changeset_type = _create_changeset(
            stack_name=stack_name,
            template_str=template_str,
            seedkit_tag=seedkit_tag,
            parameters=parameters,
            session=session,
        )
    has_changes = _wait_for_changeset(changeset_id, stack_name, session=session)
    if has_changes:
        _execute_changeset(changeset_id=changeset_id, stack_name=stack_name, session=session)
        _wait_for_execute(stack_name=stack_name, changeset_type=changeset_type, session=session)


def destroy_stack(stack_name: str, session: Optional[Union[Callable[[], Session], Session]] = None) -> None:
    """Destroy the CloudFormation Stack

    Parameters
    ----------
    stack_name : str
        Name of the CloudFormation Stack to destroy
    session: Optional[Union[Callable[[], Session], Session]], optional
        Optional Session or function returning a Session to use for all boto3 operations, by default None
    """
    _logger.debug("Destroying stack %s", stack_name)
    client = boto3_client("cloudformation", session=session)
    client.delete_stack(StackName=stack_name)
    waiter = client.get_waiter("stack_delete_complete")
    waiter.wait(StackName=stack_name, WaiterConfig={"Delay": 5, "MaxAttempts": 200})
