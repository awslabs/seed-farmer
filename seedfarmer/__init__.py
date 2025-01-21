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
from packaging.version import parse

import seedfarmer.errors
from seedfarmer.__metadata__ import __description__, __license__, __title__
from seedfarmer.models import ProjectSpec

_logger: logging.Logger = logging.getLogger(__name__)
__all__ = ["__description__", "__license__", "__title__"]
__version__: str = pkg_resources.get_distribution(__title__).version

DEBUG_LOGGING_FORMAT = "[%(asctime)s][%(filename)-13s:%(lineno)3d] %(message)s"
INFO_LOGGING_FORMAT = "[%(asctime)s | %(levelname)s | %(filename)-13s:%(lineno)3d | %(threadName)s ] %(message)s"

CLI_ROOT = os.path.dirname(os.path.abspath(__file__))
DEFAULT_PROJECT_POLICY_PATH = "resources/projectpolicy.yaml"
S3_BUCKET_CFN_PATH = "resources/s3_bucket.yaml"


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
    _OPS_ROOT: Optional[str] = None

    _project_spec: Optional[ProjectSpec] = None

    def _load_config_data(self) -> None:
        count = 0
        self._OPS_ROOT = os.getcwd()
        while not os.path.exists(os.path.join(self._OPS_ROOT, self.CONFIG_FILE)):
            if count >= 4:
                _logger.error("The seedfarmer.yaml was not found at the root of your project. Please set it and rerun.")
                raise seedfarmer.errors.SeedFarmerException(
                    "The seedfarmer.yaml was not found at the root of your project. Please set it and rerun."
                )
            else:
                self._OPS_ROOT = pathlib.Path(self._OPS_ROOT).parent  # type: ignore
                count += 1

        with open(os.path.join(self._OPS_ROOT, self.CONFIG_FILE), "r") as file:
            config_data: Dict[str, Any] = yaml.safe_load(file)
            self._project_spec = ProjectSpec(**config_data)

            self._project_spec.description = (
                "NEW PROJECT" if self._project_spec.description is None else self._project_spec.description
            )
            self._project_spec.project_policy_path = (
                os.path.join(self._OPS_ROOT, self._project_spec.project_policy_path)
                if self._project_spec.project_policy_path
                else os.path.join(CLI_ROOT, DEFAULT_PROJECT_POLICY_PATH)
            )
            if self._project_spec.seedfarmer_version:
                if parse(__version__) < parse(str(self._project_spec.seedfarmer_version)):
                    msg = (
                        f"The seedfarmer.yaml specified a minimum version: "
                        f"{self._project_spec.seedfarmer_version} but you are using {__version__}"
                    )
                    raise seedfarmer.errors.SeedFarmerException(msg)

        @codeseeder.configure(self._project_spec.project.lower(), deploy_if_not_exists=True)
        def configure(configuration: CodeSeederConfig) -> None:
            LOGGER.debug(f"OPS ROOT (OPS_ROOT) is {self.OPS_ROOT}")
            configuration.timeout = 120
            # Below is needed for Docker in Docker scenario on Ubuntu images
            configuration.pre_build_commands = [
                (
                    "nohup /usr/local/bin/dockerd --host=unix:///var/run/docker.sock"
                    " --host=tcp://127.0.0.1:2375 --storage-driver=overlay2 &"
                ),
                'timeout 15 sh -c "until docker info; do echo .; sleep 1; done"',
            ]
            configuration.pythonpipx_modules = [f"seed-farmer=={__version__}"]

    @property
    def PROJECT(self) -> str:
        if self._project_spec is None:
            self._load_config_data()
        return str(cast(ProjectSpec, self._project_spec).project)

    @property
    def DESCRIPTION(self) -> str:
        if self._project_spec is None:
            self._load_config_data()
        return str(cast(ProjectSpec, self._project_spec).description)

    @property
    def OPS_ROOT(self) -> str:
        if self._project_spec is None:
            self._load_config_data()
        return str(self._OPS_ROOT)

    @property
    def PROJECT_POLICY_PATH(self) -> str:
        if self._project_spec is None:
            self._load_config_data()
        return str(cast(ProjectSpec, self._project_spec).project_policy_path)

    @property
    def MANIFEST_VALIDATION_FAIL_ON_UNKNOWN_FIELDS(self) -> bool:
        if self._project_spec is None:
            self._load_config_data()
        return cast(ProjectSpec, self._project_spec).manifest_validation_fail_on_unknown_fields

    @property
    def BUCKET_STORAGE_PATH(self) -> str:
        if self._project_spec is None:
            self._load_config_data()
        return str(os.path.join(CLI_ROOT, S3_BUCKET_CFN_PATH))


config = Config()
