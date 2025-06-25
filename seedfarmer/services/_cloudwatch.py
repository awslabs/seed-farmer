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

from datetime import datetime, timezone
from typing import Callable, List, NamedTuple, Optional, Union

from boto3 import Session

from seedfarmer.services._service_utils import boto3_client, try_it


class CloudWatchEvent(NamedTuple):
    timestamp: datetime
    message: str


class CloudWatchEvents(NamedTuple):
    group_name: str
    stream_name_prefix: str
    start_time: Optional[datetime]
    events: List[CloudWatchEvent]
    last_timestamp: Optional[datetime]


def get_stream_name_by_prefix(
    group_name: str, prefix: str, session: Optional[Union[Callable[[], Session], Session]] = None
) -> Optional[str]:
    """Get the CloudWatch Logs stream name

    Parameters
    ----------
    group_name : str
        Name of the CloudWatch Logs group
    prefix : str
        Naming prefix of the CloudWatch Logs Stream
    session: Optional[Union[Callable[[], Session], Session]], optional
        Optional Session or function returning a Session to use for all boto3 operations, by default None

    Returns
    -------
    Optional[str]
        Name of the CloudWatch Logs Stream (if found)
    """
    client = boto3_client("logs", session=session)

    response = try_it(
        f=client.describe_log_streams,
        ex=client.exceptions.ResourceNotFoundException,
        logGroupName=group_name,
        logStreamNamePrefix=prefix,
        orderBy="LogStreamName",
        descending=True,
        limit=1,
        base=5.0,
    )

    streams = response.get("logStreams", [])
    if streams:
        return str(streams[0]["logStreamName"])
    return None


def get_log_events(
    group_name: str,
    stream_name: str,
    start_time: Optional[datetime],
    session: Optional[Union[Callable[[], Session], Session]] = None,
) -> CloudWatchEvents:
    """Get CloudWatch Logs Events

    Parameters
    ----------
    group_name : str
        Name of the CloudWatch Logs group
    stream_name : str
        Name of teh CloudWatch Logs stream in the group
    start_time : Optional[datetime]
        Start time of the CloudWatch Logs Events
    session: Optional[Union[Callable[[], Session], Session]], optional
        Optional Session or function returning a Session to use for all boto3 operations, by default None

    Returns
    -------
    CloudWatchEvents
        CloudWatch Logs Events since ``start_time`` (if found)
    """
    client = boto3_client("logs", session=session)
    args = {
        "logGroupName": group_name,
        "logStreamName": stream_name,
        "startFromHead": True,
    }
    if start_time is not None:
        args["startTime"] = int(start_time.timestamp() * 1000)
    events: List[CloudWatchEvent] = []
    response = client.get_log_events(**args)  # type: ignore[arg-type]
    previous_token = None
    token = response["nextBackwardToken"]
    while response.get("events"):
        for event in response.get("events", []):
            events.append(
                CloudWatchEvent(
                    timestamp=datetime.fromtimestamp(event["timestamp"] / 1000.0, tz=timezone.utc),
                    message=str(event.get("message", "")),
                )
            )
        previous_token = token
        token = response["nextBackwardToken"]
        if token == previous_token:
            break
        args["nextToken"] = token
        response = client.get_log_events(**args)  # type: ignore[arg-type]
    events.sort(key=lambda e: e.timestamp, reverse=False)
    return CloudWatchEvents(
        group_name=group_name,
        stream_name_prefix=stream_name,
        start_time=start_time,
        events=events,
        last_timestamp=events[-1].timestamp if events else None,
    )
