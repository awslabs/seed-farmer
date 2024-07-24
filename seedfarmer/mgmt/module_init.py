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

from cookiecutter.main import cookiecutter

import seedfarmer.errors
from seedfarmer import config

_logger: logging.Logger = logging.getLogger(__name__)


def create_module_dir(
    module_name: str,
    group_name: Optional[str],
    module_type: Optional[str],
    template_url: Optional[str],
    template_branch: Optional[str] = "main",
) -> None:
    """Initializes a directory for a new module.

    Creates a new directory that contains files that will aid in setting up a development environment

    Parameters
    ----------
    group_name : Optional[str],
        Name of the group where the module will reside. If group is a nested dir, use `/` as a delimiter
    module_name : str
        Name of the module. The initialization will include project files pulled from the template_url
    module_type: Optional[str]
        They type of code the module deploys with, adding more boilerplate code
        -- only cdkv2 is supported here
    template_url : Optional[List[str]]
        A URL, for example a Github repo, that is or contains the template for the for the initialization
    template_branch : Optional[str]
        The Branch on the template repository. If not specified, the default template branch is `main`
    """
    module_root = os.path.join(config.OPS_ROOT, "modules")
    module_path = os.path.join(module_root, module_name)
    output_dir = module_root
    checkout_branch = template_branch

    if group_name:
        module_path = os.path.join(module_root, group_name, module_name)
        output_dir = os.path.join(module_root, group_name)

        if not os.path.exists(output_dir):
            _logger.info("Creating group dir: %s", output_dir)
            os.makedirs(output_dir)

    if os.path.exists(module_path):
        raise seedfarmer.errors.InvalidPathError(f"The module {module_name} already exists under {output_dir}.")

    if template_url == "https://github.com/awslabs/seed-farmer.git":
        checkout_branch = "init-module-cdkv2" if module_type == "cdkv2" else "init-module"

    _logger.info("New module will be created in the following dir: %s", output_dir)
    cookiecutter(
        template=template_url,
        checkout=checkout_branch,
        no_input=True,
        extra_context={"project_name": module_name, "module_name": module_name},
        output_dir=output_dir,
    )


def create_project(template_url: Optional[str], template_branch: Optional[str] = "main") -> None:
    """Initializes a new project directory.

    Creates a new directory that contains files that will aid in setting up a development environment

    Parameters
    ----------
    project_name : str
        Name of the project. The initialization will include project files pulled from the template_url
        using the template_branch as reference
    template_url : Optional[List[str]]
        A URL, for example a Github repo, that is or contains the template for the initialization
    template_branch : Optional[str]
        The Branch on the template repository. If not specified, the default template branch is `main`
    """

    checkout_branch = (
        "init-project" if template_url == "https://github.com/awslabs/seed-farmer.git" else template_branch
    )
    _logger.info(" New project will be created in the following dir: %s", os.path.join(config.OPS_ROOT, config.PROJECT))
    cookiecutter(
        template=template_url,
        checkout=checkout_branch,
        no_input=True,
        extra_context={"project_name": config.PROJECT},
        output_dir=config.OPS_ROOT,
    )
    os.replace(
        os.path.join(config.OPS_ROOT, config.CONFIG_FILE),
        os.path.join(config.OPS_ROOT, config.PROJECT, config.CONFIG_FILE),
    )
