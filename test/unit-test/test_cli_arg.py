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

import mock_data.mock_manifests as mock_manifests
import pytest
from _test_cli_helper_functions import _test_command
from moto import mock_sts

from seedfarmer import config
from seedfarmer.__main__ import apply, bootstrap, destroy, init
from seedfarmer.__main__ import list as list
from seedfarmer.__main__ import metadata, projectpolicy, remove, store, version
from seedfarmer.models._deploy_spec import DeploySpec
from seedfarmer.models.manifests import DeploymentManifest, ModulesManifest
from seedfarmer.services._service_utils import boto3_client
from seedfarmer.services.session_manager import SessionManager

# Override OPS_ROOT to reflect path of resource policy needed for some testing #
_OPS_ROOT = config.OPS_ROOT
_TEST_ROOT = os.path.join(config.OPS_ROOT, "test/unit-test/mock_data")
_PROJECT = config.PROJECT

_logger: logging.Logger = logging.getLogger(__name__)


@pytest.fixture(scope="function")
def aws_credentials():
    """Mocked AWS Credentials for moto."""
    os.environ["AWS_ACCESS_KEY_ID"] = "testing"
    os.environ["AWS_SECRET_ACCESS_KEY"] = "testing"
    os.environ["AWS_SECURITY_TOKEN"] = "testing"
    os.environ["AWS_SESSION_TOKEN"] = "testing"
    os.environ["AWS_DEFAULT_REGION"] = "us-east-1"
    os.environ["MOTO_ACCOUNT_ID"] = "123456789012"


@pytest.fixture(scope="function")
def env_file():
    path = os.path.join(_OPS_ROOT, ".env")

    with open(path, "w") as f:
        f.write("PRIMARY_ACCOUNT=123456789012\n")
        f.write("VPCID=vpc-123456\n")

    yield path

    os.remove(path)


@pytest.fixture(scope="function")
def env_file2():
    path = os.path.join(_OPS_ROOT, ".env.test2")

    with open(path, "w") as f:
        f.write("PRIMARY_ACCOUNT=000000000000\n")
        f.write("SECONDARY_ACCOUNT=123456789012\n")

    yield path

    os.remove(path)


@pytest.fixture(scope="function")
def sts_client(aws_credentials):
    with mock_sts():
        yield boto3_client(service_name="sts", session=None)


@pytest.fixture(scope="function")
def session_manager(sts_client):
    SessionManager._instances = {}
    SessionManager().get_or_create(
        project_name="test",
        region_name="us-east-1",
        toolchain_region="us-east-1",
        enable_reaper=False,
    )


# -------------------------------------------
# -----   Test the sub-command `init`   -----
# -------------------------------------------


# @pytest.mark.init
# def test_init_create_module():
#     module_name = "test-module"
#     expected_module_path = os.path.join(_OPS_ROOT, "modules")

#     # Creates a new module
#     _test_command(sub_command=init, options=["module", "-m", module_name], exit_code=0, return_result=False)

#     # Creates a module that already exist
#     result = _test_command(sub_command=init, options=["module", "-m", module_name], exit_code=1, return_result=True)
#     print(result.exception.args[0])
#     assert result.exception.args[0] == f"The module {module_name} already exists under {expected_module_path}."

#     # Checks if file exists from the project template
#     assert os.path.exists(os.path.join(expected_module_path, module_name, "deployspec.yaml"))


@pytest.mark.init
def test_init_create_group_module(mocker):

    module_name = "test-module"
    group_name = "group"

    mocker.patch("seedfarmer.cli_groups._init_group.minit.create_module_dir", return_value=None)

    # Creates a group and a module within the group
    _test_command(sub_command=init, options=["module", "-g", group_name, "-m", module_name, "--debug"], exit_code=0)


@pytest.mark.init
def test_init_create_project(mocker):

    mocker.patch("seedfarmer.cli_groups._init_group.minit.create_project", return_value=None)
    _test_command(sub_command=init, options=["project"], exit_code=0)


# # -------------------------------------------
# # -----  Test the sub-command `apply`   -----
# # -------------------------------------------


@pytest.mark.version
def test_version():
    _test_command(
        sub_command=version,
        options=None,
        exit_code=0,
        expected_output="seed-farmer",
    )


@pytest.mark.apply
def test_apply_help():
    _test_command(
        sub_command=apply,
        options=["--help"],
        exit_code=0,
        expected_output="Apply manifests to a SeedFarmer managed deployment",
    )


@pytest.mark.apply
def test_apply_debug():
    _test_command(
        sub_command=apply,
        options=["--help", "--debug"],
        exit_code=0,
        expected_output="Apply manifests to a SeedFarmer managed deployment",
    )


@pytest.mark.first
@pytest.mark.apply_working_module
def test_apply_deployment_dry_run(mocker):
    # Deploys a functioning module
    mocker.patch("seedfarmer.__main__.commands.apply", return_value=None)
    deployment_manifest = f"{_TEST_ROOT}/manifests/module-test/deployment.yaml"

    command_output = _test_command(sub_command=apply, options=[deployment_manifest, "--dry-run"], exit_code=0)
    print(command_output)


@pytest.mark.first
@pytest.mark.apply_working_module
def test_apply_deployment(mocker):
    # Deploys a functioning module
    mocker.patch("seedfarmer.__main__.commands.apply", return_value=None)
    deployment_manifest = f"{_TEST_ROOT}/manifests/module-test/deployment.yaml"
    command_output = _test_command(sub_command=apply, options=[deployment_manifest, "--debug"], exit_code=0)


@pytest.mark.first
@pytest.mark.apply_working_module
def test_apply_deployment__env_variables_no_env_file(mocker, env_file):
    # Deploys a functioning module
    mocker.patch("seedfarmer.__main__.commands.apply", return_value=None)
    mocker.patch.dict(os.environ, {}, clear=True)

    deployment_manifest = f"{_TEST_ROOT}/manifests/module-test/deployment.yaml"
    _test_command(sub_command=apply, options=[deployment_manifest, "--debug"], exit_code=0)

    assert os.environ == {"PRIMARY_ACCOUNT": "123456789012", "VPCID": "vpc-123456"}


@pytest.mark.first
@pytest.mark.apply_working_module
def test_apply_deployment__env_variables_single_env_file(mocker, env_file):
    # Deploys a functioning module
    mocker.patch("seedfarmer.__main__.commands.apply", return_value=None)
    mocker.patch.dict(os.environ, {}, clear=True)

    deployment_manifest = f"{_TEST_ROOT}/manifests/module-test/deployment.yaml"
    _test_command(sub_command=apply, options=[deployment_manifest, "--debug", "--env-file", env_file], exit_code=0)

    assert os.environ == {"PRIMARY_ACCOUNT": "123456789012", "VPCID": "vpc-123456"}


@pytest.mark.first
@pytest.mark.apply_working_module
@pytest.mark.parametrize("reverse_order", [False, True])
def test_apply_deployment__env_variables_multiple_env_files(mocker, reverse_order, env_file, env_file2):
    # Deploys a functioning module
    mocker.patch("seedfarmer.__main__.commands.apply", return_value=None)
    mocker.patch.dict(os.environ, {}, clear=True)

    deployment_manifest = f"{_TEST_ROOT}/manifests/module-test/deployment.yaml"

    env_files = [env_file, env_file2]
    if reverse_order:
        env_files = env_files[::-1]

    _test_command(sub_command=apply, options=[deployment_manifest, "--debug", "--env-file",  env_files[0], "--env-file", env_files[1]], exit_code=0)

    assert os.environ == {
        "PRIMARY_ACCOUNT": "123456789012" if reverse_order else "000000000000",
        "SECONDARY_ACCOUNT": "123456789012",
        "VPCID": "vpc-123456",
    }


@pytest.mark.destroy
def test_destroy_deployment_dry_run(mocker):
    # Destroy a functioning module
    mocker.patch("seedfarmer.__main__.commands.destroy", return_value=None)
    command_output = _test_command(sub_command=destroy, options=["myapp", "--debug", "--dry-run"], exit_code=0)


@pytest.mark.destroy
def test_destroy_deployment(mocker):
    # Destroy a functioning module
    mocker.patch("seedfarmer.__main__.commands.destroy", return_value=None)
    command_output = _test_command(sub_command=destroy, options=["myapp", "--debug"], exit_code=0)


@pytest.mark.destroy
def test_destroy__deployment_env_variables_no_env_file(mocker, env_file):
    # Destroy a functioning module
    mocker.patch("seedfarmer.__main__.commands.destroy", return_value=None)
    mocker.patch.dict(os.environ, {}, clear=True)

    _test_command(sub_command=destroy, options=["myapp", "--debug"], exit_code=0)

    assert os.environ == {"PRIMARY_ACCOUNT": "123456789012", "VPCID": "vpc-123456"}


@pytest.mark.destroy
def test_destroy__deployment_env_variables_single_env_file(mocker, env_file):
    # Destroy a functioning module
    mocker.patch("seedfarmer.__main__.commands.destroy", return_value=None)
    mocker.patch.dict(os.environ, {}, clear=True)

    _test_command(sub_command=destroy, options=["myapp", "--debug", "--env-file", env_file], exit_code=0)

    assert os.environ == {"PRIMARY_ACCOUNT": "123456789012", "VPCID": "vpc-123456"}


@pytest.mark.destroy
@pytest.mark.parametrize("reverse_order", [False, True])
def test_destroy__deployment_env_variables_multiple_env_files(mocker, reverse_order, env_file, env_file2):
    # Destroy a functioning module
    mocker.patch("seedfarmer.__main__.commands.destroy", return_value=None)
    mocker.patch.dict(os.environ, {}, clear=True)

    env_files = [env_file, env_file2]
    if reverse_order:
        env_files = env_files[::-1]

    _test_command(sub_command=destroy, options=["myapp", "--debug", "--env-file",  env_files[0], "--env-file", env_files[1]], exit_code=0)

    assert os.environ == {
        "PRIMARY_ACCOUNT": "123456789012" if reverse_order else "000000000000",
        "SECONDARY_ACCOUNT": "123456789012",
        "VPCID": "vpc-123456",
    }


@pytest.mark.bootstrap
def test_bootstrap_toolchain_only(mocker):
    # Bootstrap an Account As Target
    mocker.patch("seedfarmer.commands._bootstrap_commands.bootstrap_target_account", return_value=None)
    mocker.patch("seedfarmer.commands._bootstrap_commands.bootstrap_toolchain_account", return_value=None)
    mocker.patch("seedfarmer.commands._bootstrap_commands.apply_deploy_logic", return_value=None)
    _test_command(
        sub_command=bootstrap,
        options=["toolchain", "--trusted-principal", "arn:aws:iam::123456789012:role/AdminRole", "--debug"],
        exit_code=0, skip_eval=True
    )


@pytest.mark.bootstrap
def test_bootstrap_toolchain_only_with_qualifier(mocker):
    # Bootstrap an Account As Target
    mocker.patch("seedfarmer.commands._bootstrap_commands.bootstrap_target_account", return_value=None)
    mocker.patch("seedfarmer.commands._bootstrap_commands.bootstrap_toolchain_account", return_value=None)
    mocker.patch("seedfarmer.commands._bootstrap_commands.apply_deploy_logic", return_value=None)
    _test_command(
        sub_command=bootstrap,
        options=[
            "toolchain",
            "--trusted-principal",
            "arn:aws:iam::123456789012:role/AdminRole",
            "--qualifier",
            "testit",
            "--debug",
        ],
        exit_code=0,
        skip_eval=True
    )


@pytest.mark.bootstrap
def test_bootstrap_toolchain_only_with_policies_fail(mocker):
    # Bootstrap an Account As Target
    mocker.patch("seedfarmer.commands._bootstrap_commands.bootstrap_target_account", return_value=None)
    mocker.patch("seedfarmer.commands._bootstrap_commands.bootstrap_toolchain_account", return_value=None)
    mocker.patch("seedfarmer.commands._bootstrap_commands.apply_deploy_logic", return_value=None)
    _test_command(
        sub_command=bootstrap,
        options=[
            "toolchain",
            "--trusted-principal",
            "arn:aws:iam::123456789012:role/AdminRole",
            "-pa",
            "arn:aws:iam::aws:policy/AdministratorAccess",
            "--debug",
        ],
        exit_code=1,
        skip_eval=True
    )


@pytest.mark.bootstrap
def test_bootstrap_target_account(mocker):
    # Bootstrap an Account As Target
    mocker.patch("seedfarmer.commands._bootstrap_commands.bootstrap_target_account", return_value=None)
    mocker.patch("seedfarmer.commands._bootstrap_commands.bootstrap_toolchain_account", return_value=None)
    mocker.patch("seedfarmer.commands._bootstrap_commands.apply_deploy_logic", return_value=None)
    _test_command(
        sub_command=bootstrap, options=["target", "--toolchain-account", "123456789012", "--debug"], exit_code=0, skip_eval=True
    )


@pytest.mark.bootstrap
def test_bootstrap_target_account_with_qualifier(mocker):
    # Bootstrap an Account As Target
    mocker.patch("seedfarmer.commands._bootstrap_commands.bootstrap_target_account", return_value=None)
    mocker.patch("seedfarmer.commands._bootstrap_commands.bootstrap_toolchain_account", return_value=None)
    mocker.patch("seedfarmer.commands._bootstrap_commands.apply_deploy_logic", return_value=None)
    _test_command(
        sub_command=bootstrap,
        options=["target", "--toolchain-account", "123456789012", "--qualifier", "testit", "--debug"],
        exit_code=0, skip_eval=True
    )


@pytest.mark.apply
def test_apply_missing_deployment():
    deployment_manifest = f"{_TEST_ROOT}/manifests/test-missing-deployment-manifest/deployment.yaml"

    result = _test_command(sub_command=apply, options=deployment_manifest, exit_code=1, return_result=True)
    assert result.exception.args[1] == "No such file or directory"


@pytest.mark.apply
def test_apply_missing_deployment_group_name():
    deployment_manifest = f"{_TEST_ROOT}/manifests/test-missing-deployment-group-name/deployment.yaml"
    _test_command(sub_command=apply, options=deployment_manifest, exit_code=1, return_result=True)


@pytest.mark.apply
def test_apply_missing_deployment_name():
    deployment_manifest = f"{_TEST_ROOT}/manifests/test-missing-deployment-name/deployment.yaml"

    result = _test_command(sub_command=apply, options=deployment_manifest, exit_code=1, return_result=True)
    assert result.exception.args[0] == "One of 'name' or 'name_generator' is required"


# -------------------------------------------
# -----  Test the sub-command `list`    -----
# -------------------------------------------

# Test Deployspec


@pytest.mark.list
def test_error_messaging():
    import seedfarmer.cli_groups._list_group as lg

    lg._error_messaging(deployment="test-dep", group="test-group", module="test-module")


@pytest.mark.list
def test_list_help():
    _test_command(
        list,
        options=["--help"],
        exit_code=0,
        expected_output="List the relative data (module or deployment",
    )


@pytest.mark.list
@pytest.mark.list_deployspec
@pytest.mark.parametrize("session", [None, boto3_client])
def test_list_deployspec_deployed_error(session, mocker):
    mocker.patch("seedfarmer.cli_groups._list_group.mi.get_deployspec", return_value=None)
    mocker.patch("seedfarmer.cli_groups._list_group.du.generate_deployed_manifest", return_value=None)
    _test_command(
        list,
        options=[
            "deployspec",
            "-d",
            "crazystuff",
            "-g",
            "test-group",
            "-m",
            "test-module",
            "-p",
            "something",
            "--debug",
        ],
        exit_code=1,
    )


@pytest.mark.list
@pytest.mark.list_deployspec
def test_list_deployspec_deployed_none(session_manager, mocker):
    mocker.patch("seedfarmer.cli_groups._list_group.mi.get_deployspec", return_value=None)
    mocker.patch("seedfarmer.cli_groups._list_group.du.generate_deployed_manifest", return_value=None)
    _test_command(
        list,
        options=[
            "deployspec",
            "-d",
            "test",
            "-g",
            "test-group",
            "-m",
            "test-module",
            "-p",
            "myapp",
            "--debug",
        ],
        exit_code=0,
    )


@pytest.mark.list
@pytest.mark.list_deployspec
def test_list_deployspec_missing_session(session_manager, mocker):
    mocker.patch("seedfarmer.cli_groups._list_group.mi.get_deployspec", return_value={"deploy": {"commands": "echo"}})
    mocker.patch(
        "seedfarmer.cli_groups._list_group.du.generate_deployed_manifest",
        return_value=(DeploymentManifest(**mock_manifests.deployment_manifest)),
    )
    mocker.patch(
        "seedfarmer.cli_groups._list_group.mi.get_deployspec", return_value=DeploySpec(**mock_manifests.deployspec)
    )
    _test_command(
        list,
        options=[
            "deployspec",
            "-d",
            "myapp",
            "-g",
            "messsedup",
            "-m",
            "networking",
            "-p",
            "myapp",
            "--debug",
        ],
        exit_code=0,
    )


@pytest.mark.list
@pytest.mark.list_deployspec
def test_list_deployspec(session_manager, mocker):
    mocker.patch("seedfarmer.cli_groups._list_group.mi.get_deployspec", return_value={"deploy": {"commands": "echo"}})
    mocker.patch(
        "seedfarmer.cli_groups._list_group.du.generate_deployed_manifest",
        return_value=(DeploymentManifest(**mock_manifests.deployment_manifest)),
    )
    mocker.patch(
        "seedfarmer.cli_groups._list_group.mi.get_deployspec", return_value=DeploySpec(**mock_manifests.deployspec)
    )
    _test_command(
        list,
        options=[
            "deployspec",
            "-d",
            "myapp",
            "-g",
            "optionals",
            "-m",
            "networking",
            "-p",
            "myapp",
            "--debug",
        ],
        exit_code=0,
    )


# Test list dependencies
@pytest.mark.list
@pytest.mark.list_dependencies
def test_list_dependencies_no_deployed_manifest(session_manager, mocker):
    mocker.patch("seedfarmer.cli_groups._list_group.du.generate_deployed_manifest", return_value=None)
    mocker.patch("seedfarmer.cli_groups._list_group.du.generate_dependency_maps", return_value=None)
    _test_command(
        list,
        options=[
            "dependencies",
            "-d",
            "test",
            "-g",
            "test-group",
            "-m",
            "test-module",
            "-p",
            "myapp",
            "--debug",
        ],
        exit_code=0,
    )


@pytest.mark.list
@pytest.mark.list_dependencies
def test_list_dependencies(session_manager, mocker):
    mocker.patch(
        "seedfarmer.cli_groups._list_group.du.generate_deployed_manifest",
        return_value=(DeploymentManifest(**mock_manifests.deployment_manifest)),
    )
    mocker.patch("seedfarmer.cli_groups._list_group.du.generate_dependency_maps", return_value=None)
    _test_command(
        list,
        options=[
            "dependencies",
            "-d",
            "test",
            "-g",
            "test-group",
            "-m",
            "test-module",
            "-p",
            "myapp",
            "--debug",
        ],
        exit_code=1,
    )


# # Test `list deployments` #


@pytest.mark.list
@pytest.mark.list_deployments
def test_list_deployments_help():
    _test_command(
        sub_command=list,
        options=["deployments", "--help"],
        exit_code=0,
        expected_output="List the deployments in this account",
    )


@pytest.mark.list
@pytest.mark.list_deployments
def test_list_deployments_extra_args():

    _test_command(
        sub_command=list,
        options=[
            "deployments",
            "dsfsd",
        ],
        exit_code=2,
        expected_output="Got unexpected extra argument",
    )


@pytest.mark.list
@pytest.mark.list_deployments
def test_list_deployments(session_manager, mocker):
    mocker.patch("seedfarmer.cli_groups._list_group.mi.get_all_deployments", return_value=None)
    mocker.patch(
        "seedfarmer.cli_groups._list_group.get_sts_identity_info",
        return_value=("1234566789012", "arn:aws", "aws"),
    )
    _test_command(
        sub_command=list,
        options=["deployments", "-p", "myapp", "--debug"],
        exit_code=0,
    )


# # TODO test for no deployments

# # Test `list moduledata` #


@pytest.mark.list
@pytest.mark.list_moduledata
def test_list_moduledata_help():
    _test_command(
        sub_command=list,
        options=["moduledata", "--help"],
        exit_code=0,
        expected_output="Fetch the module metadata",
    )


@pytest.mark.list
@pytest.mark.list_moduledata
def test_list_moduledata_missing_deployment_option():
    _test_command(
        sub_command=list,
        options=[
            "moduledata",
        ],
        exit_code=2,
    )


@pytest.mark.list
@pytest.mark.list_moduledata
def test_list_moduledata_no_dep_manifest(session_manager, mocker):
    mocker.patch("seedfarmer.cli_groups._list_group.du.generate_deployed_manifest", return_value=None)
    _test_command(
        sub_command=list,
        options=[
            "moduledata",
            "-d",
            "test",
            "-g",
            "test-group",
            "-m",
            "test-module",
            "-p",
            "myapp",
            "--debug",
        ],
        exit_code=0,
    )


@pytest.mark.list
@pytest.mark.list_moduledata
def test_list_moduledata(session_manager, mocker):
    mocker.patch(
        "seedfarmer.cli_groups._list_group.du.generate_deployed_manifest",
        return_value=(DeploymentManifest(**mock_manifests.deployment_manifest)),
    )
    mocker.patch(
        "seedfarmer.cli_groups._list_group.mi.get_module_metadata", return_value=mock_manifests.sample_metadata
    )

    _test_command(
        sub_command=list,
        options=[
            "moduledata",
            "-d",
            "test",
            "-g",
            "optionals",
            "-m",
            "networking",
            "-p",
            "myapp",
            "--debug",
        ],
        exit_code=0,
    )


@pytest.mark.list
@pytest.mark.list_moduledata
def test_list_moduledata_export_envs(session_manager, mocker):
    mocker.patch(
        "seedfarmer.cli_groups._list_group.du.generate_deployed_manifest",
        return_value=(DeploymentManifest(**mock_manifests.deployment_manifest)),
    )
    mocker.patch(
        "seedfarmer.cli_groups._list_group.mi.get_module_metadata", return_value=mock_manifests.sample_metadata
    )
    mocker.patch(
        "seedfarmer.cli_groups._list_group.commands.generate_export_env_params", return_value=["export SOMETHING=yo"]
    )

    _test_command(
        sub_command=list,
        options=[
            "moduledata",
            "-d",
            "test",
            "-g",
            "optionals",
            "-m",
            "networking",
            "-p",
            "myapp",
            "--export-local-env",
            "--debug",
        ],
        exit_code=0,
    )


@pytest.mark.list
@pytest.mark.list_moduledata
def test_list_moduledata_mod_not_found(session_manager, mocker):
    mocker.patch(
        "seedfarmer.cli_groups._list_group.du.generate_deployed_manifest",
        return_value=(DeploymentManifest(**mock_manifests.deployment_manifest)),
    )
    mocker.patch(
        "seedfarmer.cli_groups._list_group.mi.get_module_metadata", return_value=mock_manifests.sample_metadata
    )

    _test_command(
        sub_command=list,
        options=[
            "moduledata",
            "-d",
            "test",
            "-g",
            "somethingcrazy",
            "-m",
            "networking",
            "-p",
            "myapp",
            "--debug",
        ],
        exit_code=0,
    )


@pytest.mark.list
@pytest.mark.list_moduledata
def test_list_moduledata_missing_deployment_arg():
    _test_command(sub_command=list, options=["moduledata", "-d"], exit_code=2)


@pytest.mark.list
@pytest.mark.list_moduledata
def test_list_moduledata_missing_group_option():
    _test_command(sub_command=list, options=["moduledata", "-d", "test-deployment"], exit_code=2)


@pytest.mark.list
@pytest.mark.list_moduledata
def test_list_moduledata_missing_group_arg():
    _test_command(sub_command=list, options=["moduledata", "-d", "test-deployment", "-g"], exit_code=2)


@pytest.mark.list
@pytest.mark.list_moduledata
def test_list_moduledata_missing_module_arg():
    _test_command(
        sub_command=list, options=["moduledata", "-d", "test-deployment", "-g", "group-name", "-m"], exit_code=2
    )


@pytest.mark.list
@pytest.mark.list_moduledata
def test_list_moduledata_non_existent_module():
    _test_command(
        sub_command=list,
        options=["moduledata", "-d", "test-deployment", "-g", "group-name", "-m", "module-name"],
        exit_code=1,
        return_result=True,
    )


@pytest.mark.list
@pytest.mark.list_moduledata
def test_list_all_moduledata(session_manager, mocker):
    mocker.patch(
        "seedfarmer.cli_groups._list_group.du.generate_deployed_manifest",
        return_value=(DeploymentManifest(**mock_manifests.deployment_manifest)),
    )
    mocker.patch(
        "seedfarmer.cli_groups._list_group.mi.get_module_metadata", return_value=mock_manifests.sample_metadata
    )

    _test_command(
        sub_command=list,
        options=[
            "allmoduledata",
            "-d",
            "test",
            "-p",
            "myapp",
            "--debug",
        ],
        exit_code=0,
    )


# # Test `list modules` #


@pytest.mark.list
@pytest.mark.list_modules
def test_list_modules_help():
    _test_command(
        sub_command=list,
        options=["modules", "--help"],
        exit_code=0,
        expected_output="List the modules in a deployment",
    )


@pytest.mark.list
@pytest.mark.list_modules
def test_list_modules_incomplete_subcommand():
    _test_command(
        sub_command=list,
        options=[
            "modules",
        ],
        exit_code=2,
    )


@pytest.mark.list
@pytest.mark.list_modules
def test_list_modules_missing_deployment_arg():
    _test_command(sub_command=list, options=["modules", "-d"], exit_code=2)


@pytest.mark.list
@pytest.mark.list_modules
def test_list_modules_non_existent_module():
    _test_command(sub_command=list, options=["modules", "-d", "zzz"], exit_code=1, return_result=True)


@pytest.mark.list
@pytest.mark.list_modules
def test_list_modules(session_manager, mocker):
    mocker.patch(
        "seedfarmer.cli_groups._list_group.du.generate_deployed_manifest",
        return_value=(DeploymentManifest(**mock_manifests.deployment_manifest)),
    )
    _test_command(
        sub_command=list, options=["modules", "-p", "myapp", "-d", "example-test-dev", "--debug"], exit_code=0
    )


@pytest.mark.list
@pytest.mark.list_build_env_params
def test_list_build_env_params(session_manager, mocker):
    mocker.patch(
        "seedfarmer.cli_groups._list_group.du.generate_deployed_manifest",
        return_value=(DeploymentManifest(**mock_manifests.deployment_manifest)),
    )
    _test_command(
        sub_command=list,
        options=[
            "buildparams",
            "-d",
            "test",
            "-g",
            "optionals",
            "-m",
            "networking",
            "--build-id",
            "codebuild:12345",
            "--export-local-env",
            "-p",
            "myapp",
            "--debug",
        ],
        exit_code=0,
    )


@pytest.mark.list
@pytest.mark.list_build_env_params
def test_list_build_env_params_no_dep_manifest(session_manager, mocker):
    mocker.patch("seedfarmer.cli_groups._list_group.du.generate_deployed_manifest", return_value=None)
    _test_command(
        sub_command=list,
        options=[
            "buildparams",
            "-d",
            "test",
            "-g",
            "somethingcrazy",
            "-m",
            "networking",
            "--build-id",
            "codebuild:12345",
            "--export-local-env",
            "-p",
            "myapp",
            "--debug",
        ],
        exit_code=0,
    )


@pytest.mark.list
@pytest.mark.list_build_env_params
def test_list_build_env_params_no_with_params(session_manager, mocker):
    mocker.patch("seedfarmer.cli_groups._list_group.du.generate_deployed_manifest", return_value=None)
    mocker.patch(
        "seedfarmer.cli_groups._list_group.bi.get_build_env_params", return_value={"SEEDFARMER_PARAMETER": "AGreatName"}
    )
    _test_command(
        sub_command=list,
        options=[
            "buildparams",
            "-d",
            "test",
            "-g",
            "optionals",
            "-m",
            "networking",
            "--build-id",
            "codebuild:12345",
            "--export-local-env",
            "-p",
            "myapp",
            "--debug",
        ],
        exit_code=0,
    )


@pytest.mark.list
@pytest.mark.list_build_env_params
def test_list_build_env_params_session_error(session_manager, mocker):
    mocker.patch(
        "seedfarmer.cli_groups._list_group.du.generate_deployed_manifest",
        return_value=(DeploymentManifest(**mock_manifests.deployment_manifest)),
    )
    mocker.patch(
        "seedfarmer.cli_groups._list_group.bi.get_build_env_params", return_value={"SEEDFARMER_PARAMETER": "AGreatName"}
    )
    _test_command(
        sub_command=list,
        options=[
            "buildparams",
            "-d",
            "test",
            "-g",
            "fsafasf",
            "-m",
            "networking",
            "--build-id",
            "codebuild:12345",
            "--export-local-env",
            "-p",
            "myapp",
            "--debug",
        ],
        exit_code=0,
    )


@pytest.mark.list
@pytest.mark.list_build_env_params
def test_list_build_env_params_no_export_param(session_manager, mocker):
    mocker.patch(
        "seedfarmer.cli_groups._list_group.du.generate_deployed_manifest",
        return_value=(DeploymentManifest(**mock_manifests.deployment_manifest)),
    )
    mocker.patch(
        "seedfarmer.cli_groups._list_group.bi.get_build_env_params", return_value={"SEEDFARMER_PARAMETER": "AGreatName"}
    )
    _test_command(
        sub_command=list,
        options=[
            "buildparams",
            "-d",
            "test",
            "-g",
            "optionals",
            "-m",
            "networking",
            "--build-id",
            "codebuild:12345",
            "-p",
            "myapp",
            "--debug",
        ],
        exit_code=0,
    )


@pytest.mark.list
@pytest.mark.list_build_env_params
def test_list_build_env_params_export_param(session_manager, mocker):
    mocker.patch(
        "seedfarmer.cli_groups._list_group.du.generate_deployed_manifest",
        return_value=(DeploymentManifest(**mock_manifests.deployment_manifest)),
    )
    mocker.patch(
        "seedfarmer.cli_groups._list_group.bi.get_build_env_params", return_value={"SEEDFARMER_PARAMETER": "AGreatName"}
    )
    mocker.patch(
        "seedfarmer.cli_groups._list_group.commands.generate_export_raw_env_params",
        return_value={"SEEDFARMER_PARAMETER": "AGreatName"},
    )
    _test_command(
        sub_command=list,
        options=[
            "buildparams",
            "-d",
            "test",
            "-g",
            "optionals",
            "-m",
            "networking",
            "--build-id",
            "codebuild:12345",
            "--export-local-env",
            "-p",
            "myapp",
            "--debug",
        ],
        exit_code=0,
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
def test_remove_moduledata(session_manager, mocker):
    mocker.patch("seedfarmer.cli_groups._list_group.mi.remove_module_info", return_value=None)
    _test_command(
        sub_command=remove,
        options=[
            "moduledata",
            "-d",
            "deployment-name",
            "-g",
            "group-name",
            "-m",
            "mymodule",
            "--target-account-id",
            "123456789012",
            "--target-region",
            "us-east-1" "--debug",
        ],
        exit_code=0,
    )


@pytest.mark.remove
def test_remove_moduledata_bad_account_params(session_manager, mocker):
    mocker.patch("seedfarmer.cli_groups._list_group.mi.remove_module_info", return_value=None)
    _test_command(
        sub_command=remove,
        options=[
            "moduledata",
            "-d",
            "deployment-name",
            "-g",
            "group-name",
            "-m",
            "mymodule",
            "--target-account-id",
            "123456789012",
            "--debug",
        ],
        exit_code=1,
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
        expected_output="Top Level command to support storing module information",
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


@pytest.mark.store
@pytest.mark.store_md5
def test_store_md5_missing_type_arg():
    _test_command(
        sub_command=store,
        options=["md5", "-d", "deployment-name", "-g", "group-name", "-m", "module-name", "-t"],
        exit_code=2,
    )


@pytest.mark.store
@pytest.mark.store_md5
def test_store_md5_deployspec():

    # Store hash to SSM of type spec
    _test_command(
        sub_command=store,
        options=[
            "md5",
            "-d",
            "deployment-name",
            "-g",
            "group-name",
            "-m",
            "module-name",
            "-t",
            "spec" "<<< f4k3h4shmd5",
        ],
        exit_code=0,
    )


@pytest.mark.store
@pytest.mark.store_md5
def test_store_md5_bundle():
    # Store hash to SSM of type bundle
    _test_command(
        sub_command=store,
        options=[
            "md5",
            "-d",
            "deployment-name",
            "-g",
            "group-name",
            "-m",
            "module-name",
            "--type",
            "bundle" "<<< f4k3h4shbund13",
        ],
        exit_code=0,
    )


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


@pytest.mark.store
@pytest.mark.store_moduledata
def test_store_moduledata(mocker, session_manager):
    mocker.patch("seedfarmer.cli_groups._list_group.mi.write_metadata", return_value=None)

    _test_command(
        sub_command=store,
        options=[
            "moduledata",
            "-d",
            "deployment-name",
            "-g",
            "group-name",
            "-m",
            "module-data",
            "--project",
            "myapp",
            "--debug",
        ],
        exit_code=0,
    )


@pytest.mark.store
@pytest.mark.store_moduledata
def test_store_moduledata_with_account(mocker, session_manager):
    mocker.patch("seedfarmer.cli_groups._list_group.mi.write_metadata", return_value=None)

    _test_command(
        sub_command=store,
        options=[
            "moduledata",
            "-d",
            "deployment-name",
            "-g",
            "group-name",
            "-m",
            "module-data",
            "--target-account-id",
            "123456789012",
            "--target-region",
            "us-east-1",
            "--project",
            "myapp",
            "--debug",
        ],
        exit_code=0,
    )


@pytest.mark.store
@pytest.mark.store_deployspec
def test_store_deployspec_missing_deployment_option():
    _test_command(
        sub_command=store,
        options=["deployspec"],
        exit_code=2,
    )


@pytest.mark.store
@pytest.mark.store_deployspec
def test_store_deployspec_deployment_arg():
    _test_command(sub_command=store, options=["deployspec", "-d"], exit_code=2)


@pytest.mark.store
@pytest.mark.store_deployspec
def test_store_deployspec_missing_group_option():
    _test_command(sub_command=store, options=["deployspec", "-d", "deployment-name"], exit_code=2)


@pytest.mark.store
@pytest.mark.store_deployspec
def test_store_deployspec_missing_group_arg():
    _test_command(sub_command=store, options=["deployspec", "-d", "deployment-name", "-g"], exit_code=2)


@pytest.mark.store
@pytest.mark.store_deployspec
def test_store_deployspec_missing_module_option():
    _test_command(sub_command=store, options=["deployspec", "-d", "deployment-name", "-g", "group-name"], exit_code=2)


@pytest.mark.store
@pytest.mark.store_deployspec
def test_store_deployspec_missing_module_arg():
    _test_command(
        sub_command=store, options=["deployspec", "-d", "deployment-name", "-g", "group-name", "-m"], exit_code=2
    )


@pytest.mark.store
@pytest.mark.store_deployspec
def test_store_deployspec_missing_path():
    _test_command(
        sub_command=store,
        options=["deployspec", "-d", "deployment-name", "-g", "group-name", "-m", "module", "--project", "myapp"],
        exit_code=2,
    )


@pytest.mark.store
@pytest.mark.store_deployspec
def test_store_deployspec_missing_acct():
    path = "module/test/test"
    _test_command(
        sub_command=store,
        options=[
            "deployspec",
            "-d",
            "deployment-name",
            "-g",
            "group-name",
            "-m",
            "module",
            "--project",
            "myapp",
            "--path",
            "module/test/test" "--target_region",
            "us-east-1",
            "--debug",
        ],
        exit_code=2,
    )


@pytest.mark.store
@pytest.mark.store_deployspec
@pytest.mark.parametrize("session", [None])
def test_store_deployspec(session_manager, session):

    _test_command(
        sub_command=store,
        options=[
            "deployspec",
            "-d",
            "deployment-name",
            "-g",
            "group-name",
            "-m",
            "module",
            "--project",
            "myapp",
            "--path",
            "module/test/test",
            "--target-account-id",
            "123456789012",
            "--target-region",
            "us-east-1",
            "--debug",
        ],
        exit_code=1,
    )


@pytest.mark.projectpolicy
def test_get_projectpolicy():

    _test_command(sub_command=projectpolicy, options=["synth"], exit_code=0)


@pytest.mark.projectpolicy
def test_get_projectpolicy_debug():

    _test_command(sub_command=projectpolicy, options=["synth", "--debug"], exit_code=0)


@pytest.mark.metadata
def test_metadata_param_value(mocker):
    mocker.patch(
        "seedfarmer.cli_groups._manage_metadata_group.metadata_support.get_parameter_value", return_value="test"
    )
    _test_command(sub_command=metadata, options=["paramvalue", "--suffix", "DEPLOMENT_NAME"], exit_code=0)


@pytest.mark.metadata
def test_metadata_param_value_missing(mocker):
    mocker.patch(
        "seedfarmer.cli_groups._manage_metadata_group.metadata_support.get_parameter_value", return_value="test"
    )
    _test_command(sub_command=metadata, options=["paramvalue"], exit_code=2)


@pytest.mark.metadata
def test_metadata_depmod(mocker):
    mocker.patch("seedfarmer.cli_groups._manage_metadata_group.metadata_support.get_dep_mod_name", return_value="idf")
    _test_command(sub_command=metadata, options=["depmod"], exit_code=0)


@pytest.mark.metadata
def test_metadata_convert(mocker):
    mocker.patch("seedfarmer.cli_groups._manage_metadata_group.metadata_support.convert_cdkexports", return_value="idf")
    _test_command(sub_command=metadata, options=["convert"], exit_code=0)


@pytest.mark.metadata
def test_metadata_convert_file(mocker):
    mocker.patch("seedfarmer.cli_groups._manage_metadata_group.metadata_support.convert_cdkexports", return_value="idf")
    _test_command(sub_command=metadata, options=["convert", "--json-file", "ckd-output.json"], exit_code=0)


@pytest.mark.metadata
def test_metadata_convert_file_jq(mocker):
    mocker.patch("seedfarmer.cli_groups._manage_metadata_group.metadata_support.convert_cdkexports", return_value="idf")
    _test_command(
        sub_command=metadata, options=["convert", "--json-file", "ckd-output.json", "-jq", ".path"], exit_code=0
    )


@pytest.mark.metadata
def test_metadata_add_all_params(mocker):
    mocker.patch("seedfarmer.cli_groups._manage_metadata_group.metadata_support.add_kv_output", return_value=None)
    mocker.patch("seedfarmer.cli_groups._manage_metadata_group.metadata_support.add_json_output", return_value=None)
    _test_command(
        sub_command=metadata,
        options=["add", "--key", "adfdf", "--value", "asdfdsf", "--jsonstring", "adsfsdfa"],
        exit_code=1,
    )


@pytest.mark.metadata
def test_metadata_add_jsonstring(mocker):
    mocker.patch("seedfarmer.cli_groups._manage_metadata_group.metadata_support.add_kv_output", return_value=None)
    mocker.patch("seedfarmer.cli_groups._manage_metadata_group.metadata_support.add_json_output", return_value=None)
    _test_command(sub_command=metadata, options=["add", "--jsonstring", "adsfsdfa"], exit_code=0)


@pytest.mark.metadata
def test_metadata_add_kv(mocker):
    mocker.patch("seedfarmer.cli_groups._manage_metadata_group.metadata_support.add_kv_output", return_value=None)
    mocker.patch("seedfarmer.cli_groups._manage_metadata_group.metadata_support.add_json_output", return_value=None)
    _test_command(sub_command=metadata, options=["add", "--key", "adfdf", "--value", "asdfdsf"], exit_code=0)


@pytest.mark.metadata
def test_metadata_add_kv_missing_key(mocker):
    mocker.patch("seedfarmer.cli_groups._manage_metadata_group.metadata_support.add_kv_output", return_value=None)
    mocker.patch("seedfarmer.cli_groups._manage_metadata_group.metadata_support.add_json_output", return_value=None)
    _test_command(sub_command=metadata, options=["add", "--value", "asdfdsf"], exit_code=1)


@pytest.mark.metadata
def test_metadata_add_kv_missing_value(mocker):
    mocker.patch("seedfarmer.cli_groups._manage_metadata_group.metadata_support.add_kv_output", return_value=None)
    mocker.patch("seedfarmer.cli_groups._manage_metadata_group.metadata_support.add_json_output", return_value=None)
    _test_command(sub_command=metadata, options=["add", "--key", "adfdf"], exit_code=1)
