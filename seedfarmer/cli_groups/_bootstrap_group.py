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

from seedfarmer import DEBUG_LOGGING_FORMAT, enable_debug
from seedfarmer.config import PROJECT

_logger: logging.Logger = logging.getLogger(__name__)


@click.group(name="bootstrap", help="Bootstrap (initialize) a Toolchain or Target account")
def bootstrap() -> None:
    f"""Bootstrap a Toolchain or Target account for project {PROJECT.upper()}"""
    pass


@bootstrap.command(
    name="toolchain",
    help="Bootstrap a Toolchain account.",
)
@click.argument("project", type=str, required=True)
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
    "-p",
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
@click.option("--debug/--no-debug", default=False, help="Enable detail logging", show_default=True)
def bootstrap_toolchain(
    project: str, trusted_principal: List[str], permission_boundary: Optional[str], as_target: bool, debug: bool
) -> None:
    if debug:
        enable_debug(format=DEBUG_LOGGING_FORMAT)
    _logger.debug("Bootstrapping a Toolchain account for Project %s", project)
    pass


@bootstrap.command(
    name="target",
    help="Bootstrap a Target account.",
)
@click.argument("project", type=str, required=True)
@click.option(
    "--toolchain-account",
    "-t",
    required=True,
    help="Account Id of the Toolchain account trusted to assume the Target account's Deployment Role",
)
@click.option(
    "--permission-boundary",
    "-p",
    help="ARN of a Managed Policy to set as the Permission Boundary on the Toolchain Role",
    required=False,
    default=None,
)
@click.option("--debug/--no-debug", default=False, help="Enable detail logging", show_default=True)
def bootstrap_target(project: str, toolchain_account: str, permission_boundary: Optional[str], debug: bool) -> None:
    if debug:
        enable_debug(format=DEBUG_LOGGING_FORMAT)
    _logger.debug("Bootstrapping a Target account for Project %s", project)
    pass
