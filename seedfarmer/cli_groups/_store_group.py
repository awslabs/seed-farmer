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
import yaml
from boto3 import Session

import seedfarmer.errors
import seedfarmer.mgmt.deploy_utils as du
import seedfarmer.mgmt.module_info as mi
from seedfarmer import DEBUG_LOGGING_FORMAT, config, enable_debug
from seedfarmer.output_utils import print_bolded
from seedfarmer.services.session_manager import SessionManager, bind_session_mgr

_logger: logging.Logger = logging.getLogger(__name__)


def _load_project() -> str:
    try:
        _logger.info("No --project provided, attempting load from seedfarmer.yaml")
        return config.PROJECT
    except FileNotFoundError:
        print_bolded("Unable to determine project to bootstrap, one of --project or a seedfarmer.yaml is required")
        raise click.ClickException("Failed to determine project identifier")


@click.group(name="store", help="Top Level command to support storing module information")
def store() -> None:
    "Store module information"
    pass


@store.command(
    name="deployspec",
    help="""Store/Update a deployspec of a currently deployed module.
             Use this if you cannot destroy a deployed module because of a defect
             in the the destroy portion of the deployspec.  USE WITH CAUTION as the
             existing deployspec gets overwritten and is NOT recoverable.
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
    "--path",
    type=str,
    help="""The relative module path (ex. modules/optionals/networking) -
     DO NOT PASS IN filename `deployspec.yaml`""",
    required=True,
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
    "--qualifier",
    default=None,
    help="""A qualifier to use with the seedfarmer roles.
     Use only if bootstrapped with this qualifier""",
    required=False,
)
@click.option(
    "--target-account-id",
    default=None,
    help="""Account Id of the target account to store deployspec, if specified --target-region is required
     You SHOULD NOT use this parameter as this command will leverage the SeedFarmer session manager!
     It is meant for development purposes.
    """,
    show_default=True,
)
@click.option(
    "--target-region",
    default=None,
    help="""Region of the target account to store deployspec, if specified --target-account-id is required
     You SHOULD NOT use this parameter as this command will leverage the SeedFarmer session manager!
     It is meant for development purposes.
    """,
    show_default=True,
)
@click.option(
    "--local/--remote",
    default=False,
    help="Indicates whether to use local session role or the SeedFarmer roles",
    show_default=True,
    type=bool,
)
@click.option(
    "--debug/--no-debug",
    default=False,
    help="Enable detailed logging.",
    show_default=True,
)
@bind_session_mgr
def store_deployspec(
    deployment: str,
    group: str,
    module: str,
    path: str,
    profile: Optional[str],
    region: Optional[str],
    qualifier: Optional[str],
    project: Optional[str],
    target_account_id: Optional[str],
    target_region: Optional[str],
    local: bool,
    debug: bool,
) -> None:
    if debug:
        enable_debug(format=DEBUG_LOGGING_FORMAT)

    _logger.debug(
        f"""Storing deployspec for module {module} of group {group}
        in deployment {deployment} located at {path}/deployspec.yaml"""
    )

    if project is None:
        project = _load_project()

    session: Session = Session(profile_name=profile, region_name=region)
    if (target_account_id is not None) != (target_region is not None):
        raise seedfarmer.errors.InvalidConfigurationError(
            "Must either specify both --target-account-id and --target-region, or neither"
        )
    elif target_account_id is not None and target_region is not None:
        session = (
            SessionManager()
            .get_or_create(project_name=project, profile=profile, region_name=region, qualifier=qualifier)
            .get_deployment_session(account_id=target_account_id, region_name=target_region)
        )

    du.update_deployspec(deployment, group, module, path, session=session)


@store.command(
    name="moduledata",
    help="""CAT or pipe in a json or yaml object.
      This command is meant to be run by seedfarmer ONLY!!!
      It is run within the context of the build job.
      Do not use this unless you are sure of the ramifications!
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
    "--project",
    "-p",
    help="Project identifier",
    required=False,
    default=None,
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
    "--qualifier",
    default=None,
    help="""A qualifier to use with the seedfarmer roles.
     Use only if bootstrapped with this qualifier""",
    required=False,
)
@click.option(
    "--target-account-id",
    default=None,
    help="Account Id of the target account to store module metadata, if specified --target-region is required",
    show_default=True,
)
@click.option(
    "--target-region",
    default=None,
    help="Region of the target account to store module metadata, if specified --target-account-id is required",
    show_default=True,
)
@click.option(
    "--local/--remote",
    default=False,
    help="Indicates whether to use local session role or the SeedFarmer roles",
    show_default=True,
    type=bool,
)
@click.option(
    "--debug/--no-debug",
    default=False,
    help="Enable detailed logging.",
    show_default=True,
)
@bind_session_mgr
def store_module_metadata(
    deployment: str,
    group: str,
    module: str,
    project: Optional[str],
    profile: Optional[str],
    region: Optional[str],
    qualifier: Optional[str],
    target_account_id: Optional[str],
    target_region: Optional[str],
    local: bool,
    debug: bool,
) -> None:
    if debug:
        enable_debug(format=DEBUG_LOGGING_FORMAT)
    _logger.debug("Writing metadata for module %s in deployment %s", module, deployment)

    if project is None:
        project = _load_project()

    session: Session = Session(profile_name=profile, region_name=region)
    if (target_account_id is not None) != (target_region is not None):
        raise seedfarmer.errors.InvalidConfigurationError(
            "Must either specify both --target-account-id and --target-region, or neither"
        )
    elif target_account_id is not None and target_region is not None:
        session = (
            SessionManager()
            .get_or_create(project_name=project, profile=profile, region_name=region, qualifier=qualifier)
            .get_deployment_session(account_id=target_account_id, region_name=target_region)
        )

    d = yaml.safe_load(sys.stdin.read())
    if d:
        mi.write_metadata(deployment=deployment, group=group, module=module, data=d, session=session)
    else:
        _logger.info("No Data avaiable...skipping")


@store.command(
    name="md5",
    help="""CAT or pipe in a string.
            This command is meant to be run by seedfarmer ONLY!!!""",
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
    "--type",
    "-t",
    type=str,
    help="The kind of MD5: bundle or spec",
    required=True,
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
    "--qualifier",
    default=None,
    help="""A qualifier to use with the seedfarmer roles.
     Use only if bootstrapped with this qualifier""",
    required=False,
)
@click.option(
    "--target-account-id",
    default=None,
    help="Account Id of the target account to store md5, if specified --target-region is required",
    show_default=True,
)
@click.option(
    "--target-region",
    default=None,
    help="Region of the target account to store md5, if specified --target-account-id is required",
    show_default=True,
)
@click.option(
    "--local/--remote",
    default=False,
    help="Indicates whether to use local session role or the SeedFarmer roles",
    show_default=True,
    type=bool,
)
@click.option(
    "--debug/--no-debug",
    default=False,
    help="Enable detailed logging.",
    show_default=True,
)
@bind_session_mgr
def store_module_md5(
    deployment: str,
    group: str,
    module: str,
    type: str,
    project: Optional[str],
    target_account_id: Optional[str],
    target_region: Optional[str],
    profile: Optional[str],
    region: Optional[str],
    qualifier: Optional[str],
    local: bool,
    debug: bool,
) -> None:
    if debug:
        enable_debug(format=DEBUG_LOGGING_FORMAT)
    _logger.debug("Writing md5 of  %s for module %s in deployment %s", type, module, deployment)

    if project is None:
        project = _load_project()

    session: Session = Session(profile_name=profile, region_name=region)
    if (target_account_id is not None) != (target_region is not None):
        raise seedfarmer.errors.InvalidConfigurationError(
            "Must either specify both --target-account-id and --target-region, or neither"
        )
    elif target_account_id is not None and target_region is not None:
        session = (
            SessionManager()
            .get_or_create(project_name=project, profile=profile, region_name=region, qualifier=qualifier)
            .get_deployment_session(account_id=target_account_id, region_name=target_region)
        )

    d = sys.stdin.readline().strip()
    if d:
        if type.casefold() == "bundle":
            _type = mi.ModuleConst.BUNDLE
        elif type.casefold() == "spec":
            _type = mi.ModuleConst.DEPLOYSPEC
        mi.write_module_md5(deployment=deployment, group=group, module=module, hash=d, type=_type, session=session)
    else:
        _logger.info("No Data available...skipping")
