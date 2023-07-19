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

from seedfarmer.services._service_utils import (
    boto3_client,
    boto3_resource,
    create_new_session,
    create_new_session_with_creds,
    get_botocore_config,
    get_region,
    get_sts_identity_info,
)

__all__ = [
    "get_botocore_config",
    "get_account_id",
    "get_region",
    "boto3_client",
    "boto3_resource",
    "create_new_session",
    "create_new_session_with_creds",
    "get_sts_identity_info",
]
