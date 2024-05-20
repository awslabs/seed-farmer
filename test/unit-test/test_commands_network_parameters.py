import os
from typing import Any, Dict, cast

import pytest
from moto import mock_sts

import seedfarmer.commands._network_parameter_commands as npc
import seedfarmer.errors
from seedfarmer.models.manifests import DeploymentManifest, NetworkMapping
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


deployment_manifest_json = {
    "name": "examples-multi",
    "toolchain_region": "us-east-1",
    "groups": [
        {
            "name": "dummy",
            "path": "manifests/multi/dummy-stuff-iso-module.yaml",
            "modules": [
                {
                    "name": "dummy",
                    "path": "modules/dummy/blank",
                    "parameters": [],
                    "target_account": "primary",
                    "target_region": "us-east-1",
                }
            ],
        }
    ],
    "description": "Testing",
    "target_account_mappings": [
        {
            "alias": "primary",
            "account_id": "123456789012",
            "parameters_global": {},
            "region_mappings": [
                {
                    "region": "us-east-1",
                    "default": True,
                    "parameters_regional": {
                        "dockerCredentialsSecret": "aws-addf-docker-credentials",
                        "vpcId": "vpc-0c4cb9e06c9413222",
                        "privateSubnetIds": ["subnet-0c36d3d5808f67a02", "subnet-00fa1e71cddcf57d3"],
                        "isolatedSubnetIds": ["subnet-XXXXXXXXX", "subnet-XXXXXXXXX"],
                        "securityGroupIds": ["sg-049033188c114a3d2"],
                    },
                    # "network": {
                    #     "vpc_id": {
                    #         "value_from": {
                    #             "env_variable": null,
                    #             "parameter_store": "/idf/testing/vpcid",
                    #             "parameter_value": null
                    #         }
                    #     },
                    #     "private_subnet_ids": {
                    #         "value_from": {
                    #             "env_variable": null,
                    #             "parameter_store": "/idf/testing/privatesubnets",
                    #             "parameter_value": null
                    #         }
                    #     },
                    #     "security_group_ids": {
                    #         "value_from": {
                    #             "env_variable": null,
                    #             "parameter_store": "/idf/testing/securitygroups",
                    #             "parameter_value": null
                    #         }
                    #     }
                    # },
                }
            ],
        }
    ],
}


@pytest.mark.commands
@pytest.mark.commands_parameters
def test_no_values(session_manager, mocker):
    deployment_manifest_json["target_account_mappings"][0]["region_mappings"][0]["network"] = {
        "vpc_id": None,
        "private_subnet_ids": None,
        "security_group_ids": None,
    }
    dep = DeploymentManifest(**deployment_manifest_json)
    dep.validate_and_set_module_defaults()

    target_account_region = dep.target_accounts_regions[0]

    npc.load_network_values(
        cast(NetworkMapping, target_account_region["network"]),
        cast(Dict[str, Any], target_account_region["parameters_regional"]),
        target_account_region["account_id"],
        target_account_region["region"],
    )


@pytest.mark.commands
@pytest.mark.commands_parameters
def test_all_hardcoded_values(session_manager, mocker):
    deployment_manifest_json["target_account_mappings"][0]["region_mappings"][0]["network"] = {
        "vpc_id": "vpc-01e556d052f429282",
        "private_subnet_ids": ["subnet-0c36d3d5808f67a02", "subnet-00fa1e71cddcf57d3"],
        "security_group_ids": ["sg-049033188c114a3d2"],
    }
    dep = DeploymentManifest(**deployment_manifest_json)
    dep.validate_and_set_module_defaults()

    target_account_region = dep.target_accounts_regions[0]

    networkOut = npc.load_network_values(
        cast(NetworkMapping, target_account_region["network"]),
        cast(Dict[str, Any], target_account_region["parameters_regional"]),
        target_account_region["account_id"],
        target_account_region["region"],
    )

    assert "vpc-01e556d052f429282" in networkOut.vpc_id
    assert "subnet-0c36d3d5808f67a02" in networkOut.private_subnet_ids
    assert "sg-049033188c114a3d2" in networkOut.security_group_ids


@pytest.mark.commands
@pytest.mark.commands_parameters
def test_all_from_env(session_manager, mocker):
    os.environ["testenvvpcid"] = "vpc-01e556d052f429282"
    os.environ["testsgs"] = '["sg-049033188c114a3d2"]'
    os.environ["testsubnets"] = '["subnet-0c36d3d5808f67a02","subnet-00fa1e71cddcf57d3"]'
    deployment_manifest_json["target_account_mappings"][0]["region_mappings"][0]["network"] = {
        "vpc_id": {
            "value_from": {
                "env_variable": "testenvvpcid",
            }
        },
        "private_subnet_ids": {
            "value_from": {
                "env_variable": "testsubnets",
            }
        },
        "security_group_ids": {
            "value_from": {
                "env_variable": "testsgs",
            }
        },
    }
    dep = DeploymentManifest(**deployment_manifest_json)
    dep.validate_and_set_module_defaults()

    target_account_region = dep.target_accounts_regions[0]

    networkOut = npc.load_network_values(
        cast(NetworkMapping, target_account_region["network"]),
        cast(Dict[str, Any], target_account_region["parameters_regional"]),
        target_account_region["account_id"],
        target_account_region["region"],
    )

    assert "vpc-01e556d052f429282" in networkOut.vpc_id
    assert "subnet-0c36d3d5808f67a02" in networkOut.private_subnet_ids
    assert "sg-049033188c114a3d2" in networkOut.security_group_ids


@pytest.mark.commands
@pytest.mark.commands_parameters
def test_vpc_from_ssm(session_manager, mocker):
    mocker.patch(
        "seedfarmer.commands._network_parameter_commands.ssm.get_parameter", return_value="vpc-01e556d052f429282"
    )
    deployment_manifest_json["target_account_mappings"][0]["region_mappings"][0]["network"] = {
        "vpc_id": {
            "value_from": {
                "parameter_store": "/idf/testing/vpcid",
            }
        },
        "private_subnet_ids": ["subnet-0c36d3d5808f67a02", "subnet-00fa1e71cddcf57d3"],
        "security_group_ids": ["sg-049033188c114a3d2"],
    }
    dep = DeploymentManifest(**deployment_manifest_json)
    dep.validate_and_set_module_defaults()

    target_account_region = dep.target_accounts_regions[0]

    networkOut = npc.load_network_values(
        cast(NetworkMapping, target_account_region["network"]),
        cast(Dict[str, Any], target_account_region["parameters_regional"]),
        target_account_region["account_id"],
        target_account_region["region"],
    )

    assert "vpc-01e556d052f429282" in networkOut.vpc_id
    assert "subnet-0c36d3d5808f67a02" in networkOut.private_subnet_ids
    assert "sg-049033188c114a3d2" in networkOut.security_group_ids


@pytest.mark.commands
@pytest.mark.commands_parameters
def test_vpc_from_regional_parameter(session_manager, mocker):
    deployment_manifest_json["target_account_mappings"][0]["region_mappings"][0]["network"] = {
        "vpc_id": {
            "value_from": {
                "parameter_value": "vpcId",
            }
        },
        "private_subnet_ids": ["subnet-0c36d3d5808f67a02", "subnet-00fa1e71cddcf57d3"],
        "security_group_ids": ["sg-049033188c114a3d2"],
    }
    dep = DeploymentManifest(**deployment_manifest_json)
    dep.validate_and_set_module_defaults()

    target_account_region = dep.target_accounts_regions[0]

    networkOut = npc.load_network_values(
        cast(NetworkMapping, target_account_region["network"]),
        cast(Dict[str, Any], target_account_region["parameters_regional"]),
        target_account_region["account_id"],
        target_account_region["region"],
    )

    assert "vpc-0c4cb9e06c9413222" in networkOut.vpc_id
    assert "subnet-0c36d3d5808f67a02" in networkOut.private_subnet_ids
    assert "sg-049033188c114a3d2" in networkOut.security_group_ids


@pytest.mark.commands
@pytest.mark.commands_parameters
def test_sgs_subnets_from_ssm(session_manager, mocker):
    mocker.patch(
        "seedfarmer.commands._network_parameter_commands.ssm.get_parameter",
        return_value=["subnet-0c36d3d5808f67a02", "subnet-00fa1e71cddcf57d3"],
    )
    deployment_manifest_json["target_account_mappings"][0]["region_mappings"][0]["network"] = {
        "vpc_id": "vpc-01e556d052f429282",
        "private_subnet_ids": {
            "value_from": {
                "parameter_store": "/idf/testing/subnets",
            }
        },
        "security_group_ids": {
            "value_from": {
                "parameter_store": "/idf/testing/securitygroups",
            }
        },
    }

    dep = DeploymentManifest(**deployment_manifest_json)
    dep.validate_and_set_module_defaults()

    target_account_region = dep.target_accounts_regions[0]

    networkOut = npc.load_network_values(
        cast(NetworkMapping, target_account_region["network"]),
        cast(Dict[str, Any], target_account_region["parameters_regional"]),
        target_account_region["account_id"],
        target_account_region["region"],
    )

    assert "vpc-01e556d052f429282" in networkOut.vpc_id
    assert "subnet-0c36d3d5808f67a02" in networkOut.private_subnet_ids
    assert "subnet-00fa1e71cddcf57d3" in networkOut.security_group_ids


@pytest.mark.commands
@pytest.mark.commands_parameters
def test_sgs_subnets_from_regional_parameter(session_manager, mocker):
    mocker.patch(
        "seedfarmer.commands._network_parameter_commands.ssm.get_parameter",
        return_value=["subnet-0c36d3d5808f67a02", "subnet-00fa1e71cddcf57d3"],
    )
    deployment_manifest_json["target_account_mappings"][0]["region_mappings"][0]["network"] = {
        "vpc_id": "vpc-01e556d052f429282",
        "private_subnet_ids": {
            "value_from": {
                "parameter_value": "privateSubnetIds",
            }
        },
        "security_group_ids": {
            "value_from": {
                "parameter_value": "securityGroupIds",
            }
        },
    }

    dep = DeploymentManifest(**deployment_manifest_json)
    dep.validate_and_set_module_defaults()

    target_account_region = dep.target_accounts_regions[0]

    networkOut = npc.load_network_values(
        cast(NetworkMapping, target_account_region["network"]),
        cast(Dict[str, Any], target_account_region["parameters_regional"]),
        target_account_region["account_id"],
        target_account_region["region"],
    )

    assert "vpc-01e556d052f429282" in networkOut.vpc_id
    assert "subnet-0c36d3d5808f67a02" in networkOut.private_subnet_ids
    assert "sg-049033188c114a3d2" in networkOut.security_group_ids


@pytest.mark.commands
@pytest.mark.commands_parameters
def test_too_many_subgroups(session_manager, mocker):
    os.environ["testsgs"] = (
        '["sg-049033188c114a3d2","sg-049033188c114a3d2","sg-049033188c114a3d2","sg-049033188c114a3d2","sg-049033188c114a3d2","sg-049033188c114a3d2"]'  # noqa: E501
    )

    deployment_manifest_json["target_account_mappings"][0]["region_mappings"][0]["network"] = {
        "vpc_id": "vpc-01e556d052f429282",
        "private_subnet_ids": ["subnet-0c36d3d5808f67a02", "subnet-00fa1e71cddcf57d3"],
        "security_group_ids": {
            "value_from": {
                "env_variable": "testsgs",
            }
        },
    }
    dep = DeploymentManifest(**deployment_manifest_json)
    dep.validate_and_set_module_defaults()

    target_account_region = dep.target_accounts_regions[0]
    with pytest.raises(seedfarmer.errors.InvalidConfigurationError):
        npc.load_network_values(
            cast(NetworkMapping, target_account_region["network"]),
            cast(Dict[str, Any], target_account_region["parameters_regional"]),
            target_account_region["account_id"],
            target_account_region["region"],
        )
