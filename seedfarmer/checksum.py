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
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, cast

from gitignore_parser import parse_gitignore

from seedfarmer.models.manifests._module_manifest import DataFile


def _evaluate_gitignore(project_path: str, module_path: str) -> Dict[str, Any]:
    ignore_paths: List[str] = []
    ignore_maps: Dict[str, Any] = {}

    def _get_paths(working_dir: str) -> None:
        gitignore_path = os.path.join(working_dir, ".gitignore")
        ignore_paths.append(gitignore_path) if os.path.exists(gitignore_path) else None
        if os.path.realpath(working_dir) != os.path.realpath(project_path):
            _get_paths(str(Path(os.path.join(working_dir, os.pardir)).resolve()))

    # If the .gitignore path exists, parse_gitignore returns a function that is callable
    _get_paths(os.path.join(project_path, module_path))
    for ignore_path in ignore_paths:
        if os.path.exists(ignore_path):
            ignore_maps[ignore_path] = parse_gitignore(ignore_path)

    return ignore_maps


def _evaluate_file(filename: str, ignore_maps: Dict[str, Any]) -> bool:
    # The map of functions representing .gitignore is called with
    # the filename as a parameter, returning a boolean.
    # If the filename is present .gitignore return True
    # else return False
    if ignore_maps is None:
        return False

    for ignore_key in ignore_maps.keys():
        if ignore_maps.get(ignore_key) is not None:
            in_ignore = (ignore_maps.get(ignore_key))(filename)  # type: ignore
            if in_ignore:
                return True
    return False


def _generate_file_hash(filepath: str) -> str:
    hash = hashlib.md5()
    blocksize = 64 * 1024

    if not os.path.exists(filepath):
        return hash.hexdigest()

    with open(filepath, "rb") as fp:
        while True:
            data = fp.read(blocksize)
            if not data:
                break
            hash.update(data)
    digest = hash.hexdigest()
    return digest


def _consolidate_hash(hashlist: List[str]) -> str:
    hash = hashlib.md5()
    for hashvalue in sorted(hashlist):
        hash.update(hashvalue.encode("utf-8"))
    return hash.hexdigest()


def get_module_md5(
    project_path: str,
    module_path: str,
    data_files: Optional[List[DataFile]] = None,
    excluded_files: Optional[List[str]] = [],
) -> str:
    """
    This will generate an MD5 of the module source code, respecting .gitingore starting at
    the module level

    Parameters
    ----------
    project_path : str
       The OPS_ROOT full path (full path of the project)
    module_path : str
        The relative path of the module code (relative to OPS_ROOT)
    data_files: Optional[List[DataFile]]
        List of DataFile objects to be packaged in the bundle
    excluded_files : List[str], optional
        A list of additional files not in .gitignore that will be exclude from the bundle md5
            NOTE: this list of files is ONLY at the module level, not subdirecties of
            the module...use .gitignore for that

    Returns
    -------
    str
        the md5 of the module code
    """
    ignore_maps = _evaluate_gitignore(project_path=project_path, module_path=module_path)

    excluded_files = [] if excluded_files is None else excluded_files

    all_files = []

    def scandir(dirname: str) -> List[str]:
        files = [
            f.path
            for f in os.scandir(dirname)
            if f.is_file()
            and os.path.split(f)[1] not in cast(List[str], excluded_files)
            and not _evaluate_file(f.path, ignore_maps)
        ]
        all_files.extend(files)
        subfolders = [f.path for f in os.scandir(dirname) if f.is_dir()]
        for dirname in list(subfolders):
            # ignore all hidden directories and any dir already in .gitignore
            subfolders.extend(scandir(dirname)) if not os.path.split(dirname)[1].startswith(".") and not _evaluate_file(
                dirname, ignore_maps
            ) else None
        return subfolders

    _ = scandir(os.path.join(project_path, module_path))

    # Add in the extra files
    if data_files is not None:
        for data_file in data_files:
            (
                all_files.append(os.path.join(data_file.get_local_file_path(), data_file.file_path))  # type: ignore
                if os.path.isfile(os.path.join(data_file.get_local_file_path(), data_file.file_path))  # type: ignore
                else None
            )

    hashvalues: List[str] = []
    for viable_file in all_files:
        hashvalues.append(_generate_file_hash(viable_file))
    return _consolidate_hash(hashvalues)
