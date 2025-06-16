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

import seedfarmer.mgmt.deploy_utils as du
import seedfarmer.mgmt.module_info as mi
from seedfarmer import DEBUG_LOGGING_FORMAT, config, enable_debug
from seedfarmer.output_utils import print_bolded
from seedfarmer.services.session_manager import (
    ISessionManager,
    SessionManager,
    bind_session_mgr,
)
from seedfarmer.utils import load_dotenv_files

_logger: logging.Logger = logging.getLogger(__name__)


def _load_project() -> str:
    try:
        _logger.info("No --project provided, attempting load from seedfarmer.yaml")
        return config.PROJECT
    except FileNotFoundError:
        print_bolded("Unable to determine project to bootstrap, one of --project or a seedfarmer.yaml is required")
        raise click.ClickException("Failed to determine project identifier")


def _error_messaging(deployment: str, group: Optional[str] = None, module: Optional[str] = None) -> None:
    if group and module:
        print(f"No module info found for {deployment}-{group}-{module}")
        print_bolded(f"To see all deployed modules in {deployment}, run seedfarmer list modules -d {deployment}")
    else:
        print(f"No module info found for {deployment}")
    print_bolded("To see all deployments, run seedfarmer list deployments")


@click.group(name="taint", help="Top Level command to support adding a taint to a deployed module")
@bind_session_mgr
def taint() -> None:
    """Taint module"""
    pass


@taint.command(
    name="module",
    help="""This command will mark a module as needing
        redeploy of a module on the next deployment.
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
    help="The AWS profile used to create a session to assume the toolchain role",
    required=False,
)
@click.option(
    "--region",
    default=None,
    help="The AWS region used to create a session to assume the toolchain role",
    required=False,
)
@click.option(
    "--qualifier",
    default=None,
    help="""A qualifier to use with the seedfarmer roles.
    Use only if bootstrapped with this qualifier""",
    required=False,
)
@click.option(
    "--env-file",
    "env_files",
    default=[".env"],
    help="""A relative path to the .env file to load environment variables from.
    Multple files can be passed in by repeating this flag, and the order will be
    preserved when overriding duplicate values.
    """,
    multiple=True,
    required=False,
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
def taint_module(
    deployment: str,
    group: str,
    module: str,
    project: Optional[str],
    profile: Optional[str],
    region: Optional[str],
    qualifier: Optional[str],
    env_files: List[str],
    debug: bool,
    local: bool,
) -> None:
    if debug:
        enable_debug(format=DEBUG_LOGGING_FORMAT)
    _logger.debug("We are removing module data for %s of group %s in %s", module, group, deployment)

    if project is None:
        project = _load_project()

    load_dotenv_files(config.OPS_ROOT, env_files=env_files)

    session_manager: ISessionManager = SessionManager().get_or_create(
        project_name=project, profile=profile, region_name=region, qualifier=qualifier
    )

    try:
        dep_manifest = du.generate_deployed_manifest(deployment_name=deployment, skip_deploy_spec=True)
        dep_manifest.validate_and_set_module_defaults()  # type: ignore
        session = session_manager.get_deployment_session(
            account_id=dep_manifest.get_module(group=group, module=module).get_target_account_id(),  # type: ignore
            region_name=dep_manifest.get_module(group=group, module=module).target_region,  # type: ignore
        )
    except Exception:
        _error_messaging(deployment, group, module)
        return

    mi.remove_module_md5(
        deployment=deployment,
        group=group,
        module=module,
        type=mi.ModuleConst.BUNDLE,
        session=session,
    )
    _logger.debug("Module %s-%s-%s marked for redeploy", module, group, deployment)
