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
from typing import List, Optional

import click

from seedfarmer import DEBUG_LOGGING_FORMAT, config, enable_debug
from seedfarmer.commands import bootstrap_target_account, bootstrap_toolchain_account
from seedfarmer.output_utils import print_bolded

_logger: logging.Logger = logging.getLogger(__name__)


def _load_project() -> str:
    try:
        _logger.info("No --project provided, attempting load from seedfarmer.yaml")
        return config.PROJECT
    except FileNotFoundError:
        print_bolded("Unable to determine project to bootstrap, one of --project or a seedfarmer.yaml is required")
        raise click.ClickException("Failed to determine project identifier")


@click.group(name="bootstrap", help="Bootstrap (initialize) a Toolchain or Target account")
def bootstrap() -> None:
    """Bootstrap a Toolchain or Target account"""
    pass


@bootstrap.command(
    name="toolchain",
    help="Bootstrap a Toolchain account.",
)
@click.option(
    "--project",
    "-p",
    help="Project identifier",
    required=False,
    default=None,
)
@click.option(
    "--trusted-principal",
    "-t",
    help="""ARN of Principals trusted to assume the Toolchain Role.
    This can be used multiple times to create a list.""",
    multiple=True,
    required=True,
)
@click.option(
    "--permissions-boundary",
    "-b",
    help="ARN of a Managed Policy to set as the Permission Boundary on the Toolchain Role",
    required=False,
    default=None,
)
@click.option(
    "--as-target/--not-as-target",
    type=bool,
    default=False,
    help="Optionally also bootstrap the account as a Target account",
    required=False,
    show_default=True,
)
@click.option(
    "--synth/--no-synth",
    type=bool,
    default=False,
    help="Synthesize a CFN bootstrap template only...do not deploy",
    required=False,
    show_default=True,
)
@click.option(
    "--profile",
    default=None,
    help="The AWS profile to use to initiate a session",
    required=False,
)
@click.option(
    "--region",
    default=None,
    help="AWS region to use to initiate a session",
    required=False,
)
@click.option(
    "--qualifier",
    default=None,
    help="""A qualifier to append to toolchain role (alpha-numeric char max length of 6).
    If used, it MUST be used on every seedfarmer command.""",
    required=False,
)
@click.option(
    "--role-prefix",
    default=None,
    help="An IAM path prefix to use with the seedfarmer roles.",
    required=False,
)
@click.option(
    "--policy-prefix",
    default=None,
    help="An IAM path prefix to use with the seedfarmer policies.",
    required=False,
)
@click.option(
    "--policy-arn",
    "-pa",
    help="""ARN of existing Policy to attach to Target Role (Deploymenmt Role)
    This can be use multiple times, but EACH policy MUST be valid in the Target Account.
    The `--as-target` flag must be used if passing in policy arns as they are applied to
    the Deployment Role only.""",
    multiple=True,
    required=False,
    default=[],
)
@click.option("--debug/--no-debug", default=False, help="Enable detail logging", show_default=True)
def bootstrap_toolchain(
    project: Optional[str],
    trusted_principal: List[str],
    permissions_boundary: Optional[str],
    policy_arn: Optional[List[str]],
    profile: Optional[str],
    region: Optional[str],
    qualifier: Optional[str],
    role_prefix: Optional[str],
    policy_prefix: Optional[str],
    as_target: bool,
    synth: bool,
    debug: bool,
) -> None:
    if debug:
        enable_debug(format=DEBUG_LOGGING_FORMAT)
    if project is None:
        project = _load_project()
    _logger.debug("Bootstrapping a Toolchain account for Project %s", project)
    if len(policy_arn) > 0 and not as_target:  # type: ignore
        raise click.ClickException("Cannot set PolicyARNS when the `-as-target` flag is not set.")

    bootstrap_toolchain_account(
        project_name=project,
        principal_arns=trusted_principal,
        permissions_boundary_arn=permissions_boundary,
        policy_arns=policy_arn,
        profile=profile,
        qualifier=qualifier,
        role_prefix=role_prefix,
        policy_prefix=policy_prefix,
        region_name=region,
        synthesize=synth,
        as_target=as_target,
    )


@bootstrap.command(
    name="target",
    help="Bootstrap a Target account.",
)
@click.option(
    "--project",
    "-p",
    help="Project identifier",
    required=False,
    default=None,
)
@click.option(
    "--toolchain-account",
    "-t",
    required=True,
    help="Account Id of the Toolchain account trusted to assume the Target account's Deployment Role",
)
@click.option(
    "--permissions-boundary",
    "-b",
    help="ARN of a Managed Policy to set as the Permission Boundary on the Toolchain Role",
    required=False,
    default=None,
)
@click.option(
    "--synth/--no-synth",
    type=bool,
    default=False,
    help="Synthesize a CFN template only...do not deploy",
    required=False,
    show_default=True,
)
@click.option(
    "--profile",
    default=None,
    help="The AWS profile to use to initiate a session",
    required=False,
)
@click.option(
    "--region",
    default=None,
    help="AWS region to use to initiate a session",
    required=False,
)
@click.option(
    "--qualifier",
    default=None,
    help="""A qualifier to append to target role (alpha-numeric char max length of 6).
    If used on the toolchain account, it should be used here!""",
    required=False,
)
@click.option(
    "--role-prefix",
    default=None,
    help="An IAM path prefix to use with the seedfarmer roles.",
    required=False,
)
@click.option(
    "--policy-arn",
    "-pa",
    help="""ARN of existing Policy to attach to Target Role (Deploymenmt Role)
    This can be use multiple times to create a list, but EACH policy MUST be valid in the Target Account""",
    multiple=True,
    required=False,
    default=[],
)
@click.option("--debug/--no-debug", default=False, help="Enable detail logging", show_default=True)
def bootstrap_target(
    project: Optional[str],
    toolchain_account: str,
    permissions_boundary: Optional[str],
    policy_arn: Optional[List[str]],
    profile: Optional[str],
    region: Optional[str],
    qualifier: Optional[str],
    role_prefix: Optional[str],
    synth: bool,
    debug: bool,
) -> None:
    if debug:
        enable_debug(format=DEBUG_LOGGING_FORMAT)
    if project is None:
        project = _load_project()
    _logger.debug("Bootstrapping a Target account for Project %s", project)
    bootstrap_target_account(
        toolchain_account_id=toolchain_account,
        project_name=project,
        profile=profile,
        region_name=region,
        qualifier=qualifier,
        role_prefix=role_prefix,
        permissions_boundary_arn=permissions_boundary,
        policy_arns=policy_arn,
        synthesize=synth,
    )
