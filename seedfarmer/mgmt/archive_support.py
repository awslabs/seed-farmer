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
from typing import Tuple
from urllib.parse import parse_qs, urlparse
from zipfile import ZipFile

import requests
from requests.models import Response

from seedfarmer import config
from seedfarmer.errors import InvalidConfigurationError

_logger: logging.Logger = logging.getLogger(__name__)
parent_dir = os.path.join(config.OPS_ROOT, "seedfarmer.archive")


def _process_tar(archive_name: str, response: Response, extracted_dir: str) -> str:
    pathlib.Path(parent_dir).mkdir(parents=True, exist_ok=True)
    with open(archive_name, "wb") as z_file:
        z_file.write(response.content)
    tar = tarfile.open(archive_name, "r:gz")
    embedded_dir = os.path.commonprefix(tar.getnames())
    tar.extractall(parent_dir)
    tar.close()
    os.rename(os.path.join(parent_dir, embedded_dir), os.path.join(parent_dir, extracted_dir))
    os.remove(archive_name)
    return os.path.join(parent_dir, extracted_dir)


def _process_zip(archive_name: str, response: Response, extracted_dir: str) -> str:
    pathlib.Path(parent_dir).mkdir(parents=True, exist_ok=True)
    with open(archive_name, "wb") as z_file:
        z_file.write(response.content)
    with ZipFile(archive_name, "r") as zp:
        embedded_dir = zp.namelist()[0]
        zp.extractall(parent_dir)
    os.rename(os.path.join(parent_dir, embedded_dir), os.path.join(parent_dir, extracted_dir))
    os.remove(archive_name)
    return os.path.join(parent_dir, extracted_dir)


def _get_release_with_link(archive_url: str) -> Tuple[str, str]:
    r = urlparse(archive_url)
    query_params = parse_qs(r.query)
    p = r.path

    if not r.scheme == "https":
        raise InvalidConfigurationError("This url must be via https: %s", archive_url)

    if not query_params.get("module"):
        raise InvalidConfigurationError("module query param required : %s", archive_url)
    module = query_params["module"][0]

    archive_name = p.replace("/", "_")
    extracted_dir = p.replace(".tar.gz", "").replace(".zip", "").replace("/", "_")

    if os.path.isdir(os.path.join(parent_dir, extracted_dir)):
        return os.path.join(parent_dir, extracted_dir), module
    else:
        # TODO: add a check here for an S3 HTTPS DNS, and if so, add the SigV4 Auth to the url
        active_url = r._replace(fragment="").geturl()
        if "s3.amazonaws" in active_url:
            pass
            ## TODO - add Sigv4Auth here
            # session = SessionManager().get_or_create().toolchain_session
            # credentials = SessionManager().get_or_create().get_toolchain_credentials()
            # # GOTTA use the toolchain role - so get the toolchain session
            # active_url = create_signed_request(endpoint=active_url, session=session, credentials=credentials)
            # z = requests.get(active_url.url, headers=active_url.headers,allow_redirects=True)
        else:
            z = requests.get(active_url, allow_redirects=True)
        if z.status_code == 200:
            return (
                (_process_tar(archive_name, z, extracted_dir), module)
                if archive_name.endswith(".tar.gz")
                else (_process_zip(archive_name, z, extracted_dir), module)
            )
        if z.status_code in [400, 403, 401, 302, 404]:
            _logger.error(f"Cannot find that archive at {archive_url}")
            raise InvalidConfigurationError("Cannot find archive with the url: %s", archive_url)


def fetch_module_repo(release_path: str) -> Tuple[str, str]:
    """
    fetch_module_repo _summary_

    Parameters
    ----------
    release_path : str
        The path passed in to fetch. If using a ProServe provided repo, this should look like
        archive::https://github.com/awslabs/idf-modules/archive/refs/tags/v1.10.0.zip?module=modules/dummy/dummy


    Returns
    -------
    Tuple[str, str]
        Returns a tuple that contains (in order):
        - the full path of the seedfarmer.archive where the repo was cloned to
        - the relative path under seedfarmer.archive of the module code
    """
    return _get_release_with_link(release_path.replace("archive::", ""))
