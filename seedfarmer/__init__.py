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

import pkg_resources

from seedfarmer.__metadata__ import __description__, __license__, __title__

_logger: logging.Logger = logging.getLogger(__name__)
__all__ = ["__description__", "__license__", "__title__"]
__version__: str = pkg_resources.get_distribution(__title__).version

DEBUG_LOGGING_FORMAT = "[%(asctime)s][%(filename)-13s:%(lineno)3d] %(message)s"
INFO_LOGGING_FORMAT = "[%(filename)-13s:%(lineno)3d] %(message)s"


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
