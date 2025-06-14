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

from typing import Optional, Tuple

import click

import seedfarmer.commands._seedkit_commands as sk_commands
from seedfarmer.services.session_manager import SessionManager, SessionManagerLocalImpl

# _logger: logging.Logger = logging.getLogger(__name__)


@click.group(name="seedkit", help="Top Level command to support seedkits in SeedFarmer")
def seedkit() -> None:
    "Manage the seedkit"
    pass


@seedkit.command(
    name="deploy",
    help="""Deploy a seedkit in the specified account and region.  There can
            be only one per seedfarmer project and is region-based.
            """,
)
@click.argument(
    "project_name",
    type=str,
    required=True,
)
@click.option("--policy-arn", required=False, type=str, multiple=True, default=[])
@click.option(
    "--deploy-codeartifact/--skip-codeartifact",
    default=False,
    help="Deploy the optional CodeArtifact Domain and Repository",
    show_default=True,
)
@click.option(
    "--profile",
    default=None,
    help="AWS Credentials profile to use for boto3 commands",
    show_default=True,
)
@click.option(
    "--region",
    default=None,
    help="AWS region to use for boto3 commands",
    show_default=True,
)
@click.option(
    "--vpc-id",
    help="The VPC ID that the Codebuild Project resides in (only 1)",
    required=False,
    default=None,
)
@click.option(
    "--subnet-id",
    help="A subnet that the Codebuild Project resides in (many can be passed in)",
    multiple=True,
    required=False,
    default=[],
)
@click.option(
    "--sg-id",
    help="A Securtiy Group in the VPC that the Codebuild Project can leverage (up to 5)",
    multiple=True,
    required=False,
    default=[],
)
@click.option(
    "--permissions-boundary-arn",
    "-b",
    help="ARN of a Managed Policy to set as the Permission Boundary on the CodeBuild Role",
    required=False,
    default=None,
)
@click.option(
    "--synth/--no-synth",
    type=bool,
    default=False,
    help="Synthesize seedkit template only. Do not deploy",
    required=False,
    show_default=True,
)
@click.option(
    "--debug/--no-debug",
    default=False,
    help="Enable detailed logging.",
    show_default=True,
)
def deploy_seedkit(
    project_name: str,
    policy_arn: Tuple[str, ...],
    deploy_codeartifact: bool,
    profile: Optional[str],
    region: Optional[str],
    debug: bool,
    vpc_id: Optional[str],
    subnet_id: Tuple[str, ...],
    sg_id: Tuple[str, ...],
    permissions_boundary_arn: Optional[str],
    synth: bool,
) -> None:
    SessionManager.bind(SessionManagerLocalImpl())  # should ALWAYS use local profile info
    session = SessionManager().get_or_create(region_name=region, profile=profile).toolchain_session
    sk_commands.deploy_seedkit(
        seedkit_name=project_name,
        managed_policy_arns=[p for p in policy_arn],
        deploy_codeartifact=deploy_codeartifact,
        session=session,
        vpc_id=vpc_id,
        subnet_ids=[s for s in subnet_id],
        security_group_ids=[sg for sg in sg_id],
        permissions_boundary_arn=permissions_boundary_arn,
        synthesize=synth,
    )


@seedkit.command(name="destroy")
@click.argument(
    "project_name",
    type=str,
    required=True,
)
@click.option(
    "--profile",
    default=None,
    help="AWS Credentials profile to use for boto3 commands",
    show_default=True,
)
@click.option(
    "--region",
    default=None,
    help="AWS region to use for boto3 commands",
    show_default=True,
)
@click.option(
    "--debug/--no-debug",
    default=False,
    help="Enable detailed logging.",
    show_default=True,
)
def destroy_seedkit(project_name: str, profile: Optional[str], region: Optional[str], debug: bool) -> None:
    SessionManager.bind(SessionManagerLocalImpl())
    session = SessionManager().get_or_create(region_name=region, profile=profile).toolchain_session
    sk_commands.destroy_seedkit(seedkit_name=project_name, session=session)
