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
from typing import Any, Callable, Dict, Iterable, List, NamedTuple, Optional, Union,cast
from boto3 import Session
import botocore.exceptions
import yaml
import time
from datetime import datetime, timezone
from enum import Enum

import seedfarmer
from seedfarmer.services._service_utils import boto3_client, get_region, get_sts_identity_info, try_it
from seedfarmer.errors.codeseeder_errors import CodeSeederRuntimeError

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



def get_build_data(build_ids: List[str], session: Optional[Union[Callable[[], Session], Session]] = None) -> Optional[Dict[str, Any]]:
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
        "buildspecOverride": yaml.safe_dump(data=buildspec, sort_keys=False, indent=4),
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

    Raises
    ------
    RuntimeError
        If the CodeBuild doesn't succeed
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

    if build.status is not BuildStatus.succeeded:
        account_id, _, partition = get_sts_identity_info(session=session)
        deploy_info = {
            "AWS_REGION": get_region(session=session),
            "AWS_ACCOUNT_ID": account_id,
            "AWS_PARTITION": partition,
            "CODEBUILD_BUILD_ID": build.build_id,
        }
        _logger.debug(f"Deploy Info on error from Codebuild {deploy_info}")
        raise CodeSeederRuntimeError("Build status was not SUCCEEDED ", error_info=deploy_info)

    _logger.debug(
        "start: %s | end: %s | elapsed: %s",
        build.start_time,
        build.end_time,
        build.duration_in_seconds,
    )


def generate_spec(
    stack_outputs: Dict[str, str],
    cmds_install: Optional[List[str]] = None,
    cmds_pre: Optional[List[str]] = None,
    cmds_build: Optional[List[str]] = None,
    cmds_post: Optional[List[str]] = None,
    env_vars: Optional[Dict[str, str]] = None,
    exported_env_vars: Optional[List[str]] = None,
    runtime_versions: Optional[Dict[str, str]] = None,
    abort_phases_on_failure: bool = True,
    pypi_mirror: Optional[str] = None,
    npm_mirror: Optional[str] = None,
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
    pre: List[str] = [] if cmds_pre is None else cmds_pre
    build: List[str] = [] if cmds_build is None else cmds_build
    post: List[str] = [] if cmds_post is None else cmds_post
    variables: Dict[str, str] = {} if env_vars is None else env_vars
    exported_variables: List[str] = [] if exported_env_vars is None else exported_env_vars
    exported_variables.append("AWS_CODESEEDER_OUTPUT")
    install = [
        "mkdir -p /var/scripts/",
        "mv $CODEBUILD_SRC_DIR/bundle/retrieve_docker_creds.py /var/scripts/retrieve_docker_creds.py || true",
        "/var/scripts/retrieve_docker_creds.py && echo 'Docker logins successful' || echo 'Docker logins failed'",
    ]
    if pypi_mirror is not None:
        install.append("mv $CODEBUILD_SRC_DIR/bundle/pypi_mirror_support.py /var/scripts/pypi_mirror_support.py")
        install.append(f"/var/scripts/pypi_mirror_support.py {pypi_mirror} && echo 'Pypi Mirror Set'")

    if npm_mirror:
        install.append("mv $CODEBUILD_SRC_DIR/bundle/npm_mirror_support.py /var/scripts/npm_mirror_support.py")
        install.append(f"/var/scripts/npm_mirror_support.py {npm_mirror} && echo 'NPM Mirror Set'")
        
    install.append(
        "if curl -s --head https://astral.sh | grep '200' > /dev/null; then\n"
        "  curl -Ls https://astral.sh/uv/install.sh | sh\n"
        "else\n"
        "  pip install uv\n"
        "fi",
    )
    install.append("export PATH=$PATH:/root/.local/bin")
    install.append("uv venv  ~/.venv --python 3.11")  ## DGRABS - Make this configurable
    install.append(". ~/.venv/bin/activate")
        
    ### uv tool does NOT support aws codeartifact, so if that is being used, need to 
    ## install with pipx
    if "CodeArtifactDomain" in stack_outputs and "CodeArtifactRepository" in stack_outputs:
        install.append(
            "aws codeartifact login --tool pip "
            f"--domain {stack_outputs['CodeArtifactDomain']} "
            f"--repository {stack_outputs['CodeArtifactRepository']}"
        )
        install.append("uv pip install pipx~=1.7.1")
        install.append(f"pipx install seed-farmer=={seedfarmer.__version__}")  ## uv doesn't have support fo code artifact
    else: 
        install.append(f"uv tool install seed-farmer=={seedfarmer.__version__}")
        

    if cmds_install is not None:
        install += cmds_install

    on_failure = "ABORT" if abort_phases_on_failure else "CONTINUE"
    return_spec: Dict[str, Any] = {
        "version": 0.2,
        "env": {"shell": "bash", "variables": variables, "exported-variables": exported_variables},
        "phases": {
            "install": {
                "commands": install,
                "on-failure": on_failure,
            },
            "pre_build": {
                "commands": pre,
                "on-failure": on_failure,
            },
            "build": {
                "commands": build,
                "on-failure": on_failure,
            },
            "post_build": {
                "commands": post,
                "on-failure": on_failure,
            },
        },
    }
    if runtime_versions:
        return_spec["phases"]["install"]["runtime-versions"] = runtime_versions

    _logger.debug(return_spec)
    return return_spec
