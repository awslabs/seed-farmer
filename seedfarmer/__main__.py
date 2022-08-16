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
import yaml

import seedfarmer
import seedfarmer.mgmt.deploy_utils as du
import seedfarmer.mgmt.module_info as mi
import seedfarmer.mgmt.module_init as minit
from seedfarmer import DEBUG_LOGGING_FORMAT, DESCRIPTION, PROJECT, commands, enable_debug, utils
from seedfarmer.output_utils import print_bolded, print_deployment_inventory, print_json, print_manifest_inventory

_logger: logging.Logger = logging.getLogger(__name__)


@click.group()
def cli() -> None:
    f"{DESCRIPTION}"
    pass


@click.command(help="Get the version of seedfarmer")
def version():
    print(f"seedfarmer {seedfarmer.__version__}")


@click.command(help=f"Apply a deployment manifest relative path for {PROJECT.upper()}")
@click.argument(
    "spec",
    type=str,
    required=True,
)
@click.option(
    "--debug/--no-debug",
    default=False,
    help="Enable detailed logging.",
    show_default=True,
)
@click.option(
    "--dry-run/--no-dry-run",
    default=False,
    help="Apply but do not execute....",
    show_default=True,
)
@click.option(
    "--show-manifest/--no-show-manifest",
    default=False,
    help="Write out the generated deployment manifest",
    show_default=True,
)
def apply(spec: str, debug: bool, dry_run: bool, show_manifest: bool) -> None:
    f"Deploy a(n) {PROJECT.upper()} environemnt based on a deployspec file (yaml)." ""
    if debug:
        enable_debug(format=DEBUG_LOGGING_FORMAT)
    _logger.info("Apply request with manifest %s", spec)
    if dry_run:
        print_bolded(" ***   This is a dry-run...NO ACTIONS WILL BE TAKEN  *** ", "white")

    commands.apply(spec, dry_run, show_manifest)


@click.command(help=f"Destroy {PROJECT.upper()} Deployment")
@click.argument(
    "deployment",
    type=str,
    required=True,
)
@click.option(
    "--dry-run/--no-dry-run",
    default=False,
    help="Apply but do not execute....",
    show_default=True,
)
@click.option(
    "--show-manifest/--no-show-manifest",
    default=False,
    help="Write out the generated deployment manifest",
    show_default=True,
)
@click.option(
    "--debug/--no-debug",
    default=False,
    help="Enable detailed logging.",
    show_default=True,
)
def destroy(
    deployment: str,
    dry_run: bool,
    show_manifest: bool,
    debug: bool,
) -> None:
    f"Destroy an {PROJECT.upper} deployment ."
    if debug:
        enable_debug(format=DEBUG_LOGGING_FORMAT)
    _logger.info("Destroy for %s", deployment)
    if dry_run:
        print_bolded(" ***   This is a dry-run...NO ACTIONS WILL BE TAKEN  *** ", "white")
    commands.destroy(deployment_name=deployment, dryrun=dry_run, show_manifest=show_manifest)


@click.group(name="store", help="Top Level command to support storing module metadata")
def store() -> None:
    f"Store module data for {PROJECT.upper()}"
    pass


@store.command(name="deployspec", help="Store/Update a deployspec of a currently deployed module")
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
    "--path",
    "-p",
    type=str,
    help="The relative module path (ex. modules/optionals/networking) -- *** DO NOT PASS IN filename `deployspec.yaml`",
    required=True,
)
@click.option(
    "--debug/--no-debug",
    default=False,
    help="Enable detailed logging.",
    show_default=True,
)
def store_deployspec(
    deployment: str,
    group: str,
    module: str,
    path: str,
    debug: bool,
) -> None:
    if debug:
        enable_debug(format=DEBUG_LOGGING_FORMAT)

    _logger.debug(
        f"""Storing deployspec for module {module} of group {group}
        in deployment {deployment} located at {path}/deployspec.yaml"""
    )
    du.update_deployspec(deployment, group, module, path)


@store.command(name="moduledata", help="CAT or pipe in a json or yaml object")
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
def store_module_metadata(
    deployment: str,
    group: str,
    module: str,
    debug: bool,
) -> None:
    if debug:
        enable_debug(format=DEBUG_LOGGING_FORMAT)
    _logger.debug("Writing metadata for module %s in deployment %s", module, deployment)
    d = yaml.load(sys.stdin.read(), Loader=utils.CfnSafeYamlLoader)
    if d:
        mi.write_metadata(deployment=deployment, group=group, module=module, data=d)
    else:
        _logger.info("No Data avaiable...skipping")


@store.command(name="md5", help="CAT or pipe in a string")
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
    "--type",
    "-t",
    type=str,
    help="The kind of MD5: bundle or spec",
    required=True,
)
@click.option(
    "--debug/--no-debug",
    default=False,
    help="Enable detailed logging.",
    show_default=True,
)
def store_module_md5(
    deployment: str,
    group: str,
    module: str,
    type: str,
    debug: bool,
) -> None:
    if debug:
        enable_debug(format=DEBUG_LOGGING_FORMAT)
    _logger.debug("Writing md5 of  %s for module %s in deployment %s", type, module, deployment)
    d = sys.stdin.readline().strip()
    if d:
        if type.casefold() == "bundle":
            _type = mi.ModuleConst.BUNDLE
        elif type.casefold() == "spec":
            _type = mi.ModuleConst.DEPLOYSPEC
        mi.write_module_md5(deployment=deployment, group=group, module=module, hash=d, type=_type)
    else:
        _logger.info("No Data avaiable...skipping")


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


@click.group(name="remove", help="Top Level command to support removing module metadata")
def remove() -> None:
    f"""Remove module data for {PROJECT.upper()}"""
    pass


@remove.command(name="moduledata", help="Remove all SSM parameters tied to the module")
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
def remove_module_data(
    deployment: str,
    group: str,
    module: str,
    debug: bool,
) -> None:
    if debug:
        enable_debug(format=DEBUG_LOGGING_FORMAT)
    _logger.debug(" We are removing module data for %s of group %s in %s", module, group, deployment)

    mi.remove_module_info(deployment, group, module)


@click.group(name="init", help="Initiaize a project or module")
def init() -> None:
    f"""Initialize a project or module for {PROJECT.upper()}"""
    pass


@init.command(
    name="project",
    help=(
        "Initialize a project. " "Make sure seedfarmer.yaml is present in the same location you execute this command!!"
    ),
)
@click.option(
    "--template-url",
    "-t",
    default="https://github.com/awslabs/seed-farmer.git",
    help=(
        "The template URL. If not specified, the default template repo is " "`https://github.com/awslabs/seed-farmer`"
    ),
    required=False,
)
def init_project(template_url: str) -> None:
    minit.create_project(template_url=template_url)


@init.command(name="module", help="Initialize a new module")
@click.option(
    "--group-name",
    "-g",
    type=str,
    help="The group the module belongs to. The `group` is created if it doesn't exist",
    required=False,
    default=None,
)
@click.option("--module-name", "-m", type=str, help="The module name", required=True)
@click.option(
    "--template-url",
    "-t",
    default="https://github.com/awslabs/seed-farmer.git",
    help=(
        "The template URL. If not specified, the default template repo is " "`https://github.com/awslabs/seed-farmer`"
    ),
    required=False,
)
@click.option("--debug/--no-debug", default=False, help="Enable detail logging", show_default=True)
def init_module(group_name: str, module_name: str, template_url: str, debug: bool) -> None:
    if debug:
        enable_debug(format=DEBUG_LOGGING_FORMAT)
    _logger.debug("Initializing module %s", module_name)

    minit.create_module_dir(
        group_name=group_name,
        module_name=module_name,
        template_url=template_url,
    )


def main() -> int:
    cli.add_command(apply)
    cli.add_command(destroy)
    cli.add_command(store)
    cli.add_command(remove)
    cli.add_command(list)
    cli.add_command(init)
    cli.add_command(version)
    cli()
    return 0
