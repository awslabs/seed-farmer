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
import sys
from typing import Optional

import click
from boto3 import Session

import seedfarmer.mgmt.deploy_utils as du
import seedfarmer.mgmt.module_info as mi
from seedfarmer import DEBUG_LOGGING_FORMAT, commands, config, enable_debug
from seedfarmer.output_utils import print_bolded, print_deployment_inventory, print_json, print_manifest_inventory
from seedfarmer.services.session_manager import SessionManager

_logger: logging.Logger = logging.getLogger(__name__)


def _load_project() -> str:
    try:
        print_bolded("No --project provided, attempting load from seedfarmer.yaml", "white")
        return config.PROJECT
    except FileNotFoundError:
        print_bolded("Unable to determine project to bootstrap, one of --project or a seedfarmer.yaml is required")
        raise click.ClickException("Failed to determine project identifier")


@click.group(name="list", help="List the relative data (module or deployment)")
def list() -> None:
    """List module data"""
    pass


@list.command(name="deployspec", help="List the stored deployspec of a module")
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
def list_deployspec(
    deployment: str,
    group: str,
    module: str,
    project: Optional[str],
    target_account_id: Optional[str],
    target_region: Optional[str],
    debug: bool,
) -> None:
    if debug:
        enable_debug(format=DEBUG_LOGGING_FORMAT)
    _logger.debug("We are getting deployspec for  %s in %s of deployment %s", module, group, deployment)

    if project is None:
        project = _load_project()

    session: Optional[Session] = None
    if (target_account_id is not None) != (target_region is not None):
        raise ValueError("Must either specify both --target-account-id and --target-region, or neither")
    elif target_account_id is not None and target_region is not None:
        session = (
            SessionManager()
            .get_or_create(project_name=project)
            .get_deployment_session(account_id=target_account_id, region_name=target_region)
        )

    val = mi.get_deployspec(deployment=deployment, group=group, module=module, session=session)
    print_json(val)


@list.command(name="moduledata", help="Fetch the module metadata")
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
    "--export-local-env/--no-export-local-env",
    default=False,
    help="Print the moduledata as env parameters for local development support INSTEAD of json (default is FALSE)",
    show_default=True,
)
@click.option(
    "--debug/--no-debug",
    default=False,
    help="Enable detailed logging.",
    show_default=True,
)
def list_module_metadata(
    deployment: str,
    group: str,
    module: str,
    project: Optional[str],
    target_account_id: Optional[str],
    target_region: Optional[str],
    export_local_env: str,
    debug: bool,
) -> None:
    if debug:
        enable_debug(format=DEBUG_LOGGING_FORMAT)
    _logger.debug("We are getting module data for  %s in %s of %s", module, group, deployment)

    if project is None:
        project = _load_project()

    session: Optional[Session] = None
    if (target_account_id is not None) != (target_region is not None):
        raise ValueError("Must either specify both --target-account-id and --target-region, or neither")
    elif target_account_id is not None and target_region is not None:
        session = (
            SessionManager()
            .get_or_create(project_name=project)
            .get_deployment_session(account_id=target_account_id, region_name=target_region)
        )

    metadata_json = mi.get_module_metadata(deployment, group, module, session=session)
    if not export_local_env:
        sys.stdout.write(json.dumps(metadata_json))
    else:
        envs = commands.generate_export_env_params(metadata_json)
        if envs:
            for exp in envs:
                sys.stdout.write(exp)
                sys.stdout.write("\n")
        else:
            print(f"No module data found for {deployment}-{group}-{module}")
            print_bolded("To see all deployments, run seedfarmer list deployments")
            print_bolded(f"To see all deployed modules in {deployment}, run seedfarmer list modules -d {deployment}")


@list.command(name="modules", help="List the modules in a deployment")
@click.option(
    "--deployment",
    "-d",
    type=str,
    help="The Deployment Name",
    required=True,
)
@click.option(
    "--debug/--no-debug",
    default=False,
    help="Enable detailed logging.",
    show_default=True,
)
def list_modules(
    deployment: str,
    debug: bool,
) -> None:
    if debug:
        enable_debug(format=DEBUG_LOGGING_FORMAT)
    _logger.debug("We are getting modules for %s", deployment)

    project = _load_project()
    SessionManager().get_or_create(project_name=project)

    dep_manifest = du.generate_deployed_manifest(deployment_name=deployment, skip_deploy_spec=True)
    if dep_manifest:
        print_manifest_inventory("Deployed Modules", dep_manifest, False, "green")


@list.command(name="deployments", help="List the deployments in this account")
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
    help="The AWS profile to use for boto3.Sessions",
    required=False,
)
@click.option(
    "--region",
    default=None,
    help="The AWS region to use for boto3.Sessions",
    required=False,
)
@click.option(
    "--debug/--no-debug",
    default=False,
    help="Enable detailed logging.",
    show_default=True,
)
def list_deployments(
    project: Optional[str],
    profile: Optional[str],
    region: Optional[str],
    debug: bool,
) -> None:
    if debug:
        enable_debug(format=DEBUG_LOGGING_FORMAT)
    if project is None:
        project = _load_project()
    _logger.debug("Listing all deployments for Project %s", project)

    deps = mi.get_all_deployments(
        session=SessionManager()
        .get_or_create(project_name=project, profile=profile, region_name=region)
        .toolchain_session
    )
    print_deployment_inventory(description="Deployment Names", dep=deps)
