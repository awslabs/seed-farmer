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

import json
import logging
import os.path
import pathlib
import tarfile
from typing import Optional
from urllib.parse import urlparse
from zipfile import ZipFile

import boto3
import requests
from requests.auth import HTTPBasicAuth
from requests.models import Response

from seedfarmer import config
from seedfarmer.errors import InvalidConfigurationError

_logger: logging.Logger = logging.getLogger(__name__)
parent_dir = os.path.join(config.OPS_ROOT, "seedfarmer.archive")


def _download_archive(archive_url: str, secret_arn: Optional[str]) -> Response:
    if secret_arn:
        region = "us-west-2"  # TODO: get toolchain region
        sm_client = boto3.client("secretsmanager", region)

        credentials = json.loads(sm_client.get_secret_value(SecretId=secret_arn)["SecretString"])

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
        if credentials:
            auth = HTTPBasicAuth(credentials["user"], credentials["password"])
        else:
            auth = None

        resp = requests.get(archive_url, auth=auth, allow_redirects=True)

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


def _process_archive(archive_name: str, response: Response, extracted_dir: str) -> str:
    pathlib.Path(parent_dir).mkdir(parents=True, exist_ok=True)

    with open(archive_name, "wb") as archive_file:
        archive_file.write(response.content)

    embedded_dir = _extract_archive(archive_name)

    os.rename(os.path.join(parent_dir, embedded_dir), os.path.join(parent_dir, extracted_dir))
    os.remove(archive_name)

    return os.path.join(parent_dir, extracted_dir)


def _get_release_with_link(archive_url: str, secret_arn: Optional[str]) -> str:
    parsed_url = urlparse(archive_url)

    if not parsed_url.scheme == "https":
        raise InvalidConfigurationError("This url must be via https: %s", archive_url)

    archive_name = parsed_url.path.replace("/", "_")
    extracted_dir = parsed_url.path.replace(".tar.gz", "").replace(".zip", "").replace("/", "_")

    if os.path.isdir(os.path.join(parent_dir, extracted_dir)):
        return os.path.join(parent_dir, extracted_dir)
    else:
        resp = _download_archive(parsed_url._replace(fragment="").geturl(), secret_arn)

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


def fetch_module_repo(release_path: str, secret_arn: Optional[str] = None) -> str:
    """
    fetch_module_repo _summary_

    Parameters
    ----------
    release_path : str
        The path passed in to fetch. If using a ProServe provided repo, this should look like
        archive::https://github.com/awslabs/idf-modules/archive/refs/tags/v1.10.0.zip?module=modules/dummy/dummy

    Returns
    -------
    str:
        the full path of the seedfarmer.archive where the repo was cloned to
    """
    return _get_release_with_link(release_path.replace("archive::", ""), secret_arn)
