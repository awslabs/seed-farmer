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
from typing import Optional

from boto3 import Session

import seedfarmer.services._s3 as s3
from seedfarmer import config

_logger: logging.Logger = logging.getLogger(__name__)


BUNDLE_PREFIX = "bundle"


class BundleS3Support:
    seedkit_bucket: Optional[str] = None  # NEEDED This is for the seedkit along with seedfarmer_bucket
    seedkit_key: Optional[str] = None  # NEEDED This is for the seedkit along wih seedfarmer_bucket
    seedfarmer_bucket: Optional[str] = None
    seedfarmer_key: Optional[str] = None

    def __init__(
        self, deployment: str, group: str, module: str, bucket: str, bundle_src_path: Optional[str] = None
    ) -> None:
        self.project = config.PROJECT
        self.ops_root_path = config.OPS_ROOT
        self.seedfarmer_bucket = bucket
        self.seedfarmer_key = f"{BUNDLE_PREFIX}/{deployment}/{group}/{module}/bundle.zip"

        if bundle_src_path is not None:
            o = bundle_src_path.split("/", 1)
            self.seedkit_bucket = o[0]
            self.seedkit_key = o[1]


def copy_bundle_to_sf(
    deployment: str, group: str, module: str, bucket: str, bundle_src_path: str, session: Optional[Session] = None
) -> None:
    bundle = BundleS3Support(
        deployment=deployment, group=group, module=module, bucket=bucket, bundle_src_path=bundle_src_path
    )
    try:
        s3.copy_s3_object(
            src_bucket=str(bundle.seedkit_bucket),
            src_key=str(bundle.seedkit_key),
            dest_bucket=str(bundle.seedfarmer_bucket),
            dest_key=str(bundle.seedfarmer_key),
            session=session,
        )
    except Exception as e:
        _logger.info("Cannot copy the bundle to S3 - %s", e)


def get_bundle_sf_path(
    deployment: str,
    group: str,
    module: str,
    bucket: str,
) -> str:
    bundle = BundleS3Support(deployment=deployment, group=group, module=module, bucket=bucket)
    return f"s3://{bundle.seedfarmer_bucket}/{bundle.seedfarmer_key}"


def delete_bundle_from_sf(
    deployment: str,
    group: str,
    module: str,
    bucket: str,
    session: Optional[Session] = None,
) -> None:
    bundle = BundleS3Support(deployment=deployment, group=group, module=module, bucket=bucket)
    try:
        s3.delete_objects(bucket=str(bundle.seedfarmer_bucket), keys=[str(bundle.seedfarmer_key)], session=session)
    except Exception as e:
        _logger.info("Cannot delete the bundle from S3 - %s", e)


def check_bundle_exists_in_sf(
    deployment: str,
    group: str,
    module: str,
    bucket: str,
    session: Optional[Session] = None,
) -> bool:
    bundle = BundleS3Support(deployment=deployment, group=group, module=module, bucket=bucket)
    try:
        return bool(
            s3.object_exists(bucket=str(bundle.seedfarmer_bucket), key=str(bundle.seedfarmer_key), session=session)
        )
    except Exception as e:
        _logger.info("Cannot check if the bundle exists in S3 - %s", e)
        return False
