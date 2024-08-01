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
import shutil

import pytest

_logger: logging.Logger = logging.getLogger(__name__)


## Test Build Info
# @pytest.mark.mgmt
# def test_get_build_info():
#     import seedfarmer.mgmt.build_info as bi
#     bi.get_build_env_params(build_ids=['codebuild:123345'])


### Test Model Info
# @pytest.mark.mgmt
# def test_get_build_info(mocker):
#     import seedfarmer.mgmt.module_info as mi
#     mocker.patch()
#     mi.get_deployspec_path(module_path='test/unut-test/mock_data/modules/module-test')


### Test Model Init
@pytest.mark.mgmt
def test_module_init():
    setup_mod_dir = os.path.join(pathlib.Path(os.getcwd()), "modules")

    if os.path.isdir(setup_mod_dir):
        shutil.rmtree(setup_mod_dir)
    import seedfarmer.mgmt.module_init as mi

    mi.create_module_dir(
        module_name="mytestmodule",
        group_name="mygroup",
        module_type=None,
        template_url="https://github.com/awslabs/seed-farmer.git",
    )

    with pytest.raises(Exception) as e:
        mi.create_module_dir(
            module_name="mytestmodule",
            group_name="mygroup",
            module_type=None,
            template_url="https://github.com/awslabs/seed-farmer.git",
        )

    assert "module mytestmodule already exists" in str(e)

    shutil.rmtree(setup_mod_dir)


@pytest.mark.mgmt
def test_module_init_cdkv2():
    setup_mod_dir = os.path.join(pathlib.Path(os.getcwd()), "modules")

    if os.path.isdir(setup_mod_dir):
        shutil.rmtree(setup_mod_dir)
    import seedfarmer.mgmt.module_init as mi

    mi.create_module_dir(
        module_name="mytestmodule",
        group_name="mygroup",
        module_type="cdkv2",
        template_url="https://github.com/awslabs/seed-farmer.git",
    )

    with pytest.raises(Exception) as e:
        mi.create_module_dir(
            module_name="mytestmodule",
            group_name="mygroup",
            module_type="cdkv2",
            template_url="https://github.com/awslabs/seed-farmer.git",
        )

    assert "module mytestmodule already exists" in str(e)

    shutil.rmtree(setup_mod_dir)


@pytest.mark.mgmt
def test_module_init_branch():
    setup_mod_dir = os.path.join(pathlib.Path(os.getcwd()), "modules")

    if os.path.isdir(setup_mod_dir):
        shutil.rmtree(setup_mod_dir)
    import seedfarmer.mgmt.module_init as mi

    mi.create_module_dir(
        module_name="mytestmodule",
        group_name="mygroup",
        module_type="NOT_NEEDED",
        template_url="https://github.com/briggySmalls/cookiecutter-pypackage.git",
        template_branch="master",
    )

    with pytest.raises(Exception) as e:
        mi.create_module_dir(
            module_name="mytestmodule",
            group_name="mygroup",
            module_type="NOT_NEEDED",
            template_url="https://github.com/briggySmalls/cookiecutter-pypackage.git",
            template_branch="master",
        )

    assert "module mytestmodule already exists" in str(e)

    shutil.rmtree(setup_mod_dir)


@pytest.mark.mgmt
def test_project_init():
    setup_project_dir = os.path.join(pathlib.Path(os.getcwd()), "myapp")

    if os.path.isdir(setup_project_dir):
        shutil.rmtree(setup_project_dir)
    import seedfarmer.mgmt.module_init as mi

    mi.create_project(template_url="https://github.com/awslabs/seed-farmer.git")

    shutil.rmtree(setup_project_dir)
    shutil.copyfile(
        os.path.join(os.path.join(os.getcwd()), "test", "unit-test", "mock_data", "seedfarmer.yaml"),
        os.path.join(os.path.join(os.getcwd()), "seedfarmer.yaml"),
    )
