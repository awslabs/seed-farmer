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

import seedfarmer
from seedfarmer import DEBUG_LOGGING_FORMAT, commands, enable_debug
from seedfarmer.cli_groups import init, list, remove, store
from seedfarmer.config import DESCRIPTION, PROJECT
from seedfarmer.output_utils import print_bolded

_logger: logging.Logger = logging.getLogger(__name__)


@click.group()
def cli() -> None:
    f"{DESCRIPTION}"
    pass


@click.command(help="Get the version of seedfarmer")
def version() -> None:
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
    f"Destroy an {PROJECT.upper()} deployment ."
    if debug:
        enable_debug(format=DEBUG_LOGGING_FORMAT)
    _logger.info("Destroy for %s", deployment)
    if dry_run:
        print_bolded(" ***   This is a dry-run...NO ACTIONS WILL BE TAKEN  *** ", "white")
    commands.destroy(deployment_name=deployment, dryrun=dry_run, show_manifest=show_manifest)


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
