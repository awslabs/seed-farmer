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

import mock_data.mock_build_info as mock_build_info
import pytest
from moto import mock_aws

import seedfarmer.mgmt.build_info as bi
from seedfarmer.services._service_utils import boto3_client
from seedfarmer.services.session_manager import SessionManager

_logger: logging.Logger = logging.getLogger(__name__)


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
    with mock_aws():
        yield boto3_client(service_name="sts", session=None)


@pytest.fixture(scope="function")
def session_manager(sts_client):
    SessionManager._instances = {}
    SessionManager().get_or_create(
        project_name="test",
        region_name="us-east-1",
        toolchain_region="us-east-1",
        enable_reaper=False,
    )


@pytest.mark.mgmt
@pytest.mark.mgmt_build_info
def test_get_build_params(mocker):
    mocker.patch("seedfarmer.mgmt.build_info.codebuild.get_build_data", return_value=mock_build_info.codebuild_response)
    build_id = "codeseeder-idf:7f53415b-f47d-4e5e-860f-93d7f440aa30"
    env_params = bi.get_build_env_params(build_ids=[build_id])  # [Dict[str, Any]
    assert "SEEDFARMER_HASH" in env_params.keys()
    assert "SEEDFARMER_PROJECT_NAME" in env_params.keys()


@pytest.mark.mgmt
@pytest.mark.mgmt_build_info
def test_validate_group_parameters():
    bi.get_manifest_schema(type="deployment")
