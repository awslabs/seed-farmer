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
from typing import Any, Dict, Optional

import yaml

import seedfarmer.mgmt.bundle as bundle


def run(
    local_deploy_path: str,
    bundle_zip: str,
    buildspec: Dict[str, Any],
    env_vars: Dict[str, str],
    codebuild_image: Optional[str],
) -> None:  # Optional[codebuild.BuildInfo]:
    # write the buildspec to file
    def write_it(filename: str, content) -> None:  # type: ignore[no-untyped-def]
        with open(filename, "w") as buildspec:
            buildspec.write(yaml.dump(content, indent=4))

    write_it(os.path.join(local_deploy_path, "buildspec.yaml"), buildspec)

    # Write the environment variables to the file
    env_vars_path = os.path.join(local_deploy_path, "diw.env")
    with open(env_vars_path, "w") as f:
        for key, value in env_vars.items():
            f.write(f"{key}={value}\n")

    ## Extract the zip to the local root so it is mounted by the container
    bundle.extract_zip(bundle_zip, local_deploy_path)

    codebuild_image = (
        codebuild_image if codebuild_image else "public.ecr.aws/codebuild/amazonlinux2-x86_64-standard:5.0"
    )

    # docker_command = f"""docker run -it -v /var/run/docker.sock:/var/run/docker.sock \
    # -e "IMAGE_NAME=public.ecr.aws/codebuild/amazonlinux2-x86_64-standard:4.0" \
    # -e "ARTIFACTS={local_deploy_path}/artifacts" \
    # -e "SOURCE={local_deploy_path}/" \
    # -e "BUILDSPEC={local_deploy_path}/buildspec.yaml" \
    # -v "{local_deploy_path}/:/LocalBuild/envFile/" \
    # -e "ENV_VAR_FILE=diw.env" \
    # -e "AWS_CONFIGURATION=/home/dgraeber/.aws" \
    # -e "AWS_EC2_METADATA_DISABLED=true" \
    # -e "MOUNT_SOURCE_DIRECTORY=TRUE" \
    # -e "INITIATOR=dgraeber" \
    # public.ecr.aws/codebuild/local-builds:latest"""

    # print(docker_command)
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
        f"BUILDSPEC={local_deploy_path}/buildspec.yaml",
        "-v",
        f"{local_deploy_path}/:/LocalBuild/envFile/",
        "-e",
        "ENV_VAR_FILE=diw.env",
        "-e",
        f"AWS_CONFIGURATION={os.environ.get('HOME')}/.aws",
        "-e",
        "AWS_EC2_METADATA_DISABLED=true",
        "-e",
        "MOUNT_SOURCE_DIRECTORY=TRUE",
        "-e",
        "INITIATOR=dgraeber",
        "-e",
        f"REPORTS={local_deploy_path}/logs",
    ]

    for key, value in os.environ.items():
        if key.startswith("AWS_"):
            env_current = ["-e", f"{key}={value}"]
            docker_command.extend(env_current)

    docker_command.append("public.ecr.aws/codebuild/local-builds:latest")

    # "-v", f"{local_deploy_path}/logs:/tmp/codebuild/logs",
    print(" ")
    print(" ")
    print(" ".join(docker_command))
    print(" ")
    print(" ")

    try:
        subprocess.run(docker_command, check=True)
    except KeyboardInterrupt:
        print("\nInterrupted by user.")

    # buildImage = "public.ecr.aws/codebuild/amazonlinux2-x86_64-standard:4.0"

    # docker_script_command = [
    #     "./codebuild_build.sh","-i",f"{buildImage}",
    #         "-a","artifacts",
    #         "-s",f"/home/dgraeber/workplace/seed-group/testing-frameworks/zzz-codeseeder-testing/{local_deploy_path}",
    #         "-r","logs",
    #         "-c",
    #         "-b",f"./buildspec.yaml",
    #         "-m",
    #         "-e",f"./diw.env"
    # ]

    # print(" ")
    # print(" ")
    # print(" ".join(docker_script_command))
    # print(" ")
    # print(" ")

    return None
