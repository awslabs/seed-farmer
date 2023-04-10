import logging
import os
import boto3
import yaml
from typing import cast
import pytest
import seedfarmer.commands._parameter_commands as pc

from seedfarmer.models.manifests import DeploymentManifest, ModuleManifest, ModuleParameter
from seedfarmer.services._service_utils import boto3_client
from seedfarmer.services.session_manager import SessionManager

from moto import mock_sts


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
    SessionManager._instances={}
    SessionManager().get_or_create(
        project_name="test",
        region_name="us-east-1",
        toolchain_region="us-east-1",
        enable_reaper=False,
    )
 
dummy_list_params = {
    "vpc-id":"vpcid-12345",
    "SubnetIds":["subnet-123","subnet-456"],
    "Crazy_param_config":"123"
    
}

deployment_manifest_json = {
    "name": "mlops",
    "toolchain_region": "us-east-1",
    "groups": [
        {
            "name": "optionals",
            "path": "manifests/mlops/optional-modules.yaml",
            "modules": [
                {
                    "name": "networking",
                    "path": "modules/optionals/networking/",
                    "parameters": [
                        {
                            
                            "name": "internet-accessible",
                            "value": True
                        }
                    ],
                    
                    "target_account": "primary",
                    "target_region": "us-east-1",
                    
                },
                {
                    "name": "datalake-buckets",
                    "path": "modules/optionals/datalake-buckets",
                    "parameters": [
                        {
                            
                            "name": "encryption-type",
                            "value": "SSE"
                        }
                    ],
                    
                    "target_account": "primary",
                    "target_region": "us-east-1",                   
                }
            ] 
        },
        
        {
            "name": "core",
            "path": "manifests/mlops/core-modules.yaml",
            "modules": [
                {
                    "name": "efs",
                    "path": "modules/core/efs",
                    "parameters": [
                        {
                            "name": "removal-policy",
                            "value": "DESTROY"
                        },
                        {
                            "name": "vpc-id",
                            "value_from": {
                                "module_metadata": {
                                    "name": "networking",
                                    "group": "optionals",
                                    "key": "VpcId"
                                },
                            },
                        },
                        {
                            "name": "test-secrets-manager",
                            "value_from": {
                                "secretsManager": "my-secret-vpc-id"
                            }
                        },
                        {
                            "name": "test-ssm-store",
                            "value_from": {
                                "parameterStore": "my-ssm-name"
                            }
                        },  
                        {
                            "name": "test-regional-param",
                            "value_from": {
                                "parameterValue": "testRegionalParam"
                            }
                        },                       
                        
                    ],
                    "target_account": "primary",
                    "target_region": "us-east-1",
                    
                }
            ],
            
        },
    ],
    "target_account_mappings": [
        {
            "alias": "primary",
            "account_id": "123456789012",
            "default": True,
            "parameters_global": {
                "dockerCredentialsSecret": "aws-addf-docker-credentials"
            },
            "region_mappings": [
                {
                    "region": "us-east-1",
                    "default": True,
                    "parameters_regional": {
                        "testRegionalParam": "somethingawesomehere"
                    }, 
                }
            ],
            
        }
    ]
}
 
    
@pytest.mark.commands
@pytest.mark.commands_parameters
def test_generate_export_env_params():
    pc.generate_export_env_params(dummy_list_params)


@pytest.mark.commands
@pytest.mark.commands_parameters
def test_generate_export_raw_env_params():
    pc.generate_export_raw_env_params(dummy_list_params)
    
    
@pytest.mark.commands
@pytest.mark.commands_parameters
def test_load_parameter_values(session_manager,mocker):    
    mocker.patch("seedfarmer.commands._parameter_commands.get_module_metadata", 
                 return_value={"IsolatedSubnetIds": [], 
                               "PrivateSubnetIds": ["subnet-0758c0b5ba97e0fc9", "subnet-0dc60fe4557261145"], 
                               "PublicSubnetIds": ["subnet-089b632dada2c71e8", "subnet-0296fff0ba0fa48c0"], 
                               "VpcId": "vpc-01e556d052f429282"}
                 )
    dep = DeploymentManifest(**deployment_manifest_json)
    dep.validate_and_set_module_defaults()
    
    params = pc.load_parameter_values(deployment_name="mlops",
                             deployment_manifest=dep,
                             parameters=dep.groups[1].modules[0].parameters,
                             target_account="123456789012",
                             target_region="us-east-1",
        )
    names = []
    for module_parameter in params:
        names.append(module_parameter.name)
    assert ('removal-policy' in names) == True
    assert ('vpc-id' in names) == True
    assert ('test-secrets-manager' in names) == True
    assert ('test-ssm-store' in names) == True