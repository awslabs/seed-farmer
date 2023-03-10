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
import os
from typing import Optional

import click
from dotenv import load_dotenv

import seedfarmer
from seedfarmer import DEBUG_LOGGING_FORMAT, commands, config, enable_debug
from seedfarmer.cli_groups import bootstrap, init, list, projectpolicy, remove, store
from seedfarmer.output_utils import print_bolded

_logger: logging.Logger = logging.getLogger(__name__)


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
    "--env-file",
    default=".env",
    help="A relative path to the .env file to load environment variables from",
    required=False,
)
@click.option(
    "--debug/--no-debug",
    default=False,
    help="Enable detailed logging.",
    show_default=True,
    type=bool,
)
@click.option(
    "--dry-run/--no-dry-run",
    default=False,
    help="Apply but do not execute....",
    show_default=True,
    type=bool,
)
@click.option(
    "--show-manifest/--no-show-manifest",
    default=False,
    help="Write out the generated deployment manifest",
    show_default=True,
    type=bool,
)
@click.option(
    "--enable-session-timeout/--disable-session-timeout",
    default=False,
    help="Enable boto3 Session timeouts. If enabled, boto3 Sessions will be reset on the timeout interval",
    show_default=True,
    type=bool,
)
@click.option(
    "--session-timeout-interval",
    default=900,
    help="If --enable-session-timeout, the interval, in seconds, to reset boto3 Sessions",
    show_default=True,
    type=int,
)
def apply(
    spec: str,
    profile: Optional[str],
    region: Optional[str],
    env_file: str,
    debug: bool,
    dry_run: bool,
    show_manifest: bool,
    enable_session_timeout: bool,
    session_timeout_interval: int,
) -> None:
    """Apply manifests to a SeedFarmer managed deployment"""
    if debug:
        enable_debug(format=DEBUG_LOGGING_FORMAT)

    # Load environment variables from .env file if it exists
    load_dotenv(dotenv_path=os.path.join(config.OPS_ROOT, env_file), verbose=True, override=True)

    _logger.info("Apply request with manifest %s", spec)
    if dry_run:
        print_bolded(" ***   This is a dry-run...NO ACTIONS WILL BE TAKEN  *** ", "white")

    commands.apply(
        deployment_manifest_path=spec,
        profile=profile,
        region_name=region,
        dryrun=dry_run,
        show_manifest=show_manifest,
        enable_session_timeout=enable_session_timeout,
        session_timeout_interval=session_timeout_interval,
    )


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
    "--profile",
    default=None,
    help="The AWS profile to use for boto3.Sessions",
    required=False,
)
@click.option(
    "--region",
    default=None,
    help="The AWS region to use for toolchain",
    required=False,
)
@click.option(
    "--env-file",
    default=".env",
    help="A relative path to the .env file to load environment variables from",
    required=False,
)
@click.option(
    "--debug/--no-debug",
    default=False,
    help="Enable detailed logging.",
    show_default=True,
)
@click.option(
    "--enable-session-timeout/--disable-session-timeout",
    default=False,
    help="Enable boto3 Session timeouts. If enabled, boto3 Sessions will be reset on the timeout interval",
    show_default=True,
    type=bool,
)
@click.option(
    "--session-timeout-interval",
    default=900,
    help="If --enable-session-timeout, the interval, in seconds, to reset boto3 Sessions",
    show_default=True,
    type=int,
)
def destroy(
    deployment: str,
    dry_run: bool,
    show_manifest: bool,
    profile: Optional[str],
    region: Optional[str],
    env_file: str,
    debug: bool,
    enable_session_timeout: bool,
    session_timeout_interval: int,
) -> None:
    """Destroy a SeedFarmer managed deployment"""
    if debug:
        enable_debug(format=DEBUG_LOGGING_FORMAT)

    # Load environment variables from .env file if it exists
    load_dotenv(dotenv_path=os.path.join(config.OPS_ROOT, env_file), verbose=True, override=True)

    # MUST use seedfarmer.yaml so we can initialize codeseeder configs
    project = config.PROJECT
    _logger.debug("Listing all deployments for Project %s", project)

    _logger.info("Destroy for Project %s, Deployment %s", project, deployment)
    if dry_run:
        print_bolded(" ***   This is a dry-run...NO ACTIONS WILL BE TAKEN  *** ", "white")

    commands.destroy(
        deployment_name=deployment,
        profile=profile,
        region_name=region,
        dryrun=dry_run,
        show_manifest=show_manifest,
        enable_session_timeout=enable_session_timeout,
        session_timeout_interval=session_timeout_interval,
    )


def main() -> int:
    cli.add_command(apply)
    cli.add_command(destroy)
    cli.add_command(store)
    cli.add_command(remove)
    cli.add_command(list)
    cli.add_command(init)
    cli.add_command(version)
    cli.add_command(bootstrap)
    cli.add_command(projectpolicy)
    cli()
    return 0
