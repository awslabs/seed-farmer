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
import os

import pytest
from _test_helper_functions import _test_command

import seedfarmer.commands._stack_commands as _sc
import seedfarmer.mgmt.module_init as minit
from seedfarmer.__main__ import PROJECT, apply, destroy, init
from seedfarmer.__main__ import list as _list
from seedfarmer.__main__ import remove, store

# Override _stack_commands OPS_ROOT to reflect path of resource policy needed for some testing #
_sc.OPS_ROOT = os.path.join(_sc.OPS_ROOT, "test/unit-test/mock_data")

_logger: logging.Logger = logging.getLogger(__name__)

# -------------------------------------------
# -----   Test the sub-command `init`   -----
# -------------------------------------------


@pytest.mark.init
def test_init_create_module():
    module_name = "test-module"
    expected_module_path = os.path.join(minit.OPS_ROOT, "modules")

    # Creates a new module
    _test_command(sub_command=init, options=["module", "-m", module_name], exit_code=0, return_result=False)

    # Creates a module that already exist
    result = _test_command(sub_command=init, options=["module", "-m", module_name], exit_code=1, return_result=True)
    print(result.exception.args[0])
    assert result.exception.args[0] == f"The module {module_name} already exists under {expected_module_path}."

    # Checks if file exists from the project template
    assert os.path.exists(os.path.join(expected_module_path, module_name, "deployspec.yaml"))


@pytest.mark.init
def test_init_create_group_module():
    module_name = "test-module"
    group_name = "group"
    expected_module_path = os.path.join(minit.OPS_ROOT, "modules", group_name, module_name)

    # Creates a group and a module within the group
    _test_command(sub_command=init, options=["module", "-g", group_name, "-m", module_name], exit_code=0)
    assert os.path.exists(expected_module_path)

    # Creates a group and a module that already exists within the group
    result = _test_command(
        sub_command=init, options=["module", "-g", group_name, "-m", module_name], exit_code=1, return_result=True
    )
    assert (
        result.exception.args[0]
        == f"The module {module_name} already exists under {minit.OPS_ROOT}/modules/{group_name}."
    )

    # Checks if a file from the project template was created within the new module
    assert os.path.exists(os.path.join(expected_module_path, "deployspec.yaml"))


@pytest.mark.init
def test_init_create_project(tmp_path):
    expected_project_path = os.path.join(minit.OPS_ROOT, PROJECT)

    # Creates a new project
    _test_command(sub_command=init, options=["project"], exit_code=0, return_result=False)

    # Creates a project that already exist
    result = _test_command(sub_command=init, options=["project"], exit_code=1, return_result=True)
    assert result.exception.args[0] == f'Error: "{os.path.join(minit.OPS_ROOT, PROJECT)}" directory already exists'

    # Checks if file exists from the project template
    assert os.path.exists(os.path.join(expected_project_path, "seedfarmer.yaml"))


# -------------------------------------------
# -----  Test the sub-command `apply`   -----
# -------------------------------------------


@pytest.mark.apply
def test_apply_help():
    _test_command(
        sub_command=apply,
        options=["--help"],
        exit_code=0,
        expected_output=f"Apply a deployment manifest relative path for {PROJECT.upper()}",
    )


@pytest.mark.first
@pytest.mark.apply_working_module
def test_apply_deployment():
    # Deploys a functioning module
    deployment_manifest = "test/unit-test/mock_data/manifests/module-test/deployment.yaml"

    _test_command(sub_command=apply, options=deployment_manifest, exit_code=0)


@pytest.mark.apply
def test_apply_missing_deployment():
    deployment_manifest = "test/unit-test/mock_data/manifests/test-missing-deployment-manifest/deployment.yaml"

    result = _test_command(sub_command=apply, options=deployment_manifest, exit_code=1, return_result=True)
    assert result.exception.args[1] == "No such file or directory"


@pytest.mark.apply
def test_apply_missing_group_manifest():
    deployment_manifest = "test/unit-test/mock_data/manifests/test-missing-group-manifest/deployment.yaml"

    result = _test_command(sub_command=apply, options=deployment_manifest, exit_code=1, return_result=True)
    assert result.exception.args[1] == "No such file or directory"


@pytest.mark.apply
def test_apply_missing_deployment_group_name():
    deployment_manifest = "test/unit-test/mock_data/manifests/test-missing-deployment-group-name/deployment.yaml"

    result = _test_command(sub_command=apply, options=deployment_manifest, exit_code=1, return_result=True)
    assert result.exception.args[0][0][0].exc.errors()[0]["msg"] == "none is not an allowed value"


@pytest.mark.apply
def test_apply_missing_deployment_group_path():
    deployment_manifest = "test/unit-test/mock_data/manifests/test-missing-deployment-group-path/deployment.yaml"

    result = _test_command(sub_command=apply, options=deployment_manifest, exit_code=1, return_result=True)
    assert result.exception.args[0] == "One of the `path` or `modules` attributes must be defined on a Group"


@pytest.mark.apply
def test_apply_missing_deployment_name():
    deployment_manifest = "test/unit-test/mock_data/manifests/test-missing-deployment-name/deployment.yaml"

    result = _test_command(sub_command=apply, options=deployment_manifest, exit_code=1, return_result=True)
    assert result.exception.args[0][0].exc.msg_template == "none is not an allowed value"


@pytest.mark.apply
def test_apply_broken_deploy_phase():
    deployment_manifest = "test/unit-test/mock_data/manifests/test-broken-deployspec-deploy/deployment.yaml"

    result = _test_command(sub_command=apply, options=deployment_manifest, exit_code=1, return_result=True)
    assert result.exception.args[0][0].exc.errors()[0]["msg"] == "none is not an allowed value"


# # TODO add test for broken destroy phase
# @pytest.mark.destroy
# def test_destroy_broken_deploy_phase():
#     deployment_manifest = "test/unit-test/mock_data/manifests/test-broken-deployspec-destroy/deployment.yaml"

#     result = _test_command(sub_command=destroy, options=deployment_manifest, exit_code=1, return_result=True)
#     assert result.exception.args[0][0].exc.errors()[0]['msg'] == "none is not an allowed value"

# -------------------------------------------
# -----  Test the sub-command `list`    -----
# -------------------------------------------


@pytest.mark.list
def test_list_help():
    _test_command(
        _list,
        options=["--help"],
        exit_code=0,
        expected_output="List the relative data (module or deployment",
    )


# Test `list deployments` #


@pytest.mark.list
@pytest.mark.list_deployments
def test_list_deployments_help():
    _test_command(
        sub_command=_list,
        options=["deployments", "--help"],
        exit_code=0,
        expected_output="List the deployments in this account",
    )


@pytest.mark.list
@pytest.mark.list_deployments
def test_list_deployments_extra_args():
    _test_command(
        sub_command=_list,
        options=[
            "deployments",
            "dsfsd",
        ],
        exit_code=2,
        expected_output="Got unexpected extra argument",
    )


@pytest.mark.second
@pytest.mark.list
@pytest.mark.list_deployments
def test_list_deployments():
    _test_command(
        sub_command=_list,
        options=[
            "deployments",
        ],
        exit_code=0,
        expected_output="example-test-dev",
    )


# TODO test for no deployments

# Test `list moduledata` #


@pytest.mark.list
@pytest.mark.list_moduledata
def test_list_moduledata_help():
    _test_command(
        sub_command=_list,
        options=["moduledata", "--help"],
        exit_code=0,
        expected_output="Fetch the module metadata",
    )


@pytest.mark.list
@pytest.mark.list_moduledata
def test_list_moduledata_missing_deployment_option():
    _test_command(
        sub_command=_list,
        options=[
            "moduledata",
        ],
        exit_code=2,
    )


@pytest.mark.list
@pytest.mark.list_moduledata
def test_list_moduledata_missing_deployment_arg():
    _test_command(sub_command=_list, options=["moduledata", "-d"], exit_code=2)


@pytest.mark.list
@pytest.mark.list_moduledata
def test_list_moduledata_missing_group_option():
    _test_command(sub_command=_list, options=["moduledata", "-d", "test-deployment"], exit_code=2)


@pytest.mark.list
@pytest.mark.list_moduledata
def test_list_moduledata_missing_group_arg():
    _test_command(sub_command=_list, options=["moduledata", "-d", "test-deployment", "-g"], exit_code=2)


@pytest.mark.list
@pytest.mark.list_moduledata
def test_list_moduledata_missing_module_option():
    _test_command(sub_command=_list, options=["moduledata", "-d", "test-deployment", "-g", "group-name"], exit_code=2)


@pytest.mark.list
@pytest.mark.list_moduledata
def test_list_moduledata_missing_module_arg():
    _test_command(
        sub_command=_list, options=["moduledata", "-d", "test-deployment", "-g", "group-name", "-m"], exit_code=2
    )


@pytest.mark.list
@pytest.mark.list_moduledata
def test_list_moduledata_non_existent_module():
    _test_command(
        sub_command=_list,
        options=["moduledata", "-d", "test-deployment", "-g", "group-name", "-m", "module-name"],
        exit_code=0,
        expected_output="null",
    )


@pytest.mark.list
@pytest.mark.list_moduledata
def test_list_moduledata():
    result = _test_command(
        sub_command=_list,
        options=["moduledata", "-d", "example-test-dev", "-g", "test", "-m", "test-module"],
        exit_code=0,
        return_result=True,
    )
    assert json.loads(result.output).get("CognitoDomainName") == "testdomaindomaintest"


# Test `list modules` #


@pytest.mark.list
@pytest.mark.list_modules
def test_list_modules_help():
    _test_command(
        sub_command=_list,
        options=["modules", "--help"],
        exit_code=0,
        expected_output="List the modules in a group",
    )


@pytest.mark.list
@pytest.mark.list_modules
def test_list_modules_incomplete_subcommand():
    _test_command(
        sub_command=_list,
        options=[
            "modules",
        ],
        exit_code=2,
    )


@pytest.mark.list
@pytest.mark.list_modules
def test_list_modules_missing_deployment_arg():
    _test_command(sub_command=_list, options=["modules", "-d"], exit_code=2)


@pytest.mark.list
@pytest.mark.list_modules
def test_list_modules_non_existent_module():
    _test_command(sub_command=_list, options=["modules", "-d", "zzz"], exit_code=0, return_result=True)


@pytest.mark.list
@pytest.mark.list_modules
def test_list_modules():
    _test_command(
        sub_command=_list,
        options=["modules", "-d", "example-test-dev"],
        exit_code=0,
        expected_output="example-test-dev",
    )


# -------------------------------------------
# -----  Test the sub-command `remove`  -----
# -------------------------------------------


@pytest.mark.remove
def test_remove_help():
    # Test the sub-command `remove --help`
    _test_command(
        sub_command=remove,
        options=["--help"],
        exit_code=0,
        expected_output="Top Level command to support removing module metadata",
    )


@pytest.mark.remove
def test_remove_missing_deployment_option():
    _test_command(
        sub_command=remove,
        options=[
            "moduledata",
        ],
        exit_code=2,
    )


@pytest.mark.remove
def test_remove_missing_deployment_argument():
    _test_command(sub_command=remove, options=["moduledata", "-d"], exit_code=2)


@pytest.mark.remove
def test_remove_missing_group_option():
    _test_command(sub_command=remove, options=["moduledata", "-d", "deployment-name"], exit_code=2)


@pytest.mark.remove
def test_remove_missing_group_arg():
    _test_command(sub_command=remove, options=["moduledata", "-d", "deployment-name", "-g"], exit_code=2)


@pytest.mark.remove
def test_remove_missing_module_option():
    _test_command(sub_command=remove, options=["moduledata", "-d", "deployment-name", "-g", "group-name"], exit_code=2)


@pytest.mark.remove
def test_remove_missing_module_arg():
    _test_command(
        sub_command=remove, options=["moduledata", "-d", "deployment-name", "-g", "group-name", "-m"], exit_code=2
    )


@pytest.mark.remove
def test_remove_non_existent_module():
    _test_command(
        sub_command=remove,
        options=["moduledata", "-d", "deployment-name", "-g", "group-name", "-m", "zzz"],
        exit_code=0,
    )


@pytest.mark.remove
def test_remove_module():
    _test_command(
        sub_command=remove,
        options=["moduledata", "-d", "example-test-dev", "-g", "test", "-m", "test-module"],
        exit_code=0,
    )


# -------------------------------------------
# -----  Test the sub-command `store`   -----
# -------------------------------------------


@pytest.mark.store
def test_store_help():
    _test_command(
        sub_command=store,
        options=["--help"],
        exit_code=0,
        expected_output="Top Level command to support storing module metadata",
    )


# Testing `store md5` #


@pytest.mark.store
@pytest.mark.store_md5
def test_store_md5_missing_deployment_option():
    _test_command(
        sub_command=store,
        options=["md5"],
        exit_code=2,
    )


@pytest.mark.store
@pytest.mark.store_md5
def test_store_md5_missing_deployment_arg():
    _test_command(sub_command=store, options=["md5", "-d"], exit_code=2)


@pytest.mark.store
@pytest.mark.store_md5
def test_store_md5_missing_group_option():
    _test_command(sub_command=store, options=["md5", "-d", "deployment-name"], exit_code=2)


@pytest.mark.store
@pytest.mark.store_md5
def test_store_md5_missing_group_arg():
    _test_command(sub_command=store, options=["md5", "-d", "deployment-name", "-g"], exit_code=2)


@pytest.mark.store
@pytest.mark.store_md5
def test_store_md5_missing_module_option():
    _test_command(sub_command=store, options=["md5", "-d", "deployment-name", "-g", "group-name"], exit_code=2)


@pytest.mark.store
@pytest.mark.store_md5
def test_store_md5_missing_module_arg():
    _test_command(sub_command=store, options=["md5", "-d", "deployment-name", "-g", "group-name", "-m"], exit_code=2)

    # TODO Missing type option
    # this should fail, but exit code is 0
    # _test_command(
    #     sub_command=store,
    #     options=["moduledata", "-d", "deployment-name", "-g", "group-name", "-m", "module-name"],
    #     exit_code=2
    # )


@pytest.mark.store
@pytest.mark.store_md5
def test_store_md5_missing_type_arg():
    _test_command(
        sub_command=store,
        options=["md5", "-d", "deployment-name", "-g", "group-name", "-m", "module-name", "-t"],
        exit_code=2,
    )

    # TODO make it work
    # Store hash to SSM of type spec
    # _test_command(
    #     sub_command=store,
    #     options=[
    #         "md5", "-d", "deployment-name", "-g", "group-name", "-m", "module-name", "-t", "spec",
    #         "<<< f4k3h4shmd5"
    #     ],
    #     exit_code=0
    # )

    # Store hash to SSM of type bundle
    # _test_command(
    #     sub_command=store,
    #     options=[
    #         "md5", "-d", "deployment-name", "-g", "group-name", "-m", "module-name", "-t", "bundle",
    #         "<<< f4k3h4shbund13"
    #     ],
    #     exit_code=0
    # )


# Testing `store moduledata` #


@pytest.mark.store
@pytest.mark.store_moduledata
def test_store_moduledata_missing_deployment_option():
    _test_command(
        sub_command=store,
        options=["moduledata"],
        exit_code=2,
    )


@pytest.mark.store
@pytest.mark.store_moduledata
def test_store_moduledata_deployment_arg():
    _test_command(sub_command=store, options=["moduledata", "-d"], exit_code=2)


@pytest.mark.store
@pytest.mark.store_moduledata
def test_store_moduledata_missing_group_option():
    _test_command(sub_command=store, options=["moduledata", "-d", "deployment-name"], exit_code=2)


@pytest.mark.store
@pytest.mark.store_moduledata
def test_store_moduledata_missing_group_arg():
    _test_command(sub_command=store, options=["moduledata", "-d", "deployment-name", "-g"], exit_code=2)


@pytest.mark.store
@pytest.mark.store_moduledata
def test_store_moduledata_missing_module_option():
    _test_command(sub_command=store, options=["moduledata", "-d", "deployment-name", "-g", "group-name"], exit_code=2)


@pytest.mark.store
@pytest.mark.store_moduledata
def test_store_moduledata_missing_module_arg():
    _test_command(
        sub_command=store, options=["moduledata", "-d", "deployment-name", "-g", "group-name", "-m"], exit_code=2
    )


# TODO add test for complete command
# @pytest.mark.store
# @pytest.mark.store_moduledata
# def test_store_moduledata():
# pass

# -------------------------------------------
# -----  Test the sub-command `destroy` -----
# -------------------------------------------


@pytest.mark.destroy
def test_destroy():
    _test_command(
        sub_command=destroy, options=["--help"], exit_code=0, expected_output=f"Destroy {PROJECT.upper()} Deployment"
    )


@pytest.mark.last
@pytest.mark.destroy
def test_destroy_working_module():
    # Destroys test_apply_deployment()
    _test_command(sub_command=destroy, options="example-test-dev", exit_code=0, return_result=False)


@pytest.mark.destroy
def test_destroy_non_existent_deployment():
    _test_command(sub_command=destroy, options="deployment-that-doesnt-exist", exit_code=0, return_result=False)
