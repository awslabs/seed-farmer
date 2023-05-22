import logging
import os
import boto3
import yaml, json
from typing import cast, Tuple
import pytest
import seedfarmer.commands._module_commands as mc
import seedfarmer.errors

from seedfarmer.models.manifests import DeploymentManifest, ModuleManifest, ModuleParameter
from  seedfarmer.models._deploy_spec import DeploySpec
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


dummy_deployspec = yaml.safe_load(
    """
publishGenericEnvVariables: true
deploy:
  phases:
    install:
      commands:
      - npm install -g aws-cdk@2.20.0
      - pip install -r requirements.txt
    build:
      commands:
      - echo "This Dummy Module does nothing"
destroy:
  phases:
    install:
      commands:
      - npm install -g aws-cdk@2.20.0
      - pip install -r requirements.txt
    build:
      commands:
      - echo 'Look Ma....destroying'                                  
    """)

resp_dict_str = {
            "aws_region": "us-east-1",
            "aws_account_id": "123456789012",
            "codebuild_build_id": "somebuildid",
            "codebuild_log_path": "somelogpath",
        }
 
    
@pytest.mark.commands
@pytest.mark.commands_modules
def test_generate_export_env_params():
    mc._env_vars


@pytest.mark.commands
@pytest.mark.commands_modules
def test_generate_export_raw_env_params():
    pass
    
@pytest.mark.commands
@pytest.mark.commands_modules
def test_deploy_modules(session_manager,mocker):  

    mocker.patch("seedfarmer.commands._module_commands._execute_module_commands", return_value=(json.dumps(resp_dict_str),resp_dict_str))
    dep = DeploymentManifest(**deployment_manifest_json)
    group_name = dep.groups[1].name
    module_manifest = dep.groups[1].modules[0]
    module_manifest.deploy_spec = DeploySpec(**dummy_deployspec)

    mc.deploy_module(deployment_name=dep.name,
                     group_name=group_name,
                     module_manifest=module_manifest,
                     account_id="123456789012",
                     region='us-east-1',
                     parameters=module_manifest.parameters,
                     module_metadata=json.dumps(dummy_list_params),
                     docker_credentials_secret='aws-addf-docker-credentials',
                     permissions_boundary_arn="arn:aws:iam::123456789012:policy/boundary",
                     module_role_name="mlops-optionals-efs",
    )


@pytest.mark.commands
@pytest.mark.commands_modules
def test_deploy_modules_error_deployspec(session_manager,mocker):  

    mocker.patch("seedfarmer.commands._module_commands._execute_module_commands", return_value=(json.dumps(resp_dict_str),resp_dict_str))
    dep = DeploymentManifest(**deployment_manifest_json)
    group_name = dep.groups[1].name
    module_manifest = dep.groups[1].modules[0]
    spec = DeploySpec(**dummy_deployspec)
    spec.deploy=None
    module_manifest.deploy_spec = spec

    with pytest.raises(seedfarmer.errors.InvalidConfigurationError):
        mc.deploy_module(deployment_name=dep.name,
                        group_name=group_name,
                        module_manifest=module_manifest,
                        account_id="123456789012",
                        region='us-east-1',
                        parameters=module_manifest.parameters,
                        module_metadata=json.dumps(dummy_list_params),
                        docker_credentials_secret='aws-addf-docker-credentials',
                        permissions_boundary_arn="arn:aws:iam::123456789012:policy/boundary",
                        module_role_name="mlops-optionals-efs",
        )

@pytest.mark.commands
@pytest.mark.commands_modules
def test_destroy_modules(session_manager,mocker):  

    mocker.patch("seedfarmer.commands._module_commands._execute_module_commands", return_value=(json.dumps(resp_dict_str),resp_dict_str))
    dep = DeploymentManifest(**deployment_manifest_json)
    group_name = dep.groups[1].name
    module_manifest = dep.groups[1].modules[0]
    module_manifest.deploy_spec = DeploySpec(**dummy_deployspec)

    mc.destroy_module(deployment_name=dep.name,
                     group_name=group_name,
                     module_path="module/path/path",
                     module_manifest=module_manifest,
                     account_id="123456789012",
                     region='us-east-1',
                     parameters=module_manifest.parameters,
                     module_metadata=json.dumps(dummy_list_params),
                     module_role_name="mlops-optionals-efs",
    )


@pytest.mark.commands
@pytest.mark.commands_modules
def test_destroy_modules_error_deployspec(session_manager,mocker):  

    mocker.patch("seedfarmer.commands._module_commands._execute_module_commands", return_value=(json.dumps(resp_dict_str),resp_dict_str))
    dep = DeploymentManifest(**deployment_manifest_json)
    group_name = dep.groups[1].name
    module_manifest = dep.groups[1].modules[0]
    
    with pytest.raises(seedfarmer.errors.InvalidConfigurationError):
        mc.destroy_module(deployment_name=dep.name,
                        group_name=group_name,
                        module_path="module/path/path",
                        module_manifest=module_manifest,
                        account_id="123456789012",
                        region='us-east-1',
                        parameters=module_manifest.parameters,
                        module_metadata=json.dumps(dummy_list_params),
                        module_role_name="mlops-optionals-efs",
        )

    
    
@pytest.mark.commands
@pytest.mark.commands_modules
def test_execute_module_commands(session_manager,mocker):
    mocker.patch("seedfarmer.commands._module_commands._execute_module_commands", return_value=(json.dumps(resp_dict_str),resp_dict_str))
    dep = DeploymentManifest(**deployment_manifest_json)
    mc._execute_module_commands(deployment_name=dep.name,
                                group_name=dep.groups[1].name,
                                module_manifest_name=dep.groups[1].modules[0].name,
                                account_id="123456789012",
                                region='us-east-1',
                                metadata_env_variable= ".env"
        )
    
