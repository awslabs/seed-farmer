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
        print_bolded("No --project provided, attempting load from seedfarmer.yaml", "white")
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
    help="ARN of Principals trusted to assume the Toolchain Role",
    multiple=True,
    required=False,
    default=[],
)
@click.option(
    "--permission-boundary",
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
)
@click.option(
    "--synth/--no-synth",
    type=bool,
    default=False,
    help="Synthesize a CFN template only...do not deploy",
    required=False,
)
@click.option(
    "--profile",
    default=None,
    help="The AWS profile to initiate a session",
    required=False,
)
@click.option("--debug/--no-debug", default=False, help="Enable detail logging", show_default=True)
def bootstrap_toolchain(
    project: Optional[str],
    trusted_principal: List[str],
    permission_boundary: Optional[str],
    profile: Optional[str],
    as_target: bool,
    synth: bool,
    debug: bool,
) -> None:
    if debug:
        enable_debug(format=DEBUG_LOGGING_FORMAT)
    if project is None:
        project = _load_project()
    _logger.debug("Bootstrapping a Toolchain account for Project %s", project)
    bootstrap_toolchain_account(
        project_name=project,
        principal_arns=trusted_principal,
        permissions_boundary_arn=permission_boundary,
        profile=profile,
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
    "--permission-boundary",
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
)
@click.option(
    "--profile",
    default=None,
    help="The AWS profile to initiate a session",
    required=False,
)
@click.option("--debug/--no-debug", default=False, help="Enable detail logging", show_default=True)
def bootstrap_target(
    project: Optional[str],
    toolchain_account: str,
    permission_boundary: Optional[str],
    profile: Optional[str],
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
        permissions_boundary_arn=permission_boundary,
        synthesize=synth,
    )
