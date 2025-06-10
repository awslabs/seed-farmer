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
import pathlib

import pytest

_logger: logging.Logger = logging.getLogger(__name__)


@pytest.mark.checksum
def test_checksum():
    import seedfarmer.checksum as checksum

    root = pathlib.Path(os.getcwd())
    project_path = os.path.join(root, "test", "unit-test", "mock_data")
    module_path = os.path.join(project_path, "modules", "module-test")
    _checksum = checksum.get_module_md5(project_path=project_path, module_path=module_path)
    assert _checksum == "6320bfae9c91bed55ac6f3dc6f752f88"


@pytest.mark.checksum
def test_private_methods_checksum():
    import seedfarmer.checksum as checksum

    file_tst = os.path.abspath(__file__)
    assert checksum._evaluate_file(filename=file_tst, ignore_maps=None) is False

    _check_non = checksum._generate_file_hash(filepath=f"{file_tst}_bak")
    assert _check_non == "d41d8cd98f00b204e9800998ecf8427e"
