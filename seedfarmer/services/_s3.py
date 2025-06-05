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

import concurrent.futures
import logging
import math
import random
import time
from itertools import repeat
from typing import Any, Callable, Dict, List, Optional, TypeVar, Union, cast

from boto3 import Session
from botocore.exceptions import ClientError

from seedfarmer.services._service_utils import boto3_client, boto3_resource

_logger: logging.Logger = logging.getLogger(__name__)

ChunkifyItemType = TypeVar("ChunkifyItemType")


def _chunkify(
    lst: List[ChunkifyItemType], num_chunks: int = 1, max_length: Optional[int] = None
) -> List[List[ChunkifyItemType]]:
    chunk_size: int = int(math.ceil(float(len(lst)) / float(num_chunks))) if max_length is None else max_length
    return [lst[i : i + chunk_size] for i in range(0, len(lst), chunk_size)]


def _delete_objects(
    bucket: str, chunk: List[Dict[str, str]], session: Optional[Union[Callable[[], Session], Session]] = None
) -> None:
    client_s3 = boto3_client("s3", session=session)
    try:
        client_s3.delete_objects(Bucket=bucket, Delete={"Objects": chunk})  # type: ignore[typeddict-item]
    except client_s3.exceptions.ClientError as ex:
        if "SlowDown" in str(ex):
            time.sleep(random.randint(3, 10))
            client_s3.delete_objects(Bucket=bucket, Delete={"Objects": chunk})  # type: ignore[typeddict-item]


def list_keys(bucket: str, session: Optional[Union[Callable[[], Session], Session]] = None) -> List[Dict[str, str]]:
    """List the keys/objects in an S3 Buket

    Parameters
    ----------
    bucket : str
        S3 Bucket name
    session: Optional[Union[Callable[[], Session], Session]], optional
        Optional Session or function returning a Session to use for all boto3 operations, by default None

    Returns
    -------
    List[Dict[str, str]]
        List of Keys and VersionIds
    """
    client_s3 = boto3_client("s3", session=session)
    paginator = client_s3.get_paginator("list_object_versions")
    response_iterator = paginator.paginate(Bucket=bucket, PaginationConfig={"PageSize": 1_000})
    keys: List[Dict[str, str]] = []
    for page in response_iterator:
        if "DeleteMarkers" in page:
            for delete_marker in page["DeleteMarkers"]:
                keys.append(
                    {
                        "Key": delete_marker["Key"],
                        "VersionId": delete_marker["VersionId"],
                    }
                )
        if "Versions" in page:
            for version in page["Versions"]:
                keys.append({"Key": version["Key"], "VersionId": version["VersionId"]})
    return keys


def delete_objects(
    bucket: str, keys: Optional[List[str]] = None, session: Optional[Union[Callable[[], Session], Session]] = None
) -> None:
    """Delete objects from an S3 Bucket

    Parameters
    ----------
    bucket : str
        S3 Bucket name
    keys : Optional[List[str]], optional
        List of keys to delete, all if None, by default None
    session: Optional[Union[Callable[[], Session], Session]], optional
        Optional Session or function returning a Session to use for all boto3 operations, by default None
    """
    if keys is None:
        keys_pairs: List[Dict[str, str]] = list_keys(bucket=bucket, session=session)
    else:
        keys_pairs = [{"Key": k} for k in keys]
    if keys_pairs:
        chunks: List[List[Dict[str, str]]] = _chunkify(lst=keys_pairs, max_length=1_000)
        with concurrent.futures.ThreadPoolExecutor(max_workers=len(chunks)) as executor:
            list(executor.map(_delete_objects, repeat(bucket), chunks, repeat(session)))


def delete_bucket(bucket: str, session: Optional[Union[Callable[[], Session], Session]] = None) -> None:
    """Delete an S3 Bucket

    Parameters
    ----------
    bucket : str
        S3 Bucket Name
    session: Optional[Union[Callable[[], Session], Session]], optional
        Optional Session or function returning a Session to use for all boto3 operations, by default None

    Raises
    ------
    ex
        If error other that NoSuchBucket
    """
    client_s3 = boto3_client("s3", session=session)
    try:
        _logger.debug("Cleaning up bucket: %s", bucket)
        delete_objects(bucket=bucket, session=session)
        _logger.debug("Deleting bucket: %s", bucket)
        client_s3.delete_bucket(Bucket=bucket)
    except Exception as ex:
        if "NoSuchBucket" in str(ex):
            _logger.debug(f"Bucket ({bucket}) does not exist, skipping")
            return
        else:
            raise ex


def upload_file(
    src: str, bucket: str, key: str, session: Optional[Union[Callable[[], Session], Session]] = None
) -> None:
    """Upload file to S3 Bucket

    Parameters
    ----------
    src : str
        Local source file
    bucket : str
        S3 Bucket
    key : str
        Key name to upload to
    session: Optional[Union[Callable[[], Session], Session]], optional
        Optional Session or function returning a Session to use for all boto3 operations, by default None
    """
    client_s3 = boto3_client("s3", session=session)
    client_s3.upload_file(Filename=src, Bucket=bucket, Key=key)


def list_s3_objects(
    bucket: str, prefix: str, session: Optional[Union[Callable[[], Session], Session]] = None
) -> Dict[str, Any]:
    """List S3 objects in a Bucket filtered to a prefix

    Parameters
    ----------
    bucket : str
        S3 Bucket name
    prefix : str
        Prefix filter
    session: Optional[Union[Callable[[], Session], Session]], optional
        Optional Session or function returning a Session to use for all boto3 operations, by default None

    Returns
    -------
    Dict[str, Any]
        List of objects
    """
    client_s3 = boto3_client("s3", session=session)
    response = client_s3.list_objects_v2(Bucket=bucket, Prefix=prefix)
    return cast(Dict[str, Any], response)


def delete_bucket_by_prefix(prefix: str, session: Optional[Union[Callable[[], Session], Session]] = None) -> None:
    """Delete S3 Buckets whose name begins with a prefix

    Parameters
    ----------
    prefix : str
        Prefix to filter Buckets by
    session: Optional[Union[Callable[[], Session], Session]], optional
        Optional Session or function returning a Session to use for all boto3 operations, by default None
    """
    client_s3 = boto3_client("s3", session=session)
    for bucket in client_s3.list_buckets()["Buckets"]:
        if bucket["Name"].startswith(prefix):
            delete_bucket(bucket=bucket["Name"], session=session)


def object_exists(bucket: str, key: str, session: Optional[Union[Callable[[], Session], Session]] = None) -> bool:
    """Check for existence of an object in an S3 Bucket

    Parameters
    ----------
    bucket : str
        S3 Bucket name
    key : str
        Key to ckeck
    session: Optional[Union[Callable[[], Session], Session]], optional
        Optional Session or function returning a Session to use for all boto3 operations, by default None

    Returns
    -------
    bool
        Indicator of object existence
    """
    try:
        boto3_resource("s3", session=session).Object(bucket, key).load()  # type: ignore [attr-defined]
    except ClientError as e:
        if e.response["Error"]["Code"] == "404":
            return False
        else:
            raise
    else:
        return True


def copy_s3_object(
    src_bucket: str,
    src_key: str,
    dest_bucket: str,
    dest_key: str,
    session: Optional[Union[Callable[[], Session], Session]] = None,
) -> None:
    """Copy an S3 Object to another bucket

    Parameters
    ----------
    src_bucket : str
        Source S3 Bucket
    src_key : str
        Source Key
    dest_bucket : str
        Destination S3 Bucket
    dest_key : str
        Destination Key
    session: Optional[Union[Callable[[], Session], Session]], optional
        Optional Session or function returning a Session to use for all boto3 operations, by default None
    """
    client_s3 = boto3_client("s3", session=session)
    client_s3.copy_object(Bucket=dest_bucket, Key=dest_key, CopySource=f"{src_bucket}/{src_key}")


def is_bucket_empty(bucket: str, folder: str, session: Optional[Union[Callable[[], Session], Session]] = None) -> bool:
    """
    Checks if there is any file in a specified folder within an S3 bucket.

    Parameters:
    - bucket: The name of the S3 bucket.
    - folder: The name of the folder inside the bucket.

    Returns:
    - False if the folder contains files, True otherwise.
    """
    if not folder.endswith("/"):
        folder += "/"
    client_s3 = boto3_client("s3", session=session)

    try:
        response = client_s3.list_objects_v2(Bucket=bucket, Prefix=folder)
        if "KeyCount" in response and response["KeyCount"] > 0:
            _logger.debug(f"Found {response['KeyCount']} objects under {folder}")
            return False
        else:
            return True
    except Exception as e:
        _logger.warn(f"Bucket ({bucket} - {e}) failed when looking for object count, have to assume there are objects")
        return False
