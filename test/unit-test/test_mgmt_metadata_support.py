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

import distutils.dir_util
import json
import logging
import os
import pathlib
import shutil
from typing import Dict, Tuple

import pytest

import seedfarmer.mgmt.metadata_support as ms

_logger: logging.Logger = logging.getLogger(__name__)


@pytest.fixture(scope="function")
def build_env():
    os.environ["SEEDFARMER_PROJECT_NAME"] = "myapp-generic"
    os.environ["SEEDFARMER_DEPLOYMENT_NAME"] = "simpledeployment"
    os.environ["SEEDFARMER_MODULE_NAME"] = "simpletest"
    os.environ["MYAPP_PROJECT_NAME"] = "myapp-project"
    os.environ["MYAPP_DEPLOYMENT_NAME"] = "simpledeployment"
    os.environ["MYAPP_MODULE_NAME"] = "simpletest"


@pytest.mark.mgmt_metadata_support
def test_module_init(build_env):
    setup_module_dir = os.path.join(pathlib.Path(os.getcwd()), "module")

    if os.path.isdir(setup_module_dir):
        shutil.rmtree(setup_module_dir)

    os.mkdir(setup_module_dir)

    shutil.copyfile(
        os.path.join(os.path.join(os.getcwd()), "test", "unit-test", "mock_data", "seedfarmer.yaml"),
        os.path.join(os.path.join(os.getcwd()), "seedfarmer.yaml"),
    )
    distutils.dir_util.copy_tree(
        os.path.join(os.path.join(os.getcwd()), "test", "unit-test", "mock_data", "module"),
        os.path.join(os.path.join(os.getcwd()), "module"),
    )


def _copyfile(from_file: str, to_file: str):
    shutil.copyfile(
        os.path.join(os.path.join(os.getcwd()), "module", from_file),
        os.path.join(os.path.join(os.getcwd()), "module", to_file),
    )


def _generic_file_exists() -> Tuple[str, bool]:
    output_file = pathlib.Path(os.path.join(os.getcwd(), "module", "SEEDFARMER_MODULE_METADATA"))
    return (output_file, output_file.is_file())


def _project_file_exists() -> Tuple[str, bool]:
    output_file = pathlib.Path(os.path.join(os.getcwd(), "module", "MYAPP_MODULE_METADATA"))
    return (output_file, output_file.is_file())


def _open_metadata(path: str) -> Dict[str, str]:
    with open(path, "r") as datafile:
        j = datafile.read()
    return dict(json.loads(j))


@pytest.mark.mgmt_metadata_support
def test_module_depmod_generic(build_env):
    _copyfile("deployspec_generic.yaml", "deployspec.yaml")
    dep_mod = ms.get_dep_mod_name()
    assert dep_mod == "myapp-generic-simpledeployment-simpletest"


@pytest.mark.mgmt_metadata_support
def test_module_parameter_generic(build_env):
    _copyfile("deployspec_generic.yaml", "deployspec.yaml")
    param_val = ms.get_parameter_value("DEPLOYMENT_NAME")
    assert param_val == "simpledeployment"


@pytest.mark.mgmt_metadata_support
def test_module_parameter_generic_error(build_env):
    _copyfile("deployspec_generic.yaml", "deployspec.yaml")
    param_val = ms.get_parameter_value("DEPLOYMENT_NAME_NOT_EXISTANT")
    assert param_val is None


@pytest.mark.mgmt_metadata_support
def test_module_deployspec_error(build_env):
    os.remove(
        os.path.join(os.path.join(os.getcwd()), "module", "deployspec.yaml"),
    )
    param_val = ms.get_parameter_value("DEPLOYMENT_NAME")
    assert param_val == "simpledeployment"


@pytest.mark.mgmt_metadata_support
def test_module_add_kv_generic(build_env):
    _copyfile("deployspec_generic.yaml", "deployspec.yaml")
    ms.add_kv_output(key="TestKV", value="KVValue")
    output_path, does_exist = _generic_file_exists()
    assert True is does_exist
    metadata = _open_metadata(output_path)
    assert "TestKV" in metadata.keys()


@pytest.mark.mgmt_metadata_support
def test_module_add_json_generic(build_env):
    _copyfile("deployspec_generic.yaml", "deployspec.yaml")
    ms.add_kv_output(key="TestKV", value="KVValue")
    ms.add_json_output(json_string='{"TestJsonString":"Yo"}')
    output_path, does_exist = _generic_file_exists()
    assert True is does_exist
    metadata = _open_metadata(output_path)
    assert "TestJsonString" in metadata.keys()


@pytest.mark.mgmt_metadata_support
def test_module_convert_cdkexports_generic(build_env):
    _copyfile("deployspec_generic.yaml", "deployspec.yaml")
    ms.convert_cdkexports(json_file="cdk-exports.json")
    output_path, does_exist = _generic_file_exists()
    assert True is does_exist
    metadata = _open_metadata(output_path)
    assert "ArtifactsBucketName" in metadata.keys()


@pytest.mark.mgmt_metadata_support
def test_module_convert_cdkexports_generic_jq(build_env):
    _copyfile("deployspec_generic.yaml", "deployspec.yaml")
    ms.convert_cdkexports(
        json_file="cdk-exports.json", jq_path="addf-workshop-demo-integration-rosbag-ddb-to-os.metadata"
    )
    output_path, does_exist = _generic_file_exists()
    assert True is does_exist
    metadata = _open_metadata(output_path)
    assert "ArtifactsBucketName" in metadata.keys()


@pytest.mark.mgmt_metadata_support
def test_module_depmod_project(build_env):
    _copyfile("deployspec_project.yaml", "deployspec.yaml")
    dep_mod = ms.get_dep_mod_name()
    assert dep_mod == "myapp-project-simpledeployment-simpletest"


@pytest.mark.mgmt_metadata_support
def test_module_parameter_project(build_env):
    _copyfile("deployspec_project.yaml", "deployspec.yaml")
    param_val = ms.get_parameter_value("DEPLOYMENT_NAME")
    assert param_val == "simpledeployment"


@pytest.mark.mgmt_metadata_support
def test_module_parameter_project_error(build_env):
    _copyfile("deployspec_project.yaml", "deployspec.yaml")
    param_val = ms.get_parameter_value("DEPLOYMENT_NAME_NOT_THERE")
    assert param_val is None


@pytest.mark.mgmt_metadata_support
def test_module_add_kv_project(build_env):
    _copyfile("deployspec_project.yaml", "deployspec.yaml")
    ms.add_kv_output(key="TestKV", value="KVValue")
    output_path, does_exist = _project_file_exists()
    assert True is does_exist
    metadata = _open_metadata(output_path)
    assert "TestKV" in metadata.keys()


@pytest.mark.mgmt_metadata_support
def test_module_add_json_project(build_env):
    _copyfile("deployspec_project.yaml", "deployspec.yaml")
    ms.add_kv_output(key="TestKV", value="KVValue")
    ms.add_json_output(json_string='{"TestJsonString":"Yo"}')
    output_path, does_exist = _project_file_exists()
    assert True is does_exist
    metadata = _open_metadata(output_path)
    assert "TestJsonString" in metadata.keys()


@pytest.mark.mgmt_metadata_support
def test_module_convert_cdkexports_project(build_env):
    _copyfile("deployspec_project.yaml", "deployspec.yaml")
    ms.convert_cdkexports(json_file="cdk-exports.json")
    output_path, does_exist = _generic_file_exists()
    assert True is does_exist
    metadata = _open_metadata(output_path)
    assert "ArtifactsBucketName" in metadata.keys()


@pytest.mark.mgmt_metadata_support
def test_module_convert_cdkexports_project_jq(build_env):
    _copyfile("deployspec_project.yaml", "deployspec.yaml")
    ms.convert_cdkexports(
        json_file="cdk-exports.json", jq_path="addf-workshop-demo-integration-rosbag-ddb-to-os.metadata"
    )
    output_path, does_exist = _generic_file_exists()
    assert True is does_exist
    metadata = _open_metadata(output_path)
    assert "ArtifactsBucketName" in metadata.keys()
