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
from typing import Optional

import click
from boto3 import Session

import seedfarmer.errors
import seedfarmer.mgmt.module_info as mi
from seedfarmer import DEBUG_LOGGING_FORMAT, config, enable_debug
from seedfarmer.output_utils import print_bolded
from seedfarmer.services.session_manager import SessionManager, bind_session_mgr

_logger: logging.Logger = logging.getLogger(__name__)


def _load_project() -> str:
    try:
        _logger.info("No --project provided, attempting load from seedfarmer.yaml")
        return config.PROJECT
    except FileNotFoundError:
        print_bolded("Unable to determine project to bootstrap, one of --project or a seedfarmer.yaml is required")
        raise click.ClickException("Failed to determine project identifier")


@click.group(name="remove", help="Top Level command to support removing module metadata")
def remove() -> None:
    """Remove module data"""
    pass


@remove.command(
    name="moduledata",
    help="""Remove all SSM parameters tied to the module.
        This command is meant to be run by seedfarmer ONLY!!!
        It is run within the context of the build job.
        Do not use this unless you are sure of the ramifications!
        """,
)
@click.option(
    "--deployment",
    "-d",
    type=str,
    help="The Deployment Name",
    required=True,
)
@click.option(
    "--group",
    "-g",
    type=str,
    help="The Group Name",
    required=True,
)
@click.option(
    "--module",
    "-m",
    type=str,
    help="The Module Name",
    required=True,
)
@click.option(
    "--project",
    "-p",
    help="Project identifier",
    required=False,
    default=None,
)
@click.option(
    "--profile",
    default=None,
    help="""The AWS profile used to create a session.""",
    required=False,
)
@click.option(
    "--region",
    default=None,
    help="""The AWS region used to create a session.""",
    required=False,
)
@click.option(
    "--qualifier",
    default=None,
    help="A qualifier to use with the seedfarmer roles",
    required=False,
)
@click.option(
    "--target-account-id",
    default=None,
    help="Account Id to remove module data from, if specifed --target-region is required",
    show_default=True,
)
@click.option(
    "--target-region",
    default=None,
    help="Region to remove module data from, if specifed --target-account-id is required",
    show_default=True,
)
@click.option(
    "--debug/--no-debug",
    default=False,
    help="Enable detailed logging.",
    show_default=True,
)
@click.option(
    "--local/--remote",
    default=False,
    help="Indicates whether to use local session role or the SeedFarmer roles",
    show_default=True,
    type=bool,
)
@bind_session_mgr
def remove_module_data(
    deployment: str,
    group: str,
    module: str,
    profile: Optional[str],
    region: Optional[str],
    qualifier: Optional[str],
    project: Optional[str],
    target_account_id: Optional[str],
    target_region: Optional[str],
    debug: bool,
    local: bool,
) -> None:
    if debug:
        enable_debug(format=DEBUG_LOGGING_FORMAT)
    _logger.debug("We are removing module data for %s of group %s in %s", module, group, deployment)

    if project is None:
        project = _load_project()

    session: Session = Session(profile_name=profile, region_name=region)
    if (target_account_id is not None) != (target_region is not None):
        raise seedfarmer.errors.InvalidConfigurationError(
            "Must either specify both --target-account-id and --target-region, or neither"
        )
    elif target_account_id is not None and target_region is not None:
        session = (
            SessionManager()
            .get_or_create(project_name=project, profile=profile, region_name=region, qualifier=qualifier)
            .get_deployment_session(account_id=target_account_id, region_name=target_region)
        )
    mi.remove_module_info(deployment, group, module, session=session)
