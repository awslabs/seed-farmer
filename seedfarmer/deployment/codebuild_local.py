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
import subprocess
import uuid
from datetime import datetime, timezone
from typing import Dict, Optional

import seedfarmer.services._codebuild as codebuild

_logger: logging.Logger = logging.getLogger(__name__)


def run(
    local_deploy_path: str,
    env_vars: Dict[str, str] = {},
    codebuild_image: Optional[str] = None,
) -> codebuild.BuildInfo:
    # Write the environment variables to the file
    env_vars_path = os.path.join(local_deploy_path, "local.env")
    with open(env_vars_path, "w") as f:
        for key, value in env_vars.items():
            f.write(f"{key}={value}\n")

    ## Extract the zip to the local root so it is mounted by the container

    codebuild_image = (
        codebuild_image if codebuild_image else "public.ecr.aws/codebuild/amazonlinux2-x86_64-standard:5.0"
    )

    docker_command = [
        "docker",
        "run",
        "-v",
        "/var/run/docker.sock:/var/run/docker.sock",
        "-e",
        f"IMAGE_NAME={codebuild_image}",
        "-e",
        f"ARTIFACTS={local_deploy_path}/artifacts",
        "-e",
        f"SOURCE={local_deploy_path}/",
        "-e",
        f"BUILDSPEC={local_deploy_path}/buildspec/buildspec.yaml",
        "-v",
        f"{local_deploy_path}/:/LocalBuild/envFile/",
        "-e",
        "ENV_VAR_FILE=local.env",
        "-e",
        f"AWS_CONFIGURATION={os.environ.get('HOME')}/.aws",
        "-e",
        "AWS_EC2_METADATA_DISABLED=true",
        "-e",
        "MOUNT_SOURCE_DIRECTORY=TRUE",
        "-e",
        "INITIATOR=codebuild-user",
        "-e",
        f"COMPOSE_PROJECT_NAME=agent-{str(uuid.uuid4())[:8]}",
        "-e",
        f"REPORTS={local_deploy_path}/logs",
    ]

    for key, value in os.environ.items():
        if key.startswith("AWS_"):
            env_current = ["-e", f"{key}={value}"]
            docker_command.extend(env_current)

    docker_command.append("public.ecr.aws/codebuild/local-builds:latest")

    try:
        start_time = datetime.now(timezone.utc)
        _logger.debug("Running local Docker deployment: \n%s", " ".join(docker_command))

        process = subprocess.run(docker_command, check=True)

        end_time = datetime.now(timezone.utc)
        duration = (end_time - start_time).total_seconds()

        return codebuild.BuildInfo(
            build_id="local",
            status=codebuild.BuildStatus.succeeded if process.returncode == 0 else codebuild.BuildStatus.failed,
            start_time=start_time,
            end_time=end_time,
            duration_in_seconds=duration,
            current_phase=codebuild.BuildPhaseType.build,
            exported_env_vars=env_vars,
            phases=None,  # type: ignore[arg-type]
            logs=None,  # type: ignore[arg-type]
        )
    except KeyboardInterrupt:
        _logger.info("Interrupted by the user")
    except (subprocess.CalledProcessError, Exception) as e:
        _logger.error(e)

    end_time = datetime.now(timezone.utc)
    duration = (end_time - start_time).total_seconds()

    return codebuild.BuildInfo(
        build_id="local",
        status=codebuild.BuildStatus.failed,
        start_time=start_time,
        end_time=datetime.now(timezone.utc),
        duration_in_seconds=duration,
        current_phase=codebuild.BuildPhaseType.build,
        exported_env_vars=env_vars,
        phases=None,  # type: ignore[arg-type]
        logs=None,  # type: ignore[arg-type]
    )
