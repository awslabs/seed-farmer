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

import seedfarmer
from seedfarmer import DEBUG_LOGGING_FORMAT, commands, config, enable_debug
from seedfarmer.cli_groups import bootstrap, init, list, remove, store
from seedfarmer.output_utils import print_bolded
from seedfarmer.services.session_manager import SessionManager

_logger: logging.Logger = logging.getLogger(__name__)


def _load_project() -> str:
    try:
        print_bolded("No --project provided, attempting load from seedfarmer.yaml", "white")
        return config.PROJECT
    except FileNotFoundError:
        print_bolded("Unable to determine project to bootstrap, one of --project or a seedfarmer.yaml is required")
        raise click.ClickException("Failed to determine project identifier")


@click.group()
def cli() -> None:
    """SeedFarmer CLI interface"""
    pass


@click.command(help="Get the version SeedFarmer")
def version() -> None:
    print(f"seed-farmer-{seedfarmer.__version__}")


@click.command(help="Apply manifests to a SeedFarmer managed deployment")
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
    """Apply manifests to a SeedFarmer managed deployment"""
    if debug:
        enable_debug(format=DEBUG_LOGGING_FORMAT)
    _logger.info("Apply request with manifest %s", spec)
    if dry_run:
        print_bolded(" ***   This is a dry-run...NO ACTIONS WILL BE TAKEN  *** ", "white")

    commands.apply(spec, dry_run, show_manifest)


@click.command(help="Destroy a SeedFarmer managed deployment")
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
def destroy(
    deployment: str,
    dry_run: bool,
    show_manifest: bool,
    project: Optional[str],
    profile: Optional[str],
    region: Optional[str],
    debug: bool,
) -> None:
    """Destroy a SeedFarmer managed deployment"""
    if debug:
        enable_debug(format=DEBUG_LOGGING_FORMAT)
    if project is None:
        project = _load_project()
    _logger.debug("Listing all deployments for Project %s", project)

    _logger.info("Destroy for Project %s, Deployment %s", project, deployment)
    if dry_run:
        print_bolded(" ***   This is a dry-run...NO ACTIONS WILL BE TAKEN  *** ", "white")

    (SessionManager().get_or_create(project_name=project, profile=profile, region_name=region).toolchain_session)
    commands.destroy(deployment_name=deployment, dryrun=dry_run, show_manifest=show_manifest)


def main() -> int:
    cli.add_command(apply)
    cli.add_command(destroy)
    cli.add_command(store)
    cli.add_command(remove)
    cli.add_command(list)
    cli.add_command(init)
    cli.add_command(version)
    cli.add_command(bootstrap)
    cli()
    return 0
