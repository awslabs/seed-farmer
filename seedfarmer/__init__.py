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
from typing import Any, Dict, Optional, cast

import pkg_resources
import yaml
from aws_codeseeder import LOGGER, codeseeder
from aws_codeseeder.codeseeder import CodeSeederConfig

from seedfarmer.__metadata__ import __description__, __license__, __title__

_logger: logging.Logger = logging.getLogger(__name__)
__all__ = ["__description__", "__license__", "__title__"]
__version__: str = pkg_resources.get_distribution(__title__).version

DEBUG_LOGGING_FORMAT = "[%(asctime)s][%(filename)-13s:%(lineno)3d] %(message)s"
INFO_LOGGING_FORMAT = "[%(filename)-13s:%(lineno)3d] %(message)s"

CLI_ROOT = os.path.dirname(os.path.abspath(__file__))


def enable_debug(format: str) -> None:
    logging.basicConfig(level=logging.DEBUG, format=format)
    _logger.setLevel(logging.DEBUG)
    logging.getLogger("boto3").setLevel(logging.ERROR)
    logging.getLogger("botocore").setLevel(logging.ERROR)
    logging.getLogger("s3transfer").setLevel(logging.ERROR)
    logging.getLogger("urllib3").setLevel(logging.ERROR)


def enable_info(format: str) -> None:
    logging.basicConfig(level=logging.INFO, format=format)
    _logger.setLevel(logging.INFO)
    logging.getLogger("boto3").setLevel(logging.ERROR)
    logging.getLogger("botocore").setLevel(logging.ERROR)
    logging.getLogger("s3transfer").setLevel(logging.ERROR)
    logging.getLogger("urllib3").setLevel(logging.ERROR)


enable_info(INFO_LOGGING_FORMAT)


class Config(object):
    CONFIG_FILE = "seedfarmer.yaml"
    OPS_ROOT = os.getcwd()
    _PROJECT: Optional[str] = None
    _DESCRIPTION: Optional[str] = None

    def _load_config_data(self) -> None:
        count = 0
        while not os.path.exists(os.path.join(self.OPS_ROOT, self.CONFIG_FILE)):
            if count >= 4:
                _logger.error("The seedfarmer.yaml was not found at the root of your project. Please set it and rerun.")
                raise FileNotFoundError(
                    "The seedfarmer.yaml was not found at the root of your project. Please set it and rerun."
                )
            else:
                self.OPS_ROOT = pathlib.Path(self.OPS_ROOT).parent  # type: ignore
                count += 1

        with open(os.path.join(self.OPS_ROOT, self.CONFIG_FILE), "r") as file:
            config_data: Dict[str, Any] = yaml.safe_load(file)
            self._PROJECT = config_data["project"]
            self._DESCRIPTION = config_data["description"] if "description" in config_data else "NEW PROJECT"

        @codeseeder.configure(cast(str, self._PROJECT).lower(), deploy_if_not_exists=True)
        def configure(configuration: CodeSeederConfig) -> None:
            LOGGER.debug(f"OPS ROOT (OPS_ROOT) is {self.OPS_ROOT}")
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

    @property
    def PROJECT(self) -> str:
        if self._PROJECT is None:
            self._load_config_data()
        return str(self._PROJECT)

    @property
    def DESCRIPTION(self) -> str:
        if self._DESCRIPTION is None:
            self._load_config_data()
        return str(self._DESCRIPTION)


config = Config()
