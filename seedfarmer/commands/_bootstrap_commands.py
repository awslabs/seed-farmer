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
#
import json
import logging
import os
import re
import sys
from typing import Any, Dict, List, Optional, Tuple, cast

import yaml
from aws_codeseeder import services as cs_services
from boto3 import Session
from botocore.exceptions import WaiterError
from jinja2 import Template

import seedfarmer.errors
from seedfarmer import CLI_ROOT, __version__
from seedfarmer.services import create_new_session, get_region, get_sts_identity_info
from seedfarmer.services._iam import get_role
from seedfarmer.utils import get_deployment_role_name, get_toolchain_role_arn, get_toolchain_role_name, valid_qualifier

_logger: logging.Logger = logging.getLogger(__name__)


def get_toolchain_template(
    project_name: str,
    principal_arn: List[str],
    role_name: str,
    permissions_boundary_arn: Optional[str] = None,
) -> Dict[Any, Any]:
    with open((os.path.join(CLI_ROOT, "resources/toolchain_role.template")), "r") as f:
        role = yaml.safe_load(f)
    if principal_arn:
        role["Resources"]["ToolchainRole"]["Properties"]["AssumeRolePolicyDocument"]["Statement"][0]["Principal"][
            "AWS"
        ] = principal_arn
    if permissions_boundary_arn:
        role["Resources"]["ToolchainRole"]["Properties"]["PermissionsBoundary"] = permissions_boundary_arn
    template = Template(json.dumps(role))
    t = template.render({"project_name": project_name, "role_name": role_name, "seedfarmer_version": __version__})
    return dict(json.loads(t))


def get_deployment_template(
    toolchain_role_arn: str,
    project_name: str,
    role_name: str,
    policy_arns: Optional[List[str]],
    permissions_boundary_arn: Optional[str] = None,
) -> Dict[Any, Any]:
    with open((os.path.join(CLI_ROOT, "resources/deployment_role.template")), "r") as f:
        role = yaml.safe_load(f)
    if permissions_boundary_arn:
        role["Resources"]["DeploymentRole"]["Properties"]["PermissionsBoundary"] = permissions_boundary_arn
    if policy_arns:
        role["Resources"]["DeploymentRole"]["Properties"]["ManagedPolicyArns"] = policy_arns
    template = Template(json.dumps(role))
    t = template.render(
        {
            "toolchain_role_arn": toolchain_role_arn,
            "project_name": project_name,
            "role_name": role_name,
            "seedfarmer_version": __version__,
        }
    )
    return dict(json.loads(t))


def write_template(template: Dict[Any, Any]) -> None:
    yaml.dump(template, sys.stdout)
    print("")


def bootstrap_toolchain_account(
    project_name: str,
    principal_arns: List[str],
    permissions_boundary_arn: Optional[str] = None,
    policy_arns: Optional[List[str]] = None,
    qualifier: Optional[str] = None,
    profile: Optional[str] = None,
    region_name: Optional[str] = None,
    synthesize: bool = False,
    as_target: bool = False,
) -> Optional[Dict[Any, Any]]:
    if qualifier and not valid_qualifier(qualifier):
        raise seedfarmer.errors.InvalidConfigurationError("The Qualifier must be alphanumeric and 6 characters or less")

    for arn in principal_arns:
        if not re.match(r"arn:aws.*:(sts|iam)::(\d{12}|\*):.*$", arn):
            raise seedfarmer.errors.InvalidConfigurationError(f"Trusted principal: {arn} is not a valid principal arn")

    role_stack_name = get_toolchain_role_name(project_name=project_name, qualifier=cast(str, qualifier))
    template = get_toolchain_template(
        project_name=project_name,
        role_name=role_stack_name,
        principal_arn=principal_arns,
        permissions_boundary_arn=permissions_boundary_arn,
    )
    _logger.debug((json.dumps(template, indent=4)))
    if not synthesize:
        session = create_new_session(profile=profile, region_name=region_name)
        session_account_id, session_role_arn, partition = get_sts_identity_info(session=session)
        apply_deploy_logic(
            template=template,
            role_name=role_stack_name,
            stack_name=role_stack_name,
            session=session,
            account_id=session_account_id,
        )
        if as_target:
            bootstrap_target_account(
                toolchain_account_id=session_account_id,
                project_name=project_name,
                qualifier=cast(str, qualifier),
                permissions_boundary_arn=permissions_boundary_arn,
                profile=profile,
                region_name=region_name,
                policy_arns=policy_arns,
                session=session,
            )
    else:
        write_template(template=template)
        if as_target:
            bootstrap_target_account(
                toolchain_account_id="123456789012",
                project_name=project_name,
                qualifier=cast(str, qualifier),
                permissions_boundary_arn=permissions_boundary_arn,
                policy_arns=policy_arns,
                profile=profile,
                region_name=region_name,
                session=None,
                synthesize=synthesize,
            )
    return template


def bootstrap_target_account(
    toolchain_account_id: str,
    project_name: str,
    permissions_boundary_arn: Optional[str] = None,
    qualifier: Optional[str] = None,
    profile: Optional[str] = None,
    region_name: Optional[str] = None,
    session: Optional[Session] = None,
    policy_arns: Optional[List[str]] = None,
    synthesize: bool = False,
) -> Optional[Dict[Any, Any]]:
    if qualifier and not valid_qualifier(qualifier):
        raise seedfarmer.errors.InvalidConfigurationError("The Qualifier must be alphanumeric and 6 characters or less")

    if not session:
        session = create_new_session(profile=profile, region_name=region_name)
    session_account_id, session_role_arn, partition = get_sts_identity_info(session=session)

    role_stack_name = get_deployment_role_name(project_name=project_name, qualifier=cast(str, qualifier))
    toolchain_role_arn = get_toolchain_role_arn(
        partition=partition,
        toolchain_account_id=toolchain_account_id,
        project_name=project_name,
        qualifier=cast(str, qualifier),
    )

    template = get_deployment_template(
        toolchain_role_arn=toolchain_role_arn,
        project_name=project_name,
        role_name=role_stack_name,
        policy_arns=policy_arns if policy_arns else None,
        permissions_boundary_arn=permissions_boundary_arn,
    )
    _logger.debug((json.dumps(template, indent=4)))
    if not synthesize:
        apply_deploy_logic(
            template=template,
            role_name=role_stack_name,
            stack_name=role_stack_name,
            session=session,
            account_id=session_account_id,
        )
    else:
        write_template(template=template)
    return template


def apply_deploy_logic(
    template: Dict[Any, Any], role_name: str, stack_name: str, session: Session, account_id: Optional[str] = None
) -> None:
    role_exists, stack_exists = role_deploy_status(role_name=role_name, stack_name=stack_name, session=session)
    if not account_id:
        account_id, role_arn, partition = get_sts_identity_info(session=session)
    if not role_exists:
        _logger.info("Deploying role in account %s, region %s", account_id, get_region(session=session))
        deploy_template(template=template, stack_name=stack_name, session=session)
    else:
        if stack_exists[0]:
            _logger.info("Updating role in account %s, region %s", account_id, get_region(session=session))
            deploy_template(template=template, stack_name=stack_name, session=session)
        else:
            _logger.info(
                "The role %s exists in account %s as was not deployed in region %s, it will NOT be updated",
                role_name,
                account_id,
                get_region(session=session),
            )


def deploy_template(template: Dict[Any, Any], stack_name: str, session: Optional[Session]) -> None:
    loc = os.path.join(os.getcwd(), "templates")
    output = os.path.join(loc, f"{stack_name}.yaml")
    os.makedirs(loc, exist_ok=True)
    with open(output, "w") as outfile:
        yaml.dump(template, outfile)
    try:
        cs_services.set_boto3_session(session) if session else None
        cs_services.cfn.deploy_template(
            stack_name=stack_name,
            filename=output,
        )
        _logger.info(f"Role for Seed-Farmer deployed in stack {stack_name}")
    except WaiterError as we:
        _logger.error("Could not create the deployment role...make sure the toolchain role exists and check CFN Logs")
        raise we
    finally:
        os.remove(output)


def role_deploy_status(role_name: str, stack_name: str, session: Session) -> Tuple[Optional[Dict[str, Any]], Any]:
    return get_role(role_name=role_name, session=session), cs_services.cfn.does_stack_exist(
        stack_name=stack_name, session=session
    )
