import json
import logging
import os
from typing import Tuple, cast

import boto3
import mock_data.mock_deployment_manifest_for_destroy as mock_deployment_manifest_for_destroy
import mock_data.mock_deployment_manifest_huge as mock_deployment_manifest_huge
import mock_data.mock_deployspec as mock_deployspec
import mock_data.mock_manifests as mock_manifests
import mock_data.mock_module_info_huge as mock_module_info_huge
import pytest
import yaml
from moto import mock_sts

import seedfarmer.commands._deployment_commands as dc
import seedfarmer.errors
from seedfarmer.models._deploy_spec import DeploySpec
from seedfarmer.models.manifests import (
    DataFile,
    DeploymentManifest,
    ModuleManifest,
    ModuleParameter,
)
from seedfarmer.models.transfer import ModuleDeployObject
from seedfarmer.services._service_utils import boto3_client
from seedfarmer.services.session_manager import SessionManager


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


@pytest.mark.commands
@pytest.mark.commands_deployment
def test_apply_clean(session_manager, mocker):

    mocker.patch("seedfarmer.commands._deployment_commands.write_deployment_manifest", return_value=None)
    mocker.patch("seedfarmer.commands._deployment_commands.prime_target_accounts", return_value=None)
    mocker.patch("seedfarmer.commands._deployment_commands.du.populate_module_info_index", return_value=None)
    mocker.patch("seedfarmer.commands._deployment_commands.du.filter_deploy_destroy", return_value=None)
    mocker.patch("seedfarmer.commands._deployment_commands.write_deployment_manifest", return_value=None)
    mocker.patch("seedfarmer.commands._deployment_commands.du.validate_module_dependencies", return_value=None)
    mocker.patch("seedfarmer.commands._deployment_commands.destroy_deployment", return_value=None)
    mocker.patch("seedfarmer.commands._deployment_commands.deploy_deployment", return_value=None)
    dc.apply(deployment_manifest_path="test/unit-test/mock_data/manifests/module-test/deployment-hc.yaml", dryrun=True)


@pytest.mark.commands
@pytest.mark.commands_deployment
def test_apply_violations(session_manager, mocker):

    mocker.patch("seedfarmer.commands._deployment_commands.write_deployment_manifest", return_value=None)
    mocker.patch("seedfarmer.commands._deployment_commands.prime_target_accounts", return_value=None)
    mocker.patch("seedfarmer.commands._deployment_commands.du.populate_module_info_index", return_value=None)
    mocker.patch("seedfarmer.commands._deployment_commands.du.filter_deploy_destroy", return_value=None)
    mocker.patch("seedfarmer.commands._deployment_commands.write_deployment_manifest", return_value=None)
    mocker.patch(
        "seedfarmer.commands._deployment_commands.du.validate_module_dependencies",
        return_value=[{"module1": ["moduleA", "moduleB"]}],
    )
    with pytest.raises(Exception):
        dc.apply(deployment_manifest_path="test/unit-test/mock_data/manifests/module-test/deployment-hc.yaml")


@pytest.mark.commands
@pytest.mark.commands_deployment
def test_destroy_clean(session_manager, mocker):

    mocker.patch(
        "seedfarmer.commands._deployment_commands.du.generate_deployed_manifest",
        return_value=DeploymentManifest(**mock_deployment_manifest_for_destroy.destroy_manifest),
    )
    mocker.patch("seedfarmer.commands._deployment_commands.destroy_deployment", return_value=None)

    dc.destroy(deployment_name="myapp", dryrun=True, remove_seedkit=False)


@pytest.mark.commands
@pytest.mark.commands_deployment
def test_destroy_not_found(session_manager, mocker):

    mocker.patch(
        "seedfarmer.commands._deployment_commands.du.generate_deployed_manifest",
        return_value=DeploymentManifest(**mock_deployment_manifest_for_destroy.destroy_manifest),
    )
    mocker.patch("seedfarmer.commands._deployment_commands.destroy_deployment", return_value=None)
    mocker.patch(
        "seedfarmer.commands._bootstrap_commands.get_sts_identity_info",
        return_value=("1234566789012", "arn:aws", "aws"),
    )

    dc.destroy(deployment_name="myapp", dryrun=True, remove_seedkit=False)


# @pytest.mark.commands
# @pytest.mark.commands_deployment
# def test_tear_down_target_accounts(session_manager,mocker):
#     mocker.patch("seedfarmer.commands._deployment_commands.tear_down_target_accounts._teardown_accounts", return_value=None)
#     # mocker.patch("seedfarmer.commands._deployment_commands.tear_down_target_accounts._teardown_accounts",
#     #              return_value=None)
#     # with mocker.patch('seedfarmer.commands._deployment_commands.tear_down_target_accounts') as teardown:
#     #     teardown.
### COMMENT....I cannot get the nested threads to mock
#     dc.tear_down_target_accounts(deployment_manifest=DeploymentManifest(**mock_deployment_manifest_for_destroy.destroy_manifest))


@pytest.mark.commands
@pytest.mark.commands_deployment
def test_process_data_files(mocker):
    mocker.patch(
        "seedfarmer.commands._deployment_commands.sf_git.clone_module_repo", return_value=("git", "path", "sdfasfas")
    )
    mocker.patch("seedfarmer.commands._deployment_commands.du.validate_data_files", return_value=[])
    git_path_test = "git::https://github.com/awslabs/idf-modules.git//modules/dummy/blank?ref=release/1.0.0&depth=1"
    datafile_list = []
    datafile_list.append(DataFile(file_path=git_path_test))
    datafile_list.append(DataFile(file_path=""))

    dc._process_data_files(data_files=datafile_list, module_name="test", group_name="test")


@pytest.mark.commands
@pytest.mark.commands_deployment
def test_process_data_files_error(mocker):
    mocker.patch(
        "seedfarmer.commands._deployment_commands.sf_git.clone_module_repo", return_value=("git", "path", "sdfasfas")
    )
    mocker.patch("seedfarmer.commands._deployment_commands.du.validate_data_files", return_value=["hey"])
    git_path_test = "git::https://github.com/awslabs/idf-modules.git//modules/dummy/blank?ref=release/1.0.0&depth=1"
    datafile_list = []
    datafile_list.append(DataFile(file_path=git_path_test))
    datafile_list.append(DataFile(file_path=""))
    with pytest.raises(seedfarmer.errors.InvalidPathError):
        dc._process_data_files(data_files=datafile_list, module_name="test", group_name="test")


@pytest.mark.commands
@pytest.mark.commands_deployment
def test_execute_deploy_invalid_spec(session_manager, mocker):
    mocker.patch("seedfarmer.commands._deployment_commands.load_parameter_values", return_value=None)
    mocker.patch(
        "seedfarmer.commands._deployment_commands.commands.deploy_module_stack",
        return_value=("stack_name", "role_name"),
    )
    mocker.patch("seedfarmer.commands._deployment_commands.get_module_metadata", return_value=None)
    mocker.patch("seedfarmer.commands._deployment_commands.du.prepare_ssm_for_deploy", return_value=None)
    dep = DeploymentManifest(**mock_deployment_manifest_huge.deployment_manifest)
    dep.validate_and_set_module_defaults()
    mdo = ModuleDeployObject(
        deployment_manifest=dep, group_name=dep.groups[0].name, module_name=dep.groups[0].modules[0].name
    )
    with pytest.raises(seedfarmer.errors.InvalidManifestError):
        dc._execute_deploy(mdo)


@pytest.mark.commands
@pytest.mark.commands_deployment
def test_execute_deploy(session_manager, mocker):
    mocker.patch("seedfarmer.commands._deployment_commands.load_parameter_values", return_value=None)
    mocker.patch(
        "seedfarmer.commands._deployment_commands.commands.deploy_module_stack",
        return_value=("stack_name", "role_name"),
    )
    mocker.patch("seedfarmer.commands._deployment_commands.get_module_metadata", return_value=None)
    mocker.patch("seedfarmer.commands._deployment_commands.du.prepare_ssm_for_deploy", return_value=None)
    mocker.patch("seedfarmer.commands._deployment_commands.commands.deploy_module", return_value=None)
    dep = DeploymentManifest(**mock_deployment_manifest_huge.deployment_manifest)
    dep.validate_and_set_module_defaults()
    group = dep.groups[0]
    module_manifest = group.modules[0]
    module_manifest.deploy_spec = DeploySpec(**mock_deployspec.dummy_deployspec)
    mdo = ModuleDeployObject(deployment_manifest=dep, group_name=dep.groups[0].name, module_name=module_manifest.name)
    dc._execute_deploy(mdo)


@pytest.mark.commands
@pytest.mark.commands_deployment
def test_execute_destroy_invalid_spec(session_manager, mocker):
    from seedfarmer.models.deploy_responses import ModuleDeploymentResponse

    dep = DeploymentManifest(**mock_deployment_manifest_huge.deployment_manifest)
    dep.validate_and_set_module_defaults()
    group = dep.groups[0]
    module_manifest = group.modules[0]
    mod_resp = ModuleDeploymentResponse(deployment="myapp", group="optionals", module="metworking", status="SUCCESS")

    mocker.patch("seedfarmer.commands._deployment_commands.get_module_metadata", return_value=None)
    mocker.patch(
        "seedfarmer.commands._deployment_commands.commands.get_module_stack_info",
        return_value=("stack_name", "role_name"),
    )
    mocker.patch("seedfarmer.commands._deployment_commands.commands.destroy_module", return_value=mod_resp)
    mdo = ModuleDeployObject(
        deployment_manifest=dep, group_name=dep.groups[0].name, module_name=module_manifest.name
    )
    with pytest.raises(seedfarmer.errors.InvalidManifestError):
        dc._execute_destroy(mdo)


@pytest.mark.commands
@pytest.mark.commands_deployment
def test_execute_destroy(session_manager, mocker):
    from seedfarmer.models.deploy_responses import ModuleDeploymentResponse

    dep = DeploymentManifest(**mock_deployment_manifest_huge.deployment_manifest)
    dep.validate_and_set_module_defaults()
    group = dep.groups[0]
    module_manifest = group.modules[0]
    mod_resp = ModuleDeploymentResponse(deployment="myapp", group="optionals", module="metworking", status="SUCCESS")
    mocker.patch("seedfarmer.commands._deployment_commands.get_module_metadata", return_value=None)
    mocker.patch(
        "seedfarmer.commands._deployment_commands.commands.get_module_stack_info",
        return_value=("stack_name", "role_name"),
    )
    mocker.patch("seedfarmer.commands._deployment_commands.commands.destroy_module", return_value=mod_resp)
    mocker.patch("seedfarmer.commands._deployment_commands.commands.destroy_module_stack", return_value=None)
    mocker.patch("seedfarmer.commands._deployment_commands.commands.force_manage_policy_attach", return_value=None)
    module_manifest.deploy_spec = DeploySpec(**mock_deployspec.dummy_deployspec)
    mdo = ModuleDeployObject(deployment_manifest=dep, group_name=group.name, module_name=module_manifest.name)
    dc._execute_destroy(mdo)


@pytest.mark.commands
@pytest.mark.commands_deployment
def test_deploy_deployment(session_manager, mocker):
    import hashlib

    mock_hashlib = hashlib.md5(json.dumps({"hey": "yp"}, sort_keys=True).encode("utf-8"))

    import seedfarmer.mgmt.deploy_utils as du

    mocker.patch(
        "seedfarmer.mgmt.deploy_utils.mi.get_parameter_data_cache",
        return_value=mock_module_info_huge.module_index_info_huge,
    )
    module_info_index = du.populate_module_info_index(
        deployment_manifest=DeploymentManifest(**mock_manifests.deployment_manifest)
    )

    dep = DeploymentManifest(**mock_deployment_manifest_huge.deployment_manifest)
    mocker.patch("seedfarmer.commands._deployment_commands.print_manifest_inventory", return_value=None)
    mocker.patch("seedfarmer.commands._deployment_commands.du.validate_group_parameters", return_value=None)
    mocker.patch(
        "seedfarmer.commands._deployment_commands.get_deployspec_path",
        return_value="test/unit-test/mock_data/mock_deployspec.yaml",
    )
    mocker.patch("seedfarmer.commands._deployment_commands.checksum.get_module_md5", return_value="asfsadfsdfa")
    mocker.patch("seedfarmer.commands._deployment_commands.hashlib.md5", return_value=mock_hashlib)

    mocker.patch("seedfarmer.commands._deployment_commands._deploy_validated_deployment", return_value=None)
    mocker.patch("seedfarmer.commands._deployment_commands.du.need_to_build", return_value=None)
    # mocker.patch("seedfarmer.commands._deployment_commands.module_info_index.get_module_info",
    #              return_value=None)
    mocker.patch("seedfarmer.commands._deployment_commands.print_bolded", return_value=None)
    module_upstream_dep = {"Nothing": []}

    dc.deploy_deployment(
        deployment_manifest=dep, module_info_index=module_info_index, module_upstream_dep=module_upstream_dep
    )
