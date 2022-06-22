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

from typing import Any, Dict, List, Optional

from rich.console import Console
from rich.table import Table

from seedfarmer.models.manifests import DeploymentManifest

console = Console(record=True)


def print_deployment_inventory(description: str, dep: List[str], color: str = "yellow") -> None:
    """
    A helper method to print the list of deployments in a table to console

    Parameters
    ----------
    description : str
        Give the table a title
    dep : List[str]
        A list of strings of the deployment names
    color : str, optional
        The color of the Title , by default "yellow"
    """ """"""
    table = Table(title=f"[bold {color}]{description}", title_justify="left")

    table.add_column("Deployemnt", justify="left", style="cyan", no_wrap=True)
    for deployment in dep:
        table.add_row(deployment)

    console.print(table)


def print_manifest_inventory(
    description: str, dep: DeploymentManifest, show_path: bool = False, color: str = "yellow"
) -> None:
    """
    A helper method to print the content of a DeploymentManifest object in a table to console

    Parameters
    ----------
    description : str
        Give the table a title
    dep : DeploymentManifest
        A poluated Deplopyment Manifest object
    show_path : bool, optional
       Show the relative path of the module code, by default False
    color : str, optional
       The color of the Title, by default "yellow"
    """ """"""
    table = Table(title=f"[bold {color}]{description}", title_justify="left")

    table.add_column("Deployemnt", justify="left", style="cyan", no_wrap=True)
    table.add_column("Group", justify="left", style="magenta")
    table.add_column("Module", justify="left", style="green")
    table.add_column("Path", justify="left") if show_path else None
    d_name = dep.name
    for group in dep.groups:
        g_name = group.name
        for module in group.modules:
            m_name = module.name
            m_path = module.path
            if show_path:
                table.add_row(d_name, g_name, m_name, m_path)
            else:
                table.add_row(d_name, g_name, m_name)

    console.print(table)


def _print_modules(description: str, modules_list: List[Any]) -> None:
    table = Table(title=f"[bold yellow]{description}", title_justify="left")

    table.add_column("Deployemnt", style="cyan", no_wrap=True)
    table.add_column("Group", justify="left", style="magenta")
    table.add_column("Module", justify="left", style="green")
    for lst in modules_list:
        table.add_row(lst[0], lst[1], lst[2])

    console.print(table)


def print_manifest_json(dep: DeploymentManifest) -> None:
    """
    Pretty-print to console a json representation of the DeploymentManifest

    Parameters
    ----------
    dep : DeploymentManifest
        The DeploymentManifest to be printed as json
    """ """"""
    console.print(dep.dict(), overflow="ignore", crop=False)


def print_json(payload: Optional[Dict]) -> None:
    """
    Pretty-print to console a json representation of the DeploymentManifest

    Parameters
    ----------
    dep : DeploymentManifest
        The DeploymentManifest to be printed as json
    """ """"""
    console.print(payload, overflow="ignore", crop=False)


def print_bolded(message: str, color: str = "yellow") -> None:
    """
    Print a string message to console in a requested color and bolded

    Parameters
    ----------
    message : str
        The String
    color : str, optional
       The color you want the message printed in.... default is "yellow"
    """ """"""
    console.print(f"[bold {color}]{message}")