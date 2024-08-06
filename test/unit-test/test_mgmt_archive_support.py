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

import io
import json
import logging
import os
import shutil
import tarfile
import zipfile
from typing import Tuple
from unittest.mock import MagicMock, patch

import boto3
import pytest
from moto import mock_aws

import seedfarmer.mgmt.archive_support as archive
from seedfarmer.errors.seedfarmer_errors import InvalidConfigurationError
from seedfarmer.services._service_utils import boto3_client
from seedfarmer.services.session_manager import SessionManager

_logger: logging.Logger = logging.getLogger(__name__)


@pytest.fixture(scope="function")
def aws_credentials():
    with patch.dict(os.environ, {}, clear=True):
        """Mocked AWS Credentials for moto."""
        os.environ["AWS_ACCESS_KEY_ID"] = "testing"
        os.environ["AWS_SECRET_ACCESS_KEY"] = "testing"
        os.environ["AWS_SECURITY_TOKEN"] = "testing"
        os.environ["AWS_SESSION_TOKEN"] = "testing"
        os.environ["AWS_DEFAULT_REGION"] = "us-east-1"
        os.environ["MOTO_ACCOUNT_ID"] = "123456789012"

        yield None


@pytest.fixture(scope="function")
def sts_client(aws_credentials):
    with mock_aws():
        yield boto3_client(service_name="sts", session=None)


@pytest.fixture(scope="function")
def secretsmanager_client(aws_credentials):
    with mock_aws():
        yield boto3_client(service_name="secretsmanager", session=None)


@pytest.fixture(scope="function")
def session_manager(sts_client):
    SessionManager._instances = {}
    SessionManager().get_or_create(
        project_name="test",
        region_name="us-east-1",
        toolchain_region="us-east-1",
        enable_reaper=False,
    )


example_archive_files = [
    ("modules/test-module/modulestack.yaml", io.BytesIO(b"111")),
    ("modules/test-module/pyproject.toml", io.BytesIO(b"222")),
    ("README.md", io.BytesIO(b"333")),
    ("LICENSE", io.BytesIO(b"444")),
]


@pytest.fixture(scope="function")
def zip_file_data() -> Tuple[bytes, str]:
    zip_buffer = io.BytesIO()

    with zipfile.ZipFile(zip_buffer, "a", zipfile.ZIP_DEFLATED) as zip_file:
        for file_name, data in example_archive_files:
            zip_file.writestr(file_name, data.getvalue())

    return zip_buffer.getvalue(), "zip"


@pytest.fixture(scope="function")
def tar_file_data() -> Tuple[bytes, str]:
    tar_buffer = io.BytesIO()

    with tarfile.open(fileobj=tar_buffer, mode="w:gz") as tar_file:
        for file_name, data in example_archive_files:
            tar_file.addfile(tarfile.TarInfo(name=file_name), fileobj=data)

    return tar_buffer.getvalue(), "tar.gz"


@pytest.fixture(params=["zip_file_data", "tar_file_data"])
def archive_file_data(
    request: pytest.FixtureRequest, zip_file_data: Tuple[bytes, str], tar_file_data: Tuple[bytes, str]
) -> Tuple[bytes, str]:
    return request.getfixturevalue(request.param)


@pytest.mark.mgmt
@pytest.mark.mgmt_archive_support
def test_fetch_module_repo_dns_path():
    shutil.rmtree(archive.parent_dir) if os.path.exists(archive.parent_dir) else None
    archive_path_test = (
        "archive::https://github.com/awslabs/idf-modules/archive/refs/tags/v1.6.0.tar.gz?module=modules/dummy/blank"
    )

    archive.fetch_archived_module(release_path=archive_path_test)
    # test it again...we shouldn't be re-downloading
    archive.fetch_archived_module(release_path=archive_path_test)


@pytest.mark.mgmt
@pytest.mark.mgmt_archive_support
def test_fetch_module_repo_dns_path_zip():
    shutil.rmtree(archive.parent_dir) if os.path.exists(archive.parent_dir) else None
    archive_path_test = (
        "archive::https://github.com/awslabs/idf-modules/archive/refs/tags/v1.6.0.zip?module=modules/dummy/blank"
    )
    archive.fetch_archived_module(release_path=archive_path_test)
    # test it again...we shouldn't be re-downloading
    archive.fetch_archived_module(release_path=archive_path_test)


@pytest.mark.mgmt
@pytest.mark.mgmt_archive_support
def test_fetch_module_repo_dns_path_missing_https():
    from seedfarmer.errors import InvalidConfigurationError

    shutil.rmtree(archive.parent_dir) if os.path.exists(archive.parent_dir) else None
    archive_path_test = (
        "archive::http://github.com/awslabs/idf-modules/archive/refs/tags/v1.6.0.tar.gz?module=modules/dummy/blank"
    )
    with pytest.raises(InvalidConfigurationError):
        archive.fetch_archived_module(release_path=archive_path_test)


@pytest.mark.mgmt
@pytest.mark.mgmt_archive_support
def test_fetch_module_repo_dns_path_missing_module():
    from seedfarmer.errors import InvalidConfigurationError

    shutil.rmtree(archive.parent_dir) if os.path.exists(archive.parent_dir) else None
    archive_path_test = "archive::https://github.com/awslabs/idf-modules/archive/refs/tags/v1.6.0.tar.gz"
    with pytest.raises(InvalidConfigurationError):
        archive.fetch_archived_module(release_path=archive_path_test)


@pytest.mark.mgmt
@pytest.mark.mgmt_archive_support
def test_fetch_module_repo_dns_path_missing_archive():
    from seedfarmer.errors import InvalidConfigurationError

    shutil.rmtree(archive.parent_dir) if os.path.exists(archive.parent_dir) else None
    archive_path_test = (
        "archive::http://github.com/awslabs/idf-modules/archive/refs/tags/v1.6.1.tar.gz?module=modules/dummy/blank"
    )
    with pytest.raises(InvalidConfigurationError):
        archive.fetch_archived_module(release_path=archive_path_test)


@pytest.mark.mgmt
@pytest.mark.mgmt_archive_support
@pytest.mark.parametrize(
    "s3_bucket_http_url", ["testing-bucket.s3.amazonaws.com", "testing-bucket.s3.us-west-2.amazonaws.com"]
)
def test_fetch_module_repo_from_s3(
    session_manager: None, archive_file_data: Tuple[bytes, str], s3_bucket_http_url: str
) -> None:
    shutil.rmtree(archive.parent_dir) if os.path.exists(archive.parent_dir) else None

    archive_bytes, archive_extension = archive_file_data

    response_mock = MagicMock()
    response_mock.status_code = 200
    response_mock.content = archive_bytes

    s3_http_url = f"https://{s3_bucket_http_url}/testing-modules.{archive_extension}"
    module_name = "modules/test-module/"

    with patch("requests.get", return_value=response_mock) as mock_requests_get:
        archive_path_test = f"archive::{s3_http_url}?module={module_name}"

        archive_path, _ = archive.fetch_archived_module(release_path=archive_path_test)
        archive.fetch_archived_module(release_path=archive_path_test)

        mock_requests_get.assert_called_once()

        assert mock_requests_get.call_args.kwargs["url"] == s3_http_url

        # check that the sha256 header was added and that the request was signed
        assert "x-amz-content-sha256" in mock_requests_get.call_args.kwargs["headers"]
        assert "Authorization" in mock_requests_get.call_args.kwargs["headers"]

        # Check that the module was extracted to the correct location
        assert os.path.exists(os.path.join(archive_path, module_name, "modulestack.yaml"))


@pytest.mark.mgmt
@pytest.mark.mgmt_archive_support
@pytest.mark.parametrize(
    "s3_bucket_http_url", ["testing-bucket.s3.amazonaws.com", "testing-bucket.s3.us-west-2.amazonaws.com"]
)
def test_fetch_module_repo_from_s3_with_error(
    session_manager: None, archive_file_data: Tuple[bytes, str], s3_bucket_http_url: str
) -> None:
    shutil.rmtree(archive.parent_dir) if os.path.exists(archive.parent_dir) else None

    _, archive_extension = archive_file_data

    response_mock = MagicMock()
    response_mock.status_code = 400

    s3_http_url = f"https://{s3_bucket_http_url}/testing-modules.{archive_extension}"
    module_name = "modules/test-module/"

    with patch("requests.get", return_value=response_mock) as mock_requests_get:
        archive_path_test = f"archive::{s3_http_url}?module={module_name}"

        with pytest.raises(InvalidConfigurationError):
            archive.fetch_archived_module(release_path=archive_path_test)

        mock_requests_get.assert_called_once()


@pytest.mark.mgmt
@pytest.mark.mgmt_archive_support
def test_fetch_module_repo_from_https_with_secret(
    session_manager: None, archive_file_data: Tuple[bytes, str], secretsmanager_client: boto3.client
) -> None:
    shutil.rmtree(archive.parent_dir) if os.path.exists(archive.parent_dir) else None

    secret_name = "testing-archive-credentials-modules"
    username = "test-user"
    password = "test-password"
    secretsmanager_client.create_secret(
        Name=secret_name,
        SecretString=json.dumps(
            {
                "user": username,
                "password": password,
            },
        ),
    )

    archive_bytes, archive_extension = archive_file_data

    response_mock = MagicMock()
    response_mock.status_code = 200
    response_mock.content = archive_bytes

    https_url = f"https://www.myprivateurl.com/api/testing-modules.{archive_extension}"
    module_name = "modules/test-module/"

    with patch("requests.get", return_value=response_mock) as mock_requests_get:
        release_path = f"archive::{https_url}?module={module_name}"

        archive_path, _ = archive.fetch_archived_module(
            release_path=release_path,
            secret_name=secret_name,
        )
        archive.fetch_archived_module(release_path=release_path, secret_name=secret_name)

        mock_requests_get.assert_called_once()

        # check that the secrets manager was used
        assert mock_requests_get.call_args.kwargs["auth"].username == username
        assert mock_requests_get.call_args.kwargs["auth"].password == password

        # Check that the module was extracted to the correct location
        assert os.path.exists(os.path.join(archive_path, module_name, "modulestack.yaml"))
