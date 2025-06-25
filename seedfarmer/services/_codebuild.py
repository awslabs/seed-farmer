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

import io
import logging
import time
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Callable, Dict, Iterable, List, NamedTuple, Optional, Union, cast

import botocore.exceptions
import yaml
from boto3 import Session

from seedfarmer.errors import InvalidConfigurationError
from seedfarmer.services._service_utils import boto3_client, try_it
from seedfarmer.utils import LiteralStr

_logger: logging.Logger = logging.getLogger(__name__)
_BUILD_WAIT_POLLING_DELAY: float = 5  # SECONDS


class BuildStatus(Enum):
    failed = "FAILED"
    fault = "FAULT"
    in_progress = "IN_PROGRESS"
    stopped = "STOPPED"
    succeeded = "SUCCEEDED"
    timed_out = "TIMED_OUT"


class BuildPhaseType(Enum):
    build = "BUILD"
    completed = "COMPLETED"
    download_source = "DOWNLOAD_SOURCE"
    finalizing = "FINALIZING"
    install = "INSTALL"
    post_build = "POST_BUILD"
    pre_build = "PRE_BUILD"
    provisioning = "PROVISIONING"
    queued = "QUEUED"
    submitted = "SUBMITTED"
    upload_artifacts = "UPLOAD_ARTIFACTS"


class BuildPhaseStatus(Enum):
    failed = "FAILED"
    fault = "FAULT"
    queued = "QUEUED"
    in_progress = "IN_PROGRESS"
    stopped = "STOPPED"
    succeeded = "SUCCEEDED"
    timed_out = "TIMED_OUT"


class BuildPhaseContext(NamedTuple):
    status_code: Optional[str]
    message: Optional[str]


class BuildPhase(NamedTuple):
    phase_type: BuildPhaseType
    status: Optional[BuildPhaseStatus]
    start_time: datetime
    end_time: Optional[datetime]
    duration_in_seconds: float
    contexts: List[BuildPhaseContext]


class BuildCloudWatchLogs(NamedTuple):
    enabled: bool
    group_name: Optional[str]
    stream_name: Optional[str]


class BuildInfo(NamedTuple):
    build_id: str
    status: BuildStatus
    current_phase: BuildPhaseType
    start_time: datetime
    end_time: Optional[datetime]
    duration_in_seconds: float
    phases: List[BuildPhase]
    logs: BuildCloudWatchLogs
    exported_env_vars: Dict[str, str]


def get_build_data(
    build_ids: List[str], session: Optional[Union[Callable[[], Session], Session]] = None
) -> Optional[Dict[str, Any]]:
    client = boto3_client(service_name="codebuild", session=session)

    try:
        return cast(Dict[str, Any], client.batch_get_builds(ids=build_ids))
    except Exception as e:
        _logger.error("An error occurred fetching the build info for %s - %s", build_ids, e)
        return None


def start(
    project_name: str,
    stream_name: str,
    bundle_location: str,
    buildspec: Dict[str, Any],
    timeout: int,
    overrides: Optional[Dict[str, Any]] = None,
    session: Optional[Union[Callable[[], Session], Session]] = None,
    yaml_dumper: Optional[Any] = None,  # Accepts ruamel.yaml.YAML instance or PyYAML dump function
) -> str:
    """Start a CodeBuild Project execution

    Parameters
    ----------
    project_name : str
        Name of the CodeBuild Project
    stream_name : str
        Name of the CloudWatch Logs Stream to read CodeBuild logs from
    bundle_location : str
        S3 Location of the zip bundle to use as Source to the CodeBuild execution
    buildspec : Dict[str, Any]
        BuildSpec to use for the CodeBuild execution
    timeout : int
        Timeout of the CodeBuild execution
    overrides : Optional[Dict[str, Any]], optional
        Additional overrides to set on the CodeBuild execution, by default None
    session: Optional[Union[Callable[[], Session], Session]], optional
        Optional Session or function returning a Session to use for all boto3 operations, by default None

    Returns
    -------
    str
        The CodeBuild Build/Exectuion Id
    """
    # If no dumper is provided, use PyYAML's safe_dump
    if yaml_dumper is None:

        def default_pyyaml_dumper(data):  # type: ignore[no-untyped-def]
            return yaml.safe_dump(data, sort_keys=False, indent=4)

        yaml_dumper = default_pyyaml_dumper

    # ruamel.yaml.YAML instance: has a .dump method
    if hasattr(yaml_dumper, "dump"):
        stream = io.StringIO()
        yaml_dumper.dump(buildspec, stream)
        buildspec_yaml = stream.getvalue()
        stream.close()
    # PyYAML: function like yaml.dump or yaml.safe_dump
    elif callable(yaml_dumper):
        buildspec_yaml = yaml_dumper(buildspec)
    else:
        raise InvalidConfigurationError("yaml_dumper must be a ruamel.yaml.YAML instance or a PyYAML dump function.")

    client = boto3_client("codebuild", session=session)
    image_override: Optional[str] = overrides.get("imageOverride", None) if overrides else None
    image_pull_credentials: Optional[str] = None
    if image_override:
        if image_override.startswith("aws/"):
            image_pull_credentials = "CODEBUILD"
        else:
            image_pull_credentials = "SERVICE_ROLE"
            _logger.debug("Image Pull Credentials: %s", image_pull_credentials)

    _logger.debug("Overrides: %s", overrides)
    build_params = {
        "projectName": project_name,
        "sourceTypeOverride": "S3",
        "sourceLocationOverride": bundle_location,
        "buildspecOverride": buildspec_yaml,
        "timeoutInMinutesOverride": timeout,
        "privilegedModeOverride": True,
        "logsConfigOverride": {
            "cloudWatchLogs": {
                "status": "ENABLED",
                "groupName": f"/aws/codebuild/{project_name}",
                "streamName": stream_name,
            },
            "s3Logs": {"status": "DISABLED"},
        },
    }
    if image_pull_credentials:
        build_params["imagePullCredentialsTypeOverride"] = image_pull_credentials

    if overrides:
        build_params = {**build_params, **overrides}

    response = client.start_build(**build_params)  # type: ignore[arg-type]
    return response["build"]["id"]


def fetch_build_info(build_id: str, session: Optional[Union[Callable[[], Session], Session]] = None) -> BuildInfo:
    """Fetch info on a CodeBuild execution

    Parameters
    ----------
    build_id : str
        CodeBuild Execution/Build Id
    session: Optional[Union[Callable[[], Session], Session]], optional
        Optional Session or function returning a Session to use for all boto3 operations, by default None

    Returns
    -------
    BuildInfo
        Info on the CodeBuild execution

    Raises
    ------
    RuntimeError
        If the Build Id is not found
    """
    client = boto3_client("codebuild", session=session)
    response: Dict[str, List[Dict[str, Any]]] = try_it(
        f=client.batch_get_builds, ex=botocore.exceptions.ClientError, ids=[build_id], max_num_tries=5
    )
    if not response["builds"]:
        raise RuntimeError(f"CodeBuild build {build_id} not found.")
    build = response["builds"][0]
    now = datetime.now(timezone.utc)
    log_enabled = True if build.get("logs", {}).get("cloudWatchLogs", {}).get("status") == "ENABLED" else False
    return BuildInfo(
        build_id=build_id,
        status=BuildStatus(value=build["buildStatus"]),
        current_phase=BuildPhaseType(value=build["currentPhase"]),
        start_time=build["startTime"],
        end_time=build.get("endTime", now),
        duration_in_seconds=(build.get("endTime", now) - build["startTime"]).total_seconds(),
        exported_env_vars={d["name"]: d["value"] for d in build.get("exportedEnvironmentVariables", [])},
        phases=[
            BuildPhase(
                phase_type=BuildPhaseType(value=p["phaseType"]),
                status=None if "phaseStatus" not in p else BuildPhaseStatus(value=p["phaseStatus"]),
                start_time=p["startTime"],
                end_time=p.get("endTime", now),
                duration_in_seconds=p.get("durationInSeconds"),
                contexts=[
                    BuildPhaseContext(status_code=p.get("statusCode"), message=p.get("message"))
                    for c in p.get("contexts", [])
                ],
            )
            for p in build["phases"]
        ],
        logs=BuildCloudWatchLogs(
            enabled=log_enabled,
            group_name=build["logs"]["cloudWatchLogs"].get("groupName") if log_enabled else None,
            stream_name=build["logs"]["cloudWatchLogs"].get("streamName") if log_enabled else None,
        ),
    )


def wait(build_id: str, session: Optional[Union[Callable[[], Session], Session]] = None) -> Iterable[BuildInfo]:
    """Wait for completion of a CodeBuild execution

    Parameters
    ----------
    build_id : str
        The CodeBuild Execution/Build Id
    session: Optional[Union[Callable[[], Session], Session]], optional
        Optional Session or function returning a Session to use for all boto3 operations, by default None

    Returns
    -------
    Iterable[BuildInfo]
        Info on the CodeBuild execution

    Yields
    -------
    Iterator[Iterable[BuildInfo]]
        Info on the CodeBuild execution

    """
    build = fetch_build_info(build_id=build_id, session=session)
    while build.status is BuildStatus.in_progress:
        time.sleep(_BUILD_WAIT_POLLING_DELAY)

        last_phase = build.current_phase
        last_status = build.status
        build = fetch_build_info(build_id=build_id, session=session)

        if build.current_phase is not last_phase or build.status is not last_status:
            _logger.info("phase: %s %s (%s)", build.current_phase.value, build.build_id, build.status.value)

        yield build

    yield build


def generate_spec(
    cmds_install: Optional[List[Union[str, LiteralStr]]] = None,
    cmds_pre: Optional[List[Union[str, LiteralStr]]] = None,
    cmds_build: Optional[List[Union[str, LiteralStr]]] = None,
    cmds_post: Optional[List[Union[str, LiteralStr]]] = None,
    env_vars: Optional[Dict[str, str]] = None,
    exported_env_vars: Optional[List[str]] = None,
    runtime_versions: Optional[Dict[str, str]] = None,
    abort_phases_on_failure: bool = True,
) -> Dict[str, Any]:
    """Generate a BuildSpec for a CodeBuild execution

    Parameters
    ----------
    stack_outputs : Dict[str, str]
        The CloudFormation Stack Outputs from the Seedkit Stack where the CodeBuild Project was created
    cmds_install : Optional[List[str]], optional
        Additional commands to run during the Install phase of the CodeBuild execution, by default None
    cmds_pre : Optional[List[str]], optional
        Additional commands to run during the PreBuild phase of the CodeBuild execution, by default None
    cmds_build : Optional[List[str]], optional
        Additional commands to run during the Build phase of the CodeBuild execution, by default None
    cmds_post : Optional[List[str]], optional
        Additional commands to run during the PostBuild phase of the CodeBuild execution, by default None
    env_vars: Optional[Dict[str, str]], optional
        Environment variables to set in the CodeBuild execution, by default None
    exported_env_vars: Optional[List[str]], optional
        Environment variables to export from the CodeBuild execution, by default None
    pypi_mirror: Optional[str], optional
        Pypi mirror to use, by default None
    npm_mirror: Optional[str], optional
        NPM mirror to use, by default None

    Returns
    -------
    Dict[str, Any]
        A CodeBuild BuildSpec
    """
    # pre: List[str] = [] if cmds_pre is None else cmds_pre
    # build: List[str] = [] if cmds_build is None else cmds_build
    # post: List[str] = [] if cmds_post is None else cmds_post
    variables: Dict[str, str] = {} if env_vars is None else env_vars
    # exported_variables: List[str] = [] if exported_env_vars is None else exported_env_vars

    on_failure = "ABORT" if abort_phases_on_failure else "CONTINUE"
    return_spec: Dict[str, Any] = {
        "version": 0.2,
        "env": {"shell": "bash", "variables": variables, "exported-variables": exported_env_vars or []},
        "phases": {
            "install": {
                "commands": cmds_install or [],
                "on-failure": on_failure,
            },
            "pre_build": {
                "commands": cmds_pre or [],
                "on-failure": on_failure,
            },
            "build": {
                "commands": cmds_build or [],
                "on-failure": on_failure,
            },
            "post_build": {
                "commands": cmds_post or [],
                "on-failure": on_failure,
            },
        },
    }
    if runtime_versions:
        return_spec["phases"]["install"]["runtime-versions"] = runtime_versions

    _logger.debug(return_spec)
    return return_spec
