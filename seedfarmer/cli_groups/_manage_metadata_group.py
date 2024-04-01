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

import seedfarmer.errors
from seedfarmer import config
from seedfarmer.mgmt import metadata_support
from seedfarmer.output_utils import print_bolded

_logger: logging.Logger = logging.getLogger(__name__)


def _load_project() -> str:
    try:
        return config.PROJECT
    except FileNotFoundError:
        print_bolded("Unable to determine project to bootstrap, seedfarmer.yaml is required")
        raise click.ClickException("Failed to determine project identifier")


@click.group(name="metadata", help="Manage the metadata in a module deployment execution")
def metadata() -> None:
    """Metadata Management group"""
    pass


@metadata.command(
    name="convert",
    help="""Convert the CDK Output of the module to SeedFarmer Metadata.
     This command is meant to be run in the deployspec only!!!
    """,
)
@click.option(
    "--jq-path",
    "-jq",
    type=str,
    help="A jq-compliant path to apply to a cdk-output (json) file",
    required=False,
)
@click.option(
    "--json-file",
    "-f",
    type=str,
    help="Relative path to a cdk-output file (defautls to cdk-exports.json)",
    required=False,
    default="cdk-exports.json",
)
def convert_cdkexports(
    json_file: str,
    jq_path: Optional[str] = None,
) -> None:
    _load_project()
    metadata_support.convert_cdkexports(jq_path=jq_path, json_file=json_file)


@metadata.command(
    name="add",
    help="""Add Output K,V to the Metadata.
     This command is meant to be run in the deployspec only!!!
    """,
)
@click.option(
    "--key",
    "-k",
    type=str,
    help="The key of a key-value pair",
    required=False,
)
@click.option(
    "--value",
    "-v",
    type=str,
    help="The value of a key-value pair",
    required=False,
)
@click.option(
    "--jsonstring",
    "-j",
    type=str,
    help="JSON-compliant string to add in a stringified format",
    required=False,
)
def add(key: str, value: str, jsonstring: str) -> None:
    _load_project()
    if jsonstring and key and value:
        raise seedfarmer.errors.InvalidConfigurationError(
            "Must either specify EITHER a json string OR a key with a value..."
        )
    if jsonstring:
        metadata_support.add_json_output(json_string=jsonstring)
    else:
        if key:
            if not value:
                raise seedfarmer.errors.InvalidConfigurationError("Must specify a key and value together")
            else:
                metadata_support.add_kv_output(key=key, value=value)
        if value and not key:
            raise seedfarmer.errors.InvalidConfigurationError("Must specify a key and value together")


@metadata.command(
    name="depmod",
    help="""Get the Full Name of the Module.
     This command is meant to be run in the deployspec only!!!
    """,
)
def depmod() -> None:
    sys.stdout.write(metadata_support.get_dep_mod_name())


@metadata.command(
    name="paramvalue",
    help="""Get the parameter value based on the suffix.
     This command is meant to be run in the deployspec only!!!
    """,
)
@click.option(
    "--suffix",
    "-s",
    type=str,
    help="A jq-compliant path to apply to a cdk-output (json) file",
    required=True,
)
def param_value(
    suffix: str,
) -> None:
    p = metadata_support.get_parameter_value(parameter_suffix=suffix)
    sys.stdout.write(p) if p else None
