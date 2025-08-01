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

import click

import seedfarmer.mgmt.module_init as minit


@click.group(name="init", help="Initialize a project or module")
def init() -> None:
    """Initialize a project or module"""
    pass


@init.command(name="project", help="Initialize a project.")
@click.option(
    "--project-name",
    "-p",
    default=None,
    help="The name of the project. If None, seedfarmer.yaml must be at the dir where cli invoked.",
    required=False,
)
@click.option(
    "--project_dir",
    "-pd",
    default=None,
    help="The name of the directory that houses the project if not to be the same as the project name",
    required=False,
)
@click.option(
    "--template-url",
    "-t",
    default="https://github.com/awslabs/seed-farmer.git",
    help="The template URL. If not specified, the default template repo is `https://github.com/awslabs/seed-farmer`",
    required=False,
)
@click.option(
    "--template-branch",
    "-b",
    default="init-project",
    help="The Branch on the template repository. If not specified, the default template branch is `init-project`",
    required=False,
)
def init_project(template_url: str, template_branch: str, project_name: str, project_dir: str) -> None:
    minit.create_project(
        template_url=template_url, template_branch=template_branch, project_name=project_name, project_dir=project_dir
    )


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
    "--module-type",
    "-mt",
    type=str,
    help="The type of module code deployed...only 'cdkv2' is accepted if used here",
    required=False,
    default=None,
)
@click.option(
    "--template-url",
    "-t",
    default="https://github.com/awslabs/seed-farmer.git",
    help=("The template URL. If not specified, the default template repo is `https://github.com/awslabs/seed-farmer`"),
    required=False,
)
@click.option(
    "--template-branch",
    "-b",
    default="init-module",
    help="The Branch on the template repository. If not specified, the default template branch is `main`",
    required=False,
)
@click.option("--debug/--no-debug", default=False, help="Enable detail logging", show_default=True)
def init_module(
    group_name: str, module_name: str, module_type: str, template_url: str, template_branch: str, debug: bool
) -> None:
    minit.create_module_dir(
        group_name=group_name,
        module_name=module_name,
        module_type=module_type,
        template_url=template_url,
        template_branch=template_branch,
    )
