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
import random
import string
from datetime import datetime, timedelta
from typing import Any, Callable, Dict, List, Optional, Union

from boto3 import Session

import seedfarmer.services._cloudwatch as cloudwatch
import seedfarmer.services._codebuild as codebuild
import seedfarmer.services._s3 as s3

_logger: logging.Logger = logging.getLogger(__name__)


def _print_codebuild_logs(
    events: List[cloudwatch.CloudWatchEvent],
    codebuild_log_callback: Optional[Callable[[str], None]] = None,
) -> None:
    for event in events:
        msg = event.message[:-1] if event.message.endswith("\n") else event.message
        _logger.debug("[CODEBUILD] %s", msg)
        if codebuild_log_callback:
            codebuild_log_callback(msg)


def _wait_execution(
    build_id: str,
    stream_name_prefix: str,
    codebuild_log_callback: Optional[Callable[[str], None]] = None,
    session: Optional[Union[Callable[[], Session], Session]] = None,
) -> Optional[codebuild.BuildInfo]:
    start_time: Optional[datetime] = None
    stream_name: Optional[str] = None
    status: Optional[codebuild.BuildInfo] = None
    for status in codebuild.wait(build_id=build_id, session=session):
        if status.logs.enabled and status.logs.group_name:
            if stream_name is None:
                stream_name = cloudwatch.get_stream_name_by_prefix(
                    group_name=status.logs.group_name, prefix=f"{stream_name_prefix}/", session=session
                )
            if stream_name is not None:
                events = cloudwatch.get_log_events(
                    group_name=status.logs.group_name, stream_name=stream_name, start_time=start_time, session=session
                )
                _print_codebuild_logs(events=events.events, codebuild_log_callback=codebuild_log_callback)
                if events.last_timestamp is not None:
                    start_time = events.last_timestamp + timedelta(milliseconds=1)
    return status


def _execute_codebuild(
    stack_outputs: Dict[str, str],
    bundle_location: str,
    execution_id: str,
    buildspec: Dict[str, Any],
    timeout: int,
    overrides: Optional[Dict[str, Any]] = None,
    codebuild_log_callback: Optional[Callable[[str], None]] = None,
    session: Optional[Union[Callable[[], Session], Session]] = None,
    yaml_dumper: Optional[Any] = None,  # Accepts ruamel.yaml.YAML instance or PyYAML dump function
) -> Optional[codebuild.BuildInfo]:
    _logger.debug("bundle_location: %s", bundle_location)
    stream_name_prefix = f"codeseeder-{execution_id}"  # (LEGACY)
    _logger.debug("stream_name_prefix: %s", stream_name_prefix)
    build_id = codebuild.start(
        project_name=stack_outputs["CodeBuildProject"],
        stream_name=stream_name_prefix,
        bundle_location=bundle_location,
        buildspec=buildspec,
        timeout=timeout,
        overrides=overrides,
        session=session,
        yaml_dumper=yaml_dumper,
    )
    return _wait_execution(
        build_id=build_id,
        stream_name_prefix=stream_name_prefix,
        codebuild_log_callback=codebuild_log_callback,
        session=session,
    )


def run(
    stack_outputs: Dict[str, str],
    bundle_path: str,
    buildspec: Dict[str, Any],
    timeout: int,
    overrides: Optional[Dict[str, Any]] = None,
    codebuild_log_callback: Optional[Callable[[str], None]] = None,
    session: Optional[Union[Callable[[], Session], Session]] = None,
    bundle_id: Optional[str] = None,
    prebuilt_bundle: Optional[str] = None,
    yaml_dumper: Optional[Any] = None,  # Accepts ruamel.yaml.YAML instance or PyYAML dump function
) -> Optional[codebuild.BuildInfo]:
    execution_id = "".join(random.choice(string.ascii_lowercase) for i in range(8))

    if prebuilt_bundle:
        prebuilt_bundle = prebuilt_bundle[5:] if prebuilt_bundle.startswith("s3://") else prebuilt_bundle
        o = prebuilt_bundle.split("/", 1)
        loc = f"{o[0]}/{o[1]}"
    else:
        key: str = (
            f"seedfarmer/{bundle_id}/{execution_id}/bundle.zip"
            if bundle_id
            else f"seedfarmer/{execution_id}/bundle.zip"
        )
        bucket = stack_outputs["Bucket"]
        s3.delete_objects(bucket=bucket, keys=[key], session=session)
        s3.upload_file(src=bundle_path, bucket=bucket, key=key, session=session)
        loc = f"{bucket}/{key}"

    build_info = _execute_codebuild(
        stack_outputs=stack_outputs,
        bundle_location=loc,
        execution_id=execution_id,
        buildspec=buildspec,
        codebuild_log_callback=codebuild_log_callback,
        timeout=timeout,
        overrides=overrides,
        session=session,
        yaml_dumper=yaml_dumper,
    )
    if not prebuilt_bundle:
        s3.delete_objects(bucket=bucket, keys=[key], session=session)
    return build_info
