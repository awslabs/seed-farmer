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

import click

from seedfarmer import DEBUG_LOGGING_FORMAT, enable_debug
from seedfarmer.commands import get_default_project_policy

_logger: logging.Logger = logging.getLogger(__name__)


@click.group(
    name="projectpolicy",
    help="""Fetch info about the project policy.
      This will output the default provided project polocy that can be customized.""",
)
def projectpolicy() -> None:
    """Get info about the Project Policy"""
    pass


@projectpolicy.command(
    name="synth",
    help="Synth a Project Policy from seed-farmer.",
)
@click.option(
    "--policy-prefix",
    default="/",
    help="An IAM path prefix to use with the policy.",
    required=False,
)
@click.option("--debug/--no-debug", default=False, help="Enable detail logging", show_default=True)
def policy_synth(
    policy_prefix: str,
    debug: bool,
) -> None:
    if debug:
        enable_debug(format=DEBUG_LOGGING_FORMAT)

    get_default_project_policy(policy_prefix=policy_prefix)
