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

import click

import seedfarmer.mgmt.deploy_utils as du
import seedfarmer.mgmt.module_info as mi
from seedfarmer import DEBUG_LOGGING_FORMAT, commands, enable_debug
from seedfarmer.config import PROJECT
from seedfarmer.output_utils import print_bolded, print_deployment_inventory, print_json, print_manifest_inventory

_logger: logging.Logger = logging.getLogger(__name__)


@click.group(name="list", help="List the relative data (module or deployment)")
def list() -> None:
    f"""List module data for {PROJECT.upper()}"""
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
    "--debug/--no-debug",
    default=False,
    help="Enable detailed logging.",
    show_default=True,
)
def list_deployspec(
    deployment: str,
    group: str,
    module: str,
    debug: bool,
) -> None:
    if debug:
        enable_debug(format=DEBUG_LOGGING_FORMAT)
    _logger.debug("We are getting deployspec for  %s in %s of deployment %s", module, group, deployment)

    val = mi.get_deployspec(deployment=deployment, group=group, module=module)
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
    export_local_env: str,
    debug: bool,
) -> None:
    if debug:
        enable_debug(format=DEBUG_LOGGING_FORMAT)
    _logger.debug("We are getting module data for  %s in %s of %s", module, group, deployment)
    metadata_json = mi.get_module_metadata(deployment, group, module)
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


@list.command(name="modules", help="List the modules in a group")
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

    cache = du.generate_deployment_cache(deployment_name=deployment)
    dep_manifest = du.generate_deployed_manifest(
        deployment_name=deployment, deployment_params_cache=cache, skip_deploy_spec=True
    )
    if dep_manifest:
        print_manifest_inventory("Deployed Modules", dep_manifest, False, "green")


@list.command(name="deployments", help="List the deployments in this account")
@click.option(
    "--debug/--no-debug",
    default=False,
    help="Enable detailed logging.",
    show_default=True,
)
def list_deployments(
    debug: bool,
) -> None:
    if debug:
        enable_debug(format=DEBUG_LOGGING_FORMAT)
    _logger.debug("We are getting all deployments")
    deps = mi.get_all_deployments()
    print_deployment_inventory(description="Deployment Names", dep=deps)
