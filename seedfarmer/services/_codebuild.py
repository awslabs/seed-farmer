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
from typing import Any, Dict, List, Optional, cast

from boto3 import Session

from seedfarmer.services._service_utils import boto3_client

_logger: logging.Logger = logging.getLogger(__name__)


def get_build_data(build_ids: List[str], session: Optional[Session] = None) -> Optional[Dict[str, Any]]:
    client = boto3_client(service_name="codebuild", session=session)

    try:
        return cast(Dict[str, Any], client.batch_get_builds(ids=build_ids))
    except Exception as e:
        _logger.error("An error occurred fetching the build info for %s - %s", build_ids, e)
        return None
