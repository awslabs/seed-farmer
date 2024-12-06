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

import hashlib
import logging
import os.path
import pathlib
import re
import shutil
import tarfile
from typing import Optional, Tuple
from urllib.parse import parse_qs, urlparse
from zipfile import ZipFile

import boto3
import requests
from botocore.credentials import Credentials
from requests.auth import HTTPBasicAuth
from requests.models import Response

from seedfarmer import config
from seedfarmer.errors import InvalidConfigurationError
from seedfarmer.services._secrets_manager import get_secrets_manager_value
from seedfarmer.services._service_utils import create_signed_request
from seedfarmer.services.session_manager import SessionManager

_logger: logging.Logger = logging.getLogger(__name__)


def _download_archive(archive_url: str, secret_name: Optional[str]) -> Response:
    if re.findall(r"s3\.([^\.]+\.)?amazonaws", archive_url):
        session: boto3.Session = SessionManager().get_or_create().toolchain_session
        credentials: Credentials = SessionManager().get_or_create().get_toolchain_credentials()

        signed_request = create_signed_request(
            endpoint=archive_url,
            session=session,
            credentials=credentials,
            headers={"x-amz-content-sha256": hashlib.sha256("".encode("utf-8")).hexdigest()},
        )
        return requests.get(url=signed_request.url, headers=signed_request.headers, allow_redirects=True)  # type: ignore[arg-type]

    if secret_name:
        session: boto3.Session = SessionManager().get_or_create().toolchain_session  # type: ignore[no-redef]
        secret_value = get_secrets_manager_value(secret_name, session)

        if "username" not in secret_value or "password" not in secret_value:
            raise InvalidConfigurationError(f"username and password required in secret {secret_name}")

        auth = HTTPBasicAuth(secret_value["username"], secret_value["password"])
    else:
        auth = None

    return requests.get(
        url=archive_url,
        allow_redirects=True,
        auth=auth,
    )


def _extract_archive(archive_name: str, extracted_dir_path: str) -> str:
    if archive_name.endswith(".tar.gz"):
        with tarfile.open(archive_name, "r:gz") as tar_file:
            all_members = tar_file.getmembers()
            top_level_dirs = set(member.name.split("/")[0] for member in all_members if "/" in member.name)
            if len(top_level_dirs) > 1:
                raise InvalidConfigurationError(
                    f"the archive {archive_name} can only have one directory at the root and no files"
                )
            elif len(top_level_dirs) == 1:
                embedded_dir = top_level_dirs.pop()
            else:
                embedded_dir = ""
            tar_file.extractall(extracted_dir_path, members=all_members)
    else:
        with ZipFile(archive_name, "r") as zip_file:
            all_files = zip_file.namelist()
            top_level_dirs = set(name.split("/")[0] for name in all_files if "/" in name)
            if len(top_level_dirs) > 1:
                raise InvalidConfigurationError(
                    f"the archive {archive_name} can only have one directory at the root and no files"
                )
            elif len(top_level_dirs) == 1:
                embedded_dir = top_level_dirs.pop()
            else:
                embedded_dir = ""
            for file in all_files:
                zip_file.extract(file, path=extracted_dir_path)
    return embedded_dir


def _process_archive(archive_name: str, response: Response, extracted_dir: str) -> str:
    parent_dir = os.path.join(config.OPS_ROOT, "seedfarmer.archive")
    pathlib.Path(parent_dir).mkdir(parents=True, exist_ok=True)

    with open(archive_name, "wb") as archive_file:
        archive_file.write(response.content)

    extracted_dir_path = os.path.join(parent_dir, extracted_dir)
    embedded_dir = _extract_archive(archive_name, extracted_dir_path)

    os.remove(archive_name)

    if embedded_dir:
        file_names = os.listdir(os.path.join(extracted_dir_path, embedded_dir))
        for file_name in file_names:
            shutil.move(os.path.join(extracted_dir_path, embedded_dir, file_name), extracted_dir_path)

        os.rmdir(os.path.join(extracted_dir_path, embedded_dir))

    return extracted_dir_path


def _get_release_with_link(archive_url: str, secret_name: Optional[str]) -> Tuple[str, str]:
    parent_dir = os.path.join(config.OPS_ROOT, "seedfarmer.archive")
    parsed_url = urlparse(archive_url)

    if not parsed_url.scheme == "https":
        raise InvalidConfigurationError(f"This url must be via https: {archive_url}")

    query_params = parse_qs(parsed_url.query)
    if not query_params.get("module"):
        raise InvalidConfigurationError(f"module query param required : {archive_url}")
    module = query_params["module"][0]

    archive_name = parsed_url.path.replace("/", "_")
    extracted_dir = parsed_url.path.replace(".tar.gz", "").replace(".zip", "").replace("/", "_")

    if os.path.isdir(os.path.join(parent_dir, extracted_dir)):
        return os.path.join(parent_dir, extracted_dir), module
    else:
        resp = _download_archive(
            archive_url=parsed_url._replace(fragment="", query="").geturl(),
            secret_name=secret_name,
        )

        if resp.status_code == 200:
            return _process_archive(archive_name, resp, extracted_dir), module

        else:
            _logger.error(f"Error fetching archive at {archive_url}: {resp.status_code} {resp.reason}")
            raise InvalidConfigurationError(
                f"Error fetching archive at {archive_url}: {resp.status_code} {resp.reason}"
            )


def fetch_archived_module(release_path: str, secret_name: Optional[str] = None) -> Tuple[str, str]:
    """
    Fetch an archived module from a release path. This can be a private HTTPS link.

    This function will clone the repo to the seedfarmer.archive directory
    and return the path to the cloned repo and the relative path to the module code.

    Parameters
    ----------
    release_path: str
        The path passed in to fetch. If using a ProServe provided repo, this should look like
        archive::https://github.com/awslabs/idf-modules/archive/refs/tags/v1.10.0.zip?module=modules/dummy/dummy
    secret_name: str | None
        The name of the secret to use to fetch the module repo.
        Only used if the ``release_path`` is a private HTTPS link.

    Returns
    -------
    Tuple[str,str]
        Returns a tuple that contains (in order):
            - the full path of the seedfarmer.archive where the repo was cloned to
            - the relative path to seedfarmer.archive of the module code
    """
    return _get_release_with_link(release_path.replace("archive::", ""), secret_name=secret_name)
