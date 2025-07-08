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
from pathlib import Path
from typing import Optional

import yaml
from cookiecutter.main import cookiecutter

from seedfarmer import config

_logger: logging.Logger = logging.getLogger(__name__)


def remove_leading_path_sep(path: str) -> str:
    if path.startswith(os.sep):
        return str(path[len(os.sep) :])
    # On Windows, also check for altsep ('/')
    if os.altsep and path.startswith(os.altsep):
        return str(path[len(os.altsep) :])
    return path


def add_module_manifest(module_name: str, module_path: str) -> None:
    """Add the module manifest to the project.

    Creates the module manifest and adds the path to the groups in deployment.yaml

    Parameters
    ----------
    module_name : str
        Name of the module
    module_path: str
        The absolute path of the module location...assumed that seedfarmer.yaml
        has determined this pat
    """

    module_path = remove_leading_path_sep(module_path.replace(config.OPS_ROOT, ""))
    _logger.debug("module_path=%s", module_path)
    _logger.debug("module_name=%s", module_name)

    module_manifest = {
        "name": module_name,
        "path": module_path,
    }
    manifest_name = f"{module_name}-group.yml"
    manifest_path = os.path.join(config.OPS_ROOT, manifest_name)
    with open(manifest_path, "w") as f:
        yaml.dump(module_manifest, f)

    group_definition = {"name": f"{module_name}-group", "path": manifest_name}
    deployment_yaml = os.path.join(config.OPS_ROOT, "deployment.yaml")
    # Check if the file exists
    if os.path.exists(deployment_yaml):
        with open(deployment_yaml, "r") as file:
            data = yaml.safe_load(file) or {}
        if "groups" in data:
            if isinstance(data["groups"], list):
                data["groups"].append(group_definition)
            else:
                data["groups"] = [data["groups"], group_definition]
        else:
            data["groups"] = [group_definition]

        with open(deployment_yaml, "w") as file:
            yaml.safe_dump(data, file)
    else:
        _logger.info(f"YAML file does not exist at path: {deployment_yaml}, skipping append")


def create_module_dir(
    module_name: str,
    module_type: Optional[str],
    template_url: Optional[str],
    group_name: Optional[str] = None,
    template_branch: Optional[str] = "init-module",
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
    module_name = module_name.replace("_", "-")
    module_root = os.path.join(config.OPS_ROOT, "modules")
    module_path = os.path.join(module_root, module_name)
    output_dir = module_root
    checkout_branch = template_branch

    module_path = (
        os.path.join(module_root, group_name, module_name) if group_name else os.path.join(module_root, module_name)
    )
    output_dir = os.path.join(module_root, group_name) if group_name else os.path.join(module_root)

    if not os.path.exists(output_dir):
        _logger.info("Creating group dir: %s", output_dir)
        os.makedirs(output_dir)

    if not os.path.exists(module_path):
        if template_url == "https://github.com/awslabs/seed-farmer.git":
            checkout_branch = "init-module-cdkv2" if module_type == "cdkv2" else "init-module"
        if template_branch is not None:
            checkout_branch = template_branch

        _logger.info("New module will be created in the following dir: %s", output_dir)
        cookiecutter(
            template=template_url,
            checkout=checkout_branch,
            no_input=True,
            extra_context={"project_name": module_name, "module_name": module_name},
            output_dir=output_dir,
        )

        add_module_manifest(module_name, module_path)


def create_project(
    template_url: str = "https://github.com/awslabs/seed-farmer.git",
    template_branch: Optional[str] = "init-project",
    project_name: Optional[str] = None,
    project_dir: Optional[str] = None,
) -> None:
    """Initializes a new project directory.

    Creates a new directory that contains files that will aid in setting up a development environment

    Parameters
    ----------
    template_url : str
        A URL, for example a Github repo, that is or contains the template for the initialization
    template_branch : Optional[str]
        The Branch on the template repository. If not specified, the default template branch is `main`
    project_name : Optional[str]
        Name of the project. The initialization will include project files pulled from the template_url
        using the template_branch as reference
    project_root_name: Optional[str]
        If the name of the directory is not to be ths same name of the project, override it here
    """
    # Create minimal seedfarmer.yaml first if project_name is provided
    if project_name is not None:
        with open(os.path.join(os.getcwd(), "seedfarmer.yaml"), "w") as f:
            yaml.dump({"project": project_name}, f, default_flow_style=False)

    project_name = project_name if project_name else config.PROJECT
    project_dir = project_dir if project_dir else project_name

    proposed_project_path = Path(project_dir)

    if proposed_project_path.is_dir():
        print("The targeted project / capability directory already exists. Exiting.")
        exit(0)

    cookiecutter(
        template=template_url,
        checkout=template_branch,
        no_input=True,
        extra_context={"project_name": project_name, "project_slug": project_dir},
        output_dir=config.OPS_ROOT,
    )

    if project_name is not None:
        # Move the seedfarmer.yaml to the project directory
        os.replace(
            os.path.join(os.getcwd(), "seedfarmer.yaml"), os.path.join(config.OPS_ROOT, project_dir, "seedfarmer.yaml")
        )
    else:
        os.replace(
            os.path.join(config.OPS_ROOT, config.CONFIG_FILE),
            os.path.join(config.OPS_ROOT, config.PROJECT, config.CONFIG_FILE),
        )
