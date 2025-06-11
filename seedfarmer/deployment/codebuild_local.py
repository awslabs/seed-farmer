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


import os
import subprocess
from typing import Dict, Optional


def run(
    local_deploy_path: str,
    env_vars: Dict[str, str] = {},
    codebuild_image: Optional[str] = None,
) -> None:  # Optional[codebuild.BuildInfo]:
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
        "-it",
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
        "INITIATOR=local_user",
        "-e",
        f"REPORTS={local_deploy_path}/logs",
    ]

    for key, value in os.environ.items():
        if key.startswith("AWS_"):
            env_current = ["-e", f"{key}={value}"]
            docker_command.extend(env_current)

    docker_command.append("public.ecr.aws/codebuild/local-builds:latest")

    try:
        subprocess.run(docker_command, check=True)
    except KeyboardInterrupt:
        print("\nInterrupted by user.")
