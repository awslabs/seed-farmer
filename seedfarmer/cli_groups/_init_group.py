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

import seedfarmer.mgmt.module_init as minit
from seedfarmer import DEBUG_LOGGING_FORMAT, enable_debug

_logger: logging.Logger = logging.getLogger(__name__)


@click.group(name="init", help="Initiaize a project or module")
def init() -> None:
    """Initialize a project or module"""
    pass


@init.command(
    name="project",
    help="Initialize a project. Make sure seedfarmer.yaml is present in the same location you execute this command!!",
)
@click.option(
    "--template-url",
    "-t",
    default="https://github.com/awslabs/seed-farmer.git",
    help="The template URL. If not specified, the default template repo is `https://github.com/awslabs/seed-farmer`",
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
