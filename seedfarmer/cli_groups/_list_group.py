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

import json
import logging
import sys
from typing import List, Optional

import boto3
import click

import seedfarmer.messages as messages
import seedfarmer.mgmt.build_info as bi
import seedfarmer.mgmt.deploy_utils as du
import seedfarmer.mgmt.module_info as mi
from seedfarmer import DEBUG_LOGGING_FORMAT, commands, config, enable_debug
from seedfarmer.output_utils import (
    print_bolded,
    print_dependency_list,
    print_deployment_inventory,
    print_json,
    print_manifest_inventory,
)
from seedfarmer.services import get_sts_identity_info
from seedfarmer.services.session_manager import ISessionManager, SessionManager
from seedfarmer.utils import load_dotenv_files

_logger: logging.Logger = logging.getLogger(__name__)


def _load_project() -> str:
    try:
        _logger.info("No --project provided, attempting load from seedfarmer.yaml")
        return config.PROJECT
    except FileNotFoundError:
        print_bolded("Unable to determine project to bootstrap, one of --project or a seedfarmer.yaml is required")
        raise click.ClickException("Failed to determine project identifier")


def _error_messaging(deployment: str, group: Optional[str] = None, module: Optional[str] = None) -> None:
    if group and module:
        print(f"No module data found for {deployment}-{group}-{module}")
        print_bolded(f"To see all deployed modules in {deployment}, run seedfarmer list modules -d {deployment}")
    else:
        print(f"No module data found for {deployment}")
    print_bolded("To see all deployments, run seedfarmer list deployments")


@click.group(name="list", help="List the relative data (module or deployment)")
def list() -> None:
    """List module data"""
    pass


@list.command(name="dependencies", help="List all dependencies of a module")
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
    "--env-file",
    "env_files",
    default=[".env"],
    help="""A relative path to the .env file to load environment variables from.
    Multple files can be passed in by repeating this flag, and the order will be
    preserved when overriding duplicate values.
    """,
    multiple=True,
    required=False,
)
@click.option(
    "--debug/--no-debug",
    default=False,
    help="Enable detailed logging.",
    show_default=True,
)
def list_dependencies(
    deployment: str,
    group: str,
    module: str,
    project: Optional[str],
    profile: Optional[str],
    region: Optional[str],
    qualifier: Optional[str],
    env_files: List[str],
    debug: bool,
) -> None:
    if debug:
        enable_debug(format=DEBUG_LOGGING_FORMAT)
    _logger.debug("We are fetching the dependencies for %s in %s of deployment %s", module, group, deployment)

    if project is None:
        project = _load_project()

    load_dotenv_files(config.OPS_ROOT, env_files=env_files)

    SessionManager().get_or_create(project_name=project, profile=profile, region_name=region, qualifier=qualifier)
    dep_manifest = du.generate_deployed_manifest(deployment_name=deployment, skip_deploy_spec=True)

    if dep_manifest:
        module_depends_on_dict, module_dependencies_dict = du.generate_dependency_maps(manifest=dep_manifest)
        (
            print_dependency_list(
                header_message=f"Modules that {module} in {group} of {deployment} DEPENDS ON : ",
                modules=module_depends_on_dict[f"{group}-{module}"],
            )
            if module_depends_on_dict.get(f"{group}-{module}")
            else None
        )
        (
            print_dependency_list(
                header_message=f"Modules that ARE DEPENDENT ON {module} in {group} of {deployment} : ",
                modules=module_dependencies_dict[f"{group}-{module}"],
            )
            if module_dependencies_dict.get(f"{group}-{module}")
            else None
        )


@list.command(name="deployspec", help="List the stored deployspec of a module")
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
    "--env-file",
    "env_files",
    default=[".env"],
    help="""A relative path to the .env file to load environment variables from.
    Multple files can be passed in by repeating this flag, and the order will be
    preserved when overriding duplicate values.
    """,
    multiple=True,
    required=False,
)
@click.option(
    "--debug/--no-debug",
    default=False,
    help="Enable detailed logging.",
    show_default=True,
)
def list_deployspec(
    deployment: str,
    group: str,
    module: str,
    project: Optional[str],
    profile: Optional[str],
    region: Optional[str],
    qualifier: Optional[str],
    env_files: List[str],
    debug: bool,
) -> None:
    if debug:
        enable_debug(format=DEBUG_LOGGING_FORMAT)
    _logger.debug("We are getting deployspec for  %s in %s of deployment %s", module, group, deployment)

    if project is None:
        project = _load_project()

    load_dotenv_files(config.OPS_ROOT, env_files=env_files)

    session_manager: ISessionManager = SessionManager().get_or_create(
        project_name=project, profile=profile, region_name=region, qualifier=qualifier
    )
    dep_manifest = du.generate_deployed_manifest(deployment_name=deployment, skip_deploy_spec=True)

    if dep_manifest is None:
        print_json({})
        return

    dep_manifest.validate_and_set_module_defaults()
    try:
        session = session_manager.get_deployment_session(
            account_id=dep_manifest.get_module(group=group, module=module).get_target_account_id(),  # type: ignore
            region_name=dep_manifest.get_module(group=group, module=module).target_region,  # type: ignore
        )
    except Exception:
        _error_messaging(deployment, group, module)
        return

    val = mi.get_deployspec(deployment=deployment, group=group, module=module, session=session)
    print_json(val)


@list.command(name="moduledata", help="Fetch the module metadata")
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
    "--export-local-env/--no-export-local-env",
    default=False,
    help="Print the moduledata as env parameters for local development support INSTEAD of json (default is FALSE)",
    show_default=True,
)
@click.option(
    "--env-file",
    "env_files",
    default=[".env"],
    help="""A relative path to the .env file to load environment variables from.
    Multple files can be passed in by repeating this flag, and the order will be
    preserved when overriding duplicate values.
    """,
    multiple=True,
    required=False,
)
@click.option(
    "--debug/--no-debug",
    default=False,
    help="Enable detailed logging.",
    show_default=True,
)
def list_module_metadata(
    deployment: str,
    group: str,
    module: str,
    project: Optional[str],
    profile: Optional[str],
    region: Optional[str],
    qualifier: Optional[str],
    env_files: List[str],
    export_local_env: bool,
    debug: bool,
) -> None:
    if debug:
        enable_debug(format=DEBUG_LOGGING_FORMAT)
    _logger.debug("We are getting module data for  %s in %s of %s", module, group, deployment)

    if project is None:
        project = _load_project()

    load_dotenv_files(config.OPS_ROOT, env_files=env_files)

    session_manager: ISessionManager = SessionManager().get_or_create(
        project_name=project, profile=profile, region_name=region, qualifier=qualifier
    )
    dep_manifest = du.generate_deployed_manifest(deployment_name=deployment, skip_deploy_spec=True)

    if dep_manifest is None:
        _error_messaging(deployment, group, module)
        return

    dep_manifest.validate_and_set_module_defaults()
    try:
        session = session_manager.get_deployment_session(
            account_id=dep_manifest.get_module(group=group, module=module).get_target_account_id(),  # type: ignore
            region_name=dep_manifest.get_module(group=group, module=module).target_region,  # type: ignore
        )
    except Exception:
        _error_messaging(deployment, group, module)
        return

    metadata_json = mi.get_module_metadata(deployment, group, module, session=session)
    if not export_local_env:
        sys.stdout.write(json.dumps(metadata_json))
    else:
        envs = commands.generate_export_env_params(metadata_json)
        if envs:
            for exp in envs:
                sys.stdout.write(exp)
                sys.stdout.write("\n")
        else:
            _error_messaging(deployment, group, module)


@list.command(name="allmoduledata", help="Fetch ALL module metadata in the deployment as a dict")
@click.option(
    "--deployment",
    "-d",
    type=str,
    help="The Deployment Name",
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
    "--env-file",
    "env_files",
    default=[".env"],
    help="""A relative path to the .env file to load environment variables from.
    Multple files can be passed in by repeating this flag, and the order will be
    preserved when overriding duplicate values.
    """,
    multiple=True,
    required=False,
)
@click.option(
    "--debug/--no-debug",
    default=False,
    help="Enable detailed logging.",
    show_default=True,
)
def list_all_module_metadata(
    deployment: str,
    project: Optional[str],
    profile: Optional[str],
    region: Optional[str],
    qualifier: Optional[str],
    env_files: List[str],
    debug: bool,
) -> None:
    if debug:
        enable_debug(format=DEBUG_LOGGING_FORMAT)
    _logger.debug("We are getting all module data for  %s", deployment)

    if project is None:
        project = _load_project()

    load_dotenv_files(config.OPS_ROOT, env_files=env_files)

    session = SessionManager().get_or_create(
        project_name=project, profile=profile, region_name=region, qualifier=qualifier
    )
    dep_manifest = du.generate_deployed_manifest(deployment_name=deployment, skip_deploy_spec=True)

    if dep_manifest is None:
        _error_messaging(deployment)
        return
    dep_manifest.validate_and_set_module_defaults()
    try:
        all_metadata_json = {
            f"{group.name}-{module.name}": mi.get_module_metadata(
                deployment=deployment,
                group=group.name,
                module=module.name,
                session=(
                    session.get_deployment_session(
                        account_id=module.get_target_account_id(),  # type: ignore
                        region_name=module.target_region,  # type: ignore
                    )
                ),
            )
            for group in dep_manifest.groups
            for module in group.modules
        }
        sys.stdout.write(json.dumps(all_metadata_json))
    except Exception:
        _error_messaging(deployment)
        return


@list.command(name="modules", help="List the modules in a deployment")
@click.option(
    "--deployment",
    "-d",
    type=str,
    help="The Deployment Name",
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
    "--env-file",
    "env_files",
    default=[".env"],
    help="""A relative path to the .env file to load environment variables from.
    Multple files can be passed in by repeating this flag, and the order will be
    preserved when overriding duplicate values.
    """,
    multiple=True,
    required=False,
)
@click.option(
    "--debug/--no-debug",
    default=False,
    help="Enable detailed logging.",
    show_default=True,
)
def list_modules(
    deployment: str,
    project: Optional[str],
    profile: Optional[str],
    region: Optional[str],
    qualifier: Optional[str],
    env_files: List[str],
    debug: bool,
) -> None:
    if debug:
        enable_debug(format=DEBUG_LOGGING_FORMAT)
    _logger.debug("We are getting modules for %s", deployment)

    if project is None:
        project = _load_project()

    load_dotenv_files(config.OPS_ROOT, env_files=env_files)

    SessionManager().get_or_create(project_name=project, profile=profile, region_name=region, qualifier=qualifier)

    dep_manifest = du.generate_deployed_manifest(deployment_name=deployment, skip_deploy_spec=True)
    if dep_manifest:
        print_manifest_inventory("Deployed Modules", dep_manifest, False, "green")


@list.command(name="deployments", help="List the deployments in this account")
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
    "--debug/--no-debug",
    default=False,
    help="Enable detailed logging.",
    show_default=True,
)
def list_deployments(
    project: Optional[str],
    profile: Optional[str],
    region: Optional[str],
    qualifier: Optional[str],
    debug: bool,
) -> None:
    if debug:
        enable_debug(format=DEBUG_LOGGING_FORMAT)
    if project is None:
        project = _load_project()
    _logger.debug("Listing all deployments for Project %s", project)

    session_manager = SessionManager().get_or_create(
        project_name=project, profile=profile, region_name=region, qualifier=qualifier
    )
    deps = mi.get_all_deployments(session=session_manager.toolchain_session)
    if not deps or len(deps) == 0:
        account_id, _, _ = get_sts_identity_info(session=session_manager.toolchain_session)
        region = session_manager.toolchain_session.region_name
        _logger.info("No Deployments found for project %s in account %s and region %s", project, account_id, region)
        print_bolded(message=messages.no_deployment_found(), color="yellow")
    else:
        print_deployment_inventory(description="Deployment Names", dep=deps)


@list.command(
    name="buildparams",
    help="""Fetch the environment params of an executed build.
               This is to help with local development efforts.""",
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
    "--build-id",
    type=str,
    help="The Build ID to fetch this info for",
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
    "--export-local-env/--no-export-local-env",
    default=False,
    help="Print the moduledata as env parameters for local development support INSTEAD of json (default is FALSE)",
    show_default=True,
)
@click.option(
    "--env-file",
    "env_files",
    default=[".env"],
    help="""A relative path to the .env file to load environment variables from.
    Multple files can be passed in by repeating this flag, and the order will be
    preserved when overriding duplicate values.
    """,
    multiple=True,
    required=False,
)
@click.option(
    "--debug/--no-debug",
    default=False,
    help="Enable detailed logging.",
    show_default=True,
)
def list_build_env_params(
    deployment: str,
    group: str,
    module: str,
    build_id: str,
    project: Optional[str],
    profile: Optional[str],
    region: Optional[str],
    qualifier: Optional[str],
    env_files: List[str],
    export_local_env: str,
    debug: bool,
) -> None:
    if debug:
        enable_debug(format=DEBUG_LOGGING_FORMAT)
    _logger.debug(
        "We are getting build environment parameters for id %s of %s in %s of %s", build_id, module, group, deployment
    )

    if project is None:
        project = _load_project()

    load_dotenv_files(config.OPS_ROOT, env_files=env_files)

    session_manager: ISessionManager = SessionManager().get_or_create(
        project_name=project, profile=profile, region_name=region, qualifier=qualifier
    )
    dep_manifest = du.generate_deployed_manifest(
        deployment_name=deployment, skip_deploy_spec=True, ignore_deployed=True
    )

    if dep_manifest is None:
        _error_messaging(deployment, group, module)
        return

    dep_manifest.validate_and_set_module_defaults()
    try:
        session: boto3.Session = session_manager.get_deployment_session(
            account_id=dep_manifest.get_module(group=group, module=module).get_target_account_id(),  # type: ignore
            region_name=dep_manifest.get_module(group=group, module=module).target_region,  # type: ignore
        )
    except Exception:
        _error_messaging(deployment, group, module)
        return

    metadata_json = bi.get_build_env_params(build_ids=[build_id], session=session)
    if not export_local_env:
        sys.stdout.write(json.dumps(metadata_json))
    else:
        envs = commands.generate_export_raw_env_params(metadata=metadata_json)
        if envs:
            for exp in envs:
                sys.stdout.write(exp)
                sys.stdout.write("\n")
        else:
            _error_messaging(deployment, group, module)


@list.command(
    name="schema",
    help="""Generate the schema that SeedFarmer uses for manifest objects.
             Either the deployment manifest or module manifest schema
             can be requested.
             This will return a formatted string of the schema that can
             be piped to a file. """,
)
@click.option(
    "--type",
    "-t",
    type=click.Choice(["deployment", "module"], case_sensitive=True),
    help="Either 'deployment' or 'module' can be used, default is `deployment`",
    required=False,
    default="deployment",
)
def list_manifest_schema(type: str) -> None:
    print(json.dumps(bi.get_manifest_schema(type=type), indent=2))
