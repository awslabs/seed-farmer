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
import sys
from typing import Optional

import click

from seedfarmer import config
from seedfarmer.mgmt import bundle_support
from seedfarmer.output_utils import print_bolded
from seedfarmer.services.session_manager import SessionManager, SessionManagerLocalImpl

_logger: logging.Logger = logging.getLogger(__name__)


def _load_project() -> str:
    try:
        return config.PROJECT
    except FileNotFoundError:
        print_bolded("Unable to determine project to bootstrap, seedfarmer.yaml is required")
        raise click.ClickException("Failed to determine project identifier")


@click.group(name="bundle", help="Manage the bundle in a module deployment execution")
def bundle() -> None:
    """Bundle Management group"""
    pass


@bundle.command(
    name="store",
    help="""Store the bundle used to deploy a module.
     This command is meant to be run by SeedFarmer ONLY!!!
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
    "--bucket",
    "-b",
    help="The name of the SeedFarmer bucket the bundle to be stored in",
    required=True,
)
@click.option(
    "--origin",
    "-o",
    help="Full path of the bundle object in SeedKit bucket",
    required=True,
)
@click.option(
    "--region",
    default=None,
    help="The AWS region used to create a session",
    required=False,
)
def store_bundle(
    deployment: str, group: str, module: str, bucket: str, origin: str, region: Optional[str] = None
) -> None:
    _load_project()
    print(f"{deployment} - {group} - {module} -{bucket} - {origin}")
    SessionManager.bind(SessionManagerLocalImpl())
    session = (
        SessionManager()
        .get_or_create(region_name=region)
        .get_deployment_session(account_id="000000000000", region_name=str(region))
    )

    bundle_support.copy_bundle_to_sf(
        deployment=deployment, group=group, module=module, bucket=bucket, bundle_src_path=origin, session=session
    )


@bundle.command(
    name="fetch",
    help="""Fetch the full path where the bundle is stored in SF.
     This command is meant to be run by SeedFarmer ONLY!!!
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
    "--bucket",
    "-b",
    type=str,
    help="The Name of the bucket where the bundle is stored in SeedFarmer",
    required=True,
)
def fetch_bundle(deployment: str, group: str, module: str, bucket: str, region: Optional[str] = None) -> None:
    _load_project()
    p = bundle_support.get_bundle_sf_path(deployment=deployment, group=group, module=module, bucket=bucket)
    sys.stdout.write(p) if p else None


@bundle.command(
    name="delete",
    help="""Delete the bundle stored in SF.
     This command is meant to be run by SeedFarmer ONLY!!!
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
    "--bucket",
    "-b",
    type=str,
    help="The Name of the bucket where the bundle is stored in SeedFarmer",
    required=True,
)
@click.option(
    "--region",
    default=None,
    help="The AWS region used to create a session",
    required=False,
)
def delete_bundle(deployment: str, group: str, module: str, bucket: str, region: Optional[str] = None) -> None:
    _load_project()
    SessionManager.bind(SessionManagerLocalImpl())
    session = (
        SessionManager().get_or_create().get_deployment_session(account_id="000000000000", region_name=str(region))
    )

    bundle_support.delete_bundle_from_sf(
        deployment=deployment, group=group, module=module, bucket=bucket, session=session
    )
