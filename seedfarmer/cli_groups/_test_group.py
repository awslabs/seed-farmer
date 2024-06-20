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

from seedfarmer import DEBUG_LOGGING_FORMAT, config, enable_debug
from seedfarmer.commands import single_module_deploy
from seedfarmer.utils import load_dotenv_files

_logger: logging.Logger = logging.getLogger(__name__)


@click.group(
    name="test",
    help="Commands for testing individual module deployments",
)
def test() -> None:
    """Commands for testing individual module deployments"""
    pass


@test.command(
    name="module-deploy",
    help="Test single deployment of a module.",
)
@click.option("--debug/--no-debug", default=False, help="Enable detail logging", show_default=True)
@click.option(
    "--manifest-path",
    "-p",
    type=str,
    help="Path to manifest",
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
    "--deployment-name-prefix",
    "-d",
    default="test",
    help="Prefix to prepend to test deployment name. Defaults to 'test'",
    required=False,
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
    "--env-file",
    "env_files",
    default=[".env"],
    help="""A relative path to the .env file to load environment variables from.
    Multiple files can be passed in by repeating this flag, and the order will be
    preserved when overriding duplicate values.
    """,
    multiple=True,
    required=False,
)
def module_deploy(
    manifest_path: str,
    group: str,
    module: str,
    env_files: List[str],
    debug: bool,
    deployment_name_prefix: Optional[str],
    profile: Optional[str],
    region: Optional[str],
) -> None:
    if debug:
        enable_debug(format=DEBUG_LOGGING_FORMAT)

    load_dotenv_files(config.OPS_ROOT, env_files)
    single_module_deploy(
        manifest_path=manifest_path,
        group_name=group,
        module_name=module,
        test_deployment_name_prefix=deployment_name_prefix,
        profile=profile,
        region_name=region,
    )


@test.command(
    name="module-destroy",
    help="Test single destroy of a module.",
)
@click.option("--debug/--no-debug", default=False, help="Enable detail logging", show_default=True)
@click.option(
    "--manifest-path",
    "-p",
    type=str,
    help="Path to manifest",
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
    "--deployment-name-prefix",
    default="test",
    help="Prefix to prepend to test deployment name. Defaults to 'test'",
    required=False,
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
    "--env-file",
    "env_files",
    default=[".env"],
    help="""A relative path to the .env file to load environment variables from.
    Multiple files can be passed in by repeating this flag, and the order will be
    preserved when overriding duplicate values.
    """,
    multiple=True,
    required=False,
)
def module_destroy(
    manifest_path: str,
    group: str,
    module: str,
    env_files: List[str],
    debug: bool,
    deployment_name_prefix: Optional[str],
    profile: Optional[str],
    region: Optional[str],
) -> None:
    if debug:
        enable_debug(format=DEBUG_LOGGING_FORMAT)

    load_dotenv_files(config.OPS_ROOT, env_files)
    single_module_deploy(
        manifest_path=manifest_path,
        group_name=group,
        module_name=module,
        test_deployment_name_prefix=deployment_name_prefix,
        destroy=True,
        profile=profile,
        region_name=region,
    )
