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
import os.path
import pathlib
import tarfile
from typing import Optional, Tuple
from urllib.parse import urlparse
from zipfile import ZipFile

import boto3
import requests
from requests.auth import HTTPBasicAuth
from requests.models import Response

from seedfarmer import config
from seedfarmer.errors import InvalidConfigurationError
from seedfarmer.services._secrets_manager import get_secrets_manager_value

_logger: logging.Logger = logging.getLogger(__name__)
parent_dir = os.path.join(config.OPS_ROOT, "seedfarmer.archive")


def _download_archive(archive_url: str, session: Optional[boto3.Session], secret_name: Optional[str]) -> Response:
    credentials = get_secrets_manager_value("secretsmanager", session) if secret_name else None

    # TODO: add a check here for an S3 HTTPS DNS, and if so, add the SigV4 Auth to the url

    if "s3.amazonaws" in archive_url:
        pass
        ## TODO - add Sigv4Auth here
        # session = SessionManager().get_or_create().toolchain_session
        # credentials = SessionManager().get_or_create().get_toolchain_credentials()
        # # GOTTA use the toolchain role - so get the toolchain session
        # active_url = create_signed_request(endpoint=active_url, session=session, credentials=credentials)
        # z = requests.get(active_url.url, headers=active_url.headers,allow_redirects=True)
    else:
        resp = requests.get(
            archive_url,
            allow_redirects=True,
            auth=HTTPBasicAuth(credentials["user"], credentials["password"]) if credentials else None,
        )

    return resp


def _extract_archive(archive_name: str) -> str:
    if archive_name.endswith(".tar.gz"):
        with tarfile.open(archive_name, "r:gz") as tar_file:
            embedded_dir = os.path.commonprefix(tar_file.getnames())
            tar_file.extractall(parent_dir)
    else:
        with ZipFile(archive_name, "r") as zip_file:
            embedded_dir = zip_file.namelist()[0]
            zip_file.extractall(parent_dir)

    return embedded_dir


def _process_archive(archive_name: str, response: Response, extracted_dir: str) -> Tuple[str, str]:
    pathlib.Path(parent_dir).mkdir(parents=True, exist_ok=True)

    with open(archive_name, "wb") as archive_file:
        archive_file.write(response.content)

    embedded_dir = _extract_archive(archive_name)

    os.rename(os.path.join(parent_dir, embedded_dir), os.path.join(parent_dir, extracted_dir))
    os.remove(archive_name)

    return parent_dir, extracted_dir


def _get_release_with_link(archive_url: str, session: Optional[boto3.Session], secret_name: Optional[str]) -> Tuple[str, str]:
    parsed_url = urlparse(archive_url)

    if not parsed_url.scheme == "https":
        raise InvalidConfigurationError("This url must be via https: %s", archive_url)

    archive_name = parsed_url.path.replace("/", "_")
    extracted_dir = parsed_url.path.replace(".tar.gz", "").replace(".zip", "").replace("/", "_")

    if os.path.isdir(os.path.join(parent_dir, extracted_dir)):
        return parent_dir, extracted_dir
    else:
        resp = _download_archive(
            archive_url=parsed_url._replace(fragment="").geturl(),
            session=session,
            secret_name=secret_name,
        )

        if resp.status_code == 200:
            return _process_archive(archive_name, resp, extracted_dir)

        elif resp.status_code in [400, 403, 401, 302, 404]:
            _logger.error(f"Cannot find that archive at {archive_url}")
            raise InvalidConfigurationError("Cannot find archive with the url: %s", archive_url)

        else:
            _logger.error(f"Error fetching archive at {archive_url} with status code {resp.status_code}")
            raise InvalidConfigurationError(
                "Error fetching archive with the url (error code %s): %s", str(resp.status_code), archive_url
            )


def fetch_archived_module(
    release_path: str, session: Optional[boto3.Session] = None, secret_name: Optional[str] = None
) -> Tuple[str, str]:
    """
    Fetch an archived module from a release path. This can be a private HTTPS link.

    This function will clone the repo to the seedfarmer.archive directory
    and return the path to the cloned repo and the relative path to the module code.

    Parameters
    ----------
    release_path: str
        The path passed in to fetch. If using a ProServe provided repo, this should look like
        archive::https://github.com/awslabs/idf-modules/archive/refs/tags/v1.10.0.zip?module=modules/dummy/dummy
    session: boto3.Session | None
        The boto3 session to use to fetch the module repo.
        Only used if the ``release_path`` is a private HTTPS link.
    secret_name: str | None
        The name of the secret to use to fetch the module repo.
        Only used if the ``release_path`` is a private HTTPS link.

    Returns
    -------
    Tuple[str,str]
        Returns a tuple that contains (in order):
            - the full path of the seedfarmer.archive where the repo was cloned to
            - the relative path to seedfarmer.gitmodules of the module code
    """
    return _get_release_with_link(release_path.replace("archive::", ""), session=session, secret_name=secret_name)
