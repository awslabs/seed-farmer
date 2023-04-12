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
import os
import sys
from typing import Optional

import click
from dotenv import load_dotenv

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
from seedfarmer.services.session_manager import SessionManager

_logger: logging.Logger = logging.getLogger(__name__)


def _load_project() -> str:
    try:
        _logger.info("No --project provided, attempting load from seedfarmer.yaml")
        return config.PROJECT
    except FileNotFoundError:
        print_bolded("Unable to determine project to bootstrap, one of --project or a seedfarmer.yaml is required")
        raise click.ClickException("Failed to determine project identifier")


def _error_messaging(deployment: str, group: str, module: str) -> None:
    print(f"No module data found for {deployment}-{group}-{module}")
    print_bolded("To see all deployments, run seedfarmer list deployments")
    print_bolded(f"To see all deployed modules in {deployment}, run seedfarmer list modules -d {deployment}")


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
    help="The AWS profile to use for boto3.Sessions",
    required=False,
)
@click.option(
    "--region",
    default=None,
    help="The AWS region of the toolchain",
    required=False,
)
@click.option(
    "--env-file",
    default=".env",
    help="A relative path to the .env file to load environment variables from",
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
    env_file: str,
    debug: bool,
) -> None:
    if debug:
        enable_debug(format=DEBUG_LOGGING_FORMAT)
    _logger.debug("We are fetching the dependencies for %s in %s of deployment %s", module, group, deployment)

    if project is None:
        project = _load_project()
    load_dotenv(dotenv_path=os.path.join(config.OPS_ROOT, env_file), verbose=True, override=True)

    SessionManager().get_or_create(project_name=project, profile=profile, region_name=region)
    dep_manifest = du.generate_deployed_manifest(deployment_name=deployment, skip_deploy_spec=True)

    if dep_manifest:
        module_depends_on_dict, module_dependencies_dict = du.generate_dependency_maps(manifest=dep_manifest)
        print_dependency_list(
            header_message=f"Modules that {module} in {group} of {deployment} DEPENDS ON : ",
            modules=module_depends_on_dict[f"{group}-{module}"],
        ) if module_depends_on_dict.get(f"{group}-{module}") else None
        print_dependency_list(
            header_message=f"Modules that ARE DEPENDENT ON {module} in {group} of {deployment} : ",
            modules=module_dependencies_dict[f"{group}-{module}"],
        ) if module_dependencies_dict.get(f"{group}-{module}") else None


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
    help="The AWS profile to use for boto3.Sessions",
    required=False,
)
@click.option(
    "--region",
    default=None,
    help="The AWS region of the toolchain",
    required=False,
)
@click.option(
    "--env-file",
    default=".env",
    help="A relative path to the .env file to load environment variables from",
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
    env_file: str,
    debug: bool,
) -> None:
    if debug:
        enable_debug(format=DEBUG_LOGGING_FORMAT)
    _logger.debug("We are getting deployspec for  %s in %s of deployment %s", module, group, deployment)

    if project is None:
        project = _load_project()
    load_dotenv(dotenv_path=os.path.join(config.OPS_ROOT, env_file), verbose=True, override=True)

    session = SessionManager().get_or_create(project_name=project, profile=profile, region_name=region)
    dep_manifest = du.generate_deployed_manifest(deployment_name=deployment, skip_deploy_spec=True)

    if dep_manifest is None:
        print_json({})
        return

    dep_manifest.validate_and_set_module_defaults()
    try:
        session = session.get_deployment_session(
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
    help="The AWS profile to use for boto3.Sessions",
    required=False,
)
@click.option(
    "--region",
    default=None,
    help="The AWS region of the toolchain",
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
    default=".env",
    help="A relative path to the .env file to load environment variables from",
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
    env_file: str,
    export_local_env: bool,
    debug: bool,
) -> None:
    if debug:
        enable_debug(format=DEBUG_LOGGING_FORMAT)
    _logger.debug("We are getting module data for  %s in %s of %s", module, group, deployment)

    if project is None:
        project = _load_project()
    load_dotenv(dotenv_path=os.path.join(config.OPS_ROOT, env_file), verbose=True, override=True)

    session = SessionManager().get_or_create(project_name=project, profile=profile, region_name=region)
    dep_manifest = du.generate_deployed_manifest(deployment_name=deployment, skip_deploy_spec=True)

    if dep_manifest is None:
        _error_messaging(deployment, group, module)
        return

    dep_manifest.validate_and_set_module_defaults()
    try:
        session = session.get_deployment_session(
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
    help="The AWS profile to use for boto3.Sessions",
    required=False,
)
@click.option(
    "--region",
    default=None,
    help="The AWS region of the toolchain",
    required=False,
)
@click.option(
    "--env-file",
    default=".env",
    help="A relative path to the .env file to load environment variables from",
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
    env_file: str,
    debug: bool,
) -> None:
    if debug:
        enable_debug(format=DEBUG_LOGGING_FORMAT)
    _logger.debug("We are getting modules for %s", deployment)

    if project is None:
        project = _load_project()
    load_dotenv(dotenv_path=os.path.join(config.OPS_ROOT, env_file), verbose=True, override=True)
    SessionManager().get_or_create(project_name=project, profile=profile, region_name=region)

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
    help="The AWS profile to use for boto3.Sessions",
    required=False,
)
@click.option(
    "--region",
    default=None,
    help="The AWS region of the toolchain",
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
    debug: bool,
) -> None:
    if debug:
        enable_debug(format=DEBUG_LOGGING_FORMAT)
    if project is None:
        project = _load_project()
    _logger.debug("Listing all deployments for Project %s", project)

    deps = mi.get_all_deployments(
        session=SessionManager()
        .get_or_create(project_name=project, profile=profile, region_name=region)
        .toolchain_session
    )
    print_deployment_inventory(description="Deployment Names", dep=deps)


@list.command(name="buildparams", help="Fetch the environment params of an executed build")
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
    help="The AWS profile to use for boto3.Sessions",
    required=False,
)
@click.option(
    "--region",
    default=None,
    help="The AWS region of the toolchain",
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
    default=".env",
    help="A relative path to the .env file to load environment variables from",
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
    env_file: str,
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
    load_dotenv(dotenv_path=os.path.join(config.OPS_ROOT, env_file), verbose=True, override=True)

    session = SessionManager().get_or_create(project_name=project, profile=profile, region_name=region)
    dep_manifest = du.generate_deployed_manifest(
        deployment_name=deployment, skip_deploy_spec=True, ignore_deployed=True
    )

    if dep_manifest is None:
        _error_messaging(deployment, group, module)
        return

    dep_manifest.validate_and_set_module_defaults()
    try:
        session = session.get_deployment_session(
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
