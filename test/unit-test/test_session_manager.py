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

import os

import pytest
from moto import mock_sts

from seedfarmer.services._service_utils import boto3_client
from seedfarmer.services.session_manager import SessionManager


@pytest.fixture(scope="function")
def session_manager():
    SessionManager._instances = {}


@pytest.fixture(scope="function")
def aws_credentials():
    """Mocked AWS Credentials for moto."""
    os.environ["AWS_ACCESS_KEY_ID"] = "testing"
    os.environ["AWS_SECRET_ACCESS_KEY"] = "testing"
    os.environ["AWS_SECURITY_TOKEN"] = "testing"
    os.environ["AWS_SESSION_TOKEN"] = "testing"
    os.environ["AWS_DEFAULT_REGION"] = "us-east-1"
    os.environ["MOTO_ACCOUNT_ID"] = "123456789012"


@pytest.fixture(scope="function")
def sts_client(aws_credentials):
    with mock_sts():
        yield boto3_client(service_name="sts", session=None)


@pytest.mark.session_manager
def test_failed_creation(session_manager):
    with pytest.raises(ValueError) as e:
        SessionManager().get_or_create()
    assert "A 'project_name' is required for first time initialization of the SessionManager" in str(e)


@pytest.mark.session_manager
def test_singleton(session_manager, sts_client):
    session_manager_1 = SessionManager().get_or_create(
        project_name="test",
        region_name="us-east-1",
        toolchain_region="us-east-1",
        reaper_interval=3,
        enable_reaper=True,
    )
    session_manager_2 = SessionManager().get_or_create()
    assert session_manager_1 == session_manager_2
    assert session_manager_1.toolchain_session == session_manager_2.toolchain_session


@pytest.mark.session_manager
def test_deployment_session(session_manager, sts_client):
    SessionManager().get_or_create(project_name="test").get_deployment_session(account_id="111111111111", region_name="us-east-1")
