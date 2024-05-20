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
from moto import mock_sts

import seedfarmer.mgmt.git_support as sf_git
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
    with mock_sts():
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
@pytest.mark.mgmt_git_support
def test_clone_module_repo_branch(mocker):
    git_path_test = "git::https://github.com/awslabs/idf-modules.git//modules/network/basic-cdk/?ref=release/1.1.0"
    git_path_test_redo = "git::https://github.com/awslabs/idf-modules.git//modules/dummy/blank?ref=release/1.1.0"

    sf_git_dir, module_path, commit_hash = sf_git.clone_module_repo(git_path=git_path_test)
    # Make sure the pull works on an existing repo
    sf_git_dir, module_path, commit_hash = sf_git.clone_module_repo(git_path=git_path_test_redo)


@pytest.mark.mgmt
@pytest.mark.mgmt_git_support
def test_clone_module_repo_tag(mocker):
    git_path_test = "git::https://github.com/awslabs/idf-modules.git//modules/network/basic-cdk/?ref=v1.1.0"
    git_path_test_redo = "git::https://github.com/awslabs/idf-modules.git//modules/dummy/blank?depth=1"

    sf_git_dir, module_path, commit_hash = sf_git.clone_module_repo(git_path=git_path_test)
    # Make sure the pull works on an existing repo
    sf_git_dir, module_path, commit_hash = sf_git.clone_module_repo(git_path=git_path_test_redo)


@pytest.mark.mgmt
@pytest.mark.mgmt_git_support
def test_clone_module_repo_commit(mocker):
    git_path_test = "git::https://github.com/awslabs/idf-modules.git//modules/replication/dockerimage-replication?ref=a190c5c93e84c34c9af070eb59c2e7b65f973afd"
    git_path_test_redo = "git::https://github.com/awslabs/idf-modules.git//modules/replication/dockerimage-replication?ref=a190c5c93e84c34c9af070eb59c2e7b65f973afd"

    sf_git_dir, module_path, commit_hash = sf_git.clone_module_repo(git_path=git_path_test)
    # Make sure the pull works on an existing repo
    sf_git_dir, module_path, commit_hash = sf_git.clone_module_repo(git_path=git_path_test_redo)


@pytest.mark.mgmt
@pytest.mark.mgmt_git_support
def test_clone_module_repo_main(mocker):
    git_path_test = "git::https://github.com/awslabs/idf-modules.git//modules/dummy/blank?depth=1"
    git_path_test_redo = "git::https://github.com/awslabs/idf-modules.git//modules/network/basic-cdk?depth=1"

    sf_git_dir, module_path, commit_hash = sf_git.clone_module_repo(git_path=git_path_test)
    # Make sure the pull works on an existing repo
    sf_git_dir, module_path, commit_hash = sf_git.clone_module_repo(git_path=git_path_test_redo)
