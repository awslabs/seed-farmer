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

import pytest
from moto import mock_aws

import seedfarmer.mgmt.archive_support as archive
from seedfarmer.services._service_utils import boto3_client
from seedfarmer.services.session_manager import SessionManager
import shutil


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
@pytest.mark.mgmt_archive_support
def test_fetch_module_repo_dns_path(mocker):
    shutil.rmtree(archive.parent_dir) if os.path.exists(archive.parent_dir) else None
    archive_path_test = "archive::https://github.com/awslabs/idf-modules/archive/refs/tags/v1.6.0.tar.gz?module=modules/dummy/blank"

    archive_dir, module_path = archive.fetch_module_repo(release_path=archive_path_test)
    # test it again...we shouldn't be re-downloading
    archive_dir, module_path = archive.fetch_module_repo(release_path=archive_path_test)

@pytest.mark.mgmt
@pytest.mark.mgmt_archive_support
def test_fetch_module_repo_dns_path_zip(mocker):
    shutil.rmtree(archive.parent_dir) if os.path.exists(archive.parent_dir) else None
    archive_path_test = "archive::https://github.com/awslabs/idf-modules/archive/refs/tags/v1.6.0.zip?module=modules/dummy/blank"
    archive_dir, module_path = archive.fetch_module_repo(release_path=archive_path_test)
    # test it again...we shouldn't be re-downloading
    archive_dir, module_path = archive.fetch_module_repo(release_path=archive_path_test)



@pytest.mark.mgmt
@pytest.mark.mgmt_archive_support
def test_fetch_module_repo_dns_path_missing_module(mocker):
    from seedfarmer.errors import InvalidConfigurationError
    shutil.rmtree(archive.parent_dir) if os.path.exists(archive.parent_dir) else None
    archive_path_test = "archive::https://github.com/awslabs/idf-modules/archive/refs/tags/v1.6.0.tar.gz"
    with pytest.raises(InvalidConfigurationError):
        archive_dir, module_path = archive.fetch_module_repo(release_path=archive_path_test)
        
@pytest.mark.mgmt
@pytest.mark.mgmt_archive_support
def test_fetch_module_repo_dns_path_missing_https(mocker):
    from seedfarmer.errors import InvalidConfigurationError
    shutil.rmtree(archive.parent_dir) if os.path.exists(archive.parent_dir) else None
    archive_path_test = "archive::http://github.com/awslabs/idf-modules/archive/refs/tags/v1.6.0.tar.gz?module=modules/dummy/blank"
    with pytest.raises(InvalidConfigurationError):
        archive_dir, module_path = archive.fetch_module_repo(release_path=archive_path_test)


@pytest.mark.mgmt
@pytest.mark.mgmt_archive_support
def test_fetch_module_repo_dns_path_missing_archive(mocker):
    from seedfarmer.errors import InvalidConfigurationError
    shutil.rmtree(archive.parent_dir) if os.path.exists(archive.parent_dir) else None
    archive_path_test = "archive::http://github.com/awslabs/idf-modules/archive/refs/tags/v1.6.1.tar.gz?module=modules/dummy/blank"
    with pytest.raises(InvalidConfigurationError):
        archive_dir, module_path = archive.fetch_module_repo(release_path=archive_path_test)
        
