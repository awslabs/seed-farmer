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
import pathlib

from typing import Any, Dict

import yaml

from aws_codeseeder import LOGGER, codeseeder
from aws_codeseeder.codeseeder import CodeSeederConfig

from seedfarmer import __version__

_logger: logging.Logger = logging.getLogger(__name__)

CONFIG_FILE = "seedfarmer.yaml"
OPS_ROOT = os.getcwd()
PROJECT = ""
DESCRIPTION = ""

def _load_config_data() -> None:
    count = 0
    global CONFIG_FILE
    global OPS_ROOT
    global PROJECT
    global DESCRIPTION

    while not os.path.exists(os.path.join(OPS_ROOT, CONFIG_FILE)):
        if count >= 4:
            _logger.error("The seedfarmer.yaml was not found at the root of your project.  Please set it and rerun.")
            raise FileNotFoundError("The seedfarmer.yaml was not found at the root of your project.  Please set it and rerun.")
        else:
            OPS_ROOT = pathlib.Path(OPS_ROOT).parent  # type: ignore
            count += 1

    with open(os.path.join(OPS_ROOT, CONFIG_FILE), "r") as file:
        config_data: Dict[str, Any] = yaml.safe_load(file)
        PROJECT = config_data["project"]
        DESCRIPTION = config_data["description"] if "description" in config_data else "NEW PROJECT"

_load_config_data()

@codeseeder.configure(PROJECT.lower(), deploy_if_not_exists=True)
def configure(configuration: CodeSeederConfig) -> None:
    LOGGER.debug(f"OPS ROOT (OPS_ROOT) is {OPS_ROOT}")
    configuration.timeout = 120
    configuration.codebuild_image = "public.ecr.aws/v3o4w1g6/aws-codeseeder/code-build-base:2.2.0"
    configuration.pre_build_commands = [
        (
            "nohup /usr/local/bin/dockerd --host=unix:///var/run/docker.sock"
            " --host=tcp://127.0.0.1:2375 --storage-driver=overlay2 &"
        ),
        'timeout 15 sh -c "until docker info; do echo .; sleep 1; done"',
    ]
    configuration.python_modules = [f"seed-farmer=={__version__}"]
    configuration.runtime_versions = {"nodejs": "14", "python": "3.9"}
