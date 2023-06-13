import yaml

deployment_manifest = yaml.safe_load(
    """
{
    "name": "myapp",
    "name_generator": null,
    "toolchain_region": "us-east-1",
    "groups": [
        {
            "name": "optionals",
            "path": "manifests/mlops/optional-modules.yaml",
            "modules": [
                {
                    "name": "networking",
                    "path": "modules/optionals/networking/",
                    "bundle_md5": null,
                    "manifest_md5": null,
                    "deployspec_md5": null,
                    "parameters": [
                        {
                            "value_from": null,
                            "name": "internet-accessible",
                            "value": true
                        }
                    ],
                    "deploy_spec": null,
                    "target_account": "primary",
                    "target_region": "us-east-1",
                    "codebuild_image": null
                },
                {
                    "name": "datalake-buckets",
                    "path": "modules/optionals/datalake-buckets",
                    "bundle_md5": null,
                    "manifest_md5": null,
                    "deployspec_md5": null,
                    "parameters": [
                        {
                            "value_from": null,
                            "name": "encryption-type",
                            "value": "SSE"
                        }
                    ],
                    "deploy_spec": null,
                    "target_account": "primary",
                    "target_region": "us-east-1",
                    "codebuild_image": null
                }
            ],
            "concurrency": null
        },
        {
            "name": "core",
            "path": "manifests/mlops/core-modules.yaml",
            "modules": [
                {
                    "name": "eks",
                    "path": "modules/core/eks/",
                    "bundle_md5": null,
                    "manifest_md5": null,
                    "deployspec_md5": null,
                    "parameters": [
                        {
                            "value_from": {
                                "module_metadata": {
                                    "name": "networking",
                                    "group": "optionals",
                                    "key": "VpcId"
                                },
                                "env_variable": null,
                                "parameter_store": null,
                                "secrets_manager": null,
                                "parameter_value": null
                            },
                            "name": "vpc-id",
                            "value": null
                        },
                        {
                            "value_from": {
                                "module_metadata": {
                                    "name": "networking",
                                    "group": "optionals",
                                    "key": "PrivateSubnetIds"
                                },
                                "env_variable": null,
                                "parameter_store": null,
                                "secrets_manager": null,
                                "parameter_value": null
                            },
                            "name": "private-subnet-ids",
                            "value": null
                        },
                        {
                            "value_from": null,
                            "name": "eks-admin-role-name",
                            "value": "Admin"
                        },
                        {
                            "value_from": null,
                            "name": "eks-compute",
                            "value": {
                                "eks_nodegroup_config": [
                                    {
                                        "eks_ng_name": "ng1",
                                        "eks_node_quantity": 3,
                                        "eks_node_max_quantity": 6,
                                        "eks_node_min_quantity": 2,
                                        "eks_node_disk_size": 50,
                                        "eks_node_instance_types": [
                                            "m5.large"
                                        ]
                                    }
                                ],
                                "eks_version": 1.23,
                                "eks_node_spot": false
                            }
                        },
                        {
                            "value_from": null,
                            "name": "eks-addons",
                            "value": {
                                "deploy_aws_lb_controller": true,
                                "deploy_external_dns": true,
                                "deploy_aws_ebs_csi": true,
                                "deploy_aws_efs_csi": true,
                                "deploy_aws_fsx_csi": true,
                                "deploy_cluster_autoscaler": true,
                                "deploy_metrics_server": true,
                                "deploy_secretsmanager_csi": true,
                                "deploy_external_secrets": false,
                                "deploy_cloudwatch_container_insights_metrics": true,
                                "deploy_cloudwatch_container_insights_logs": false,
                                "cloudwatch_container_insights_logs_retention_days": 7,
                                "deploy_amp": false,
                                "deploy_grafana_for_amp": false
                            }
                        }
                    ],
                    "deploy_spec": null,
                    "target_account": "primary",
                    "target_region": "us-east-1",
                    "codebuild_image": null
                },
                {
                    "name": "efs",
                    "path": "modules/core/efs",
                    "bundle_md5": null,
                    "manifest_md5": null,
                    "deployspec_md5": null,
                    "parameters": [
                        {
                            "value_from": {
                                "module_metadata": {
                                    "name": "networking",
                                    "group": "optionals",
                                    "key": "VpcId"
                                },
                                "env_variable": null,
                                "parameter_store": null,
                                "secrets_manager": null,
                                "parameter_value": null
                            },
                            "name": "vpc-id",
                            "value": null
                        },
                        {
                            "value_from": null,
                            "name": "removal-policy",
                            "value": "DESTROY"
                        }
                    ],
                    "deploy_spec": null,
                    "target_account": "primary",
                    "target_region": "us-east-1",
                    "codebuild_image": null
                }
            ],
            "concurrency": null
        },
        {
            "name": "platform",
            "path": "manifests/mlops/kf-platform.yaml",
            "modules": [
                {
                    "name": "kubeflow-platform",
                    "path": "modules/mlops/kubeflow-platform/",
                    "bundle_md5": null,
                    "manifest_md5": null,
                    "deployspec_md5": null,
                    "parameters": [
                        {
                            "value_from": {
                                "module_metadata": {
                                    "name": "eks",
                                    "group": "core",
                                    "key": "EksClusterMasterRoleArn"
                                },
                                "env_variable": null,
                                "parameter_store": null,
                                "secrets_manager": null,
                                "parameter_value": null
                            },
                            "name": "EksClusterMasterRoleArn",
                            "value": null
                        },
                        {
                            "value_from": {
                                "module_metadata": {
                                    "name": "eks",
                                    "group": "core",
                                    "key": "EksClusterName"
                                },
                                "env_variable": null,
                                "parameter_store": null,
                                "secrets_manager": null,
                                "parameter_value": null
                            },
                            "name": "EksClusterName",
                            "value": null
                        },
                        {
                            "value_from": null,
                            "name": "InstallationOption",
                            "value": "kustomize"
                        },
                        {
                            "value_from": null,
                            "name": "DeploymentOption",
                            "value": "vanilla"
                        },
                        {
                            "value_from": null,
                            "name": "KubeflowReleaseVersion",
                            "value": "v1.6.1"
                        },
                        {
                            "value_from": null,
                            "name": "AwsKubeflowBuild",
                            "value": "1.0.0"
                        }
                    ],
                    "deploy_spec": null,
                    "target_account": "primary",
                    "target_region": "us-east-1",
                    "codebuild_image": null
                },
                {
                    "name": "efs-on-eks",
                    "path": "modules/integration/efs-on-eks",
                    "bundle_md5": null,
                    "manifest_md5": null,
                    "deployspec_md5": null,
                    "parameters": [
                        {
                            "value_from": {
                                "module_metadata": {
                                    "name": "eks",
                                    "group": "core",
                                    "key": "EksClusterAdminRoleArn"
                                },
                                "env_variable": null,
                                "parameter_store": null,
                                "secrets_manager": null,
                                "parameter_value": null
                            },
                            "name": "eks-cluster-admin-role-arn",
                            "value": null
                        },
                        {
                            "value_from": {
                                "module_metadata": {
                                    "name": "eks",
                                    "group": "core",
                                    "key": "EksClusterName"
                                },
                                "env_variable": null,
                                "parameter_store": null,
                                "secrets_manager": null,
                                "parameter_value": null
                            },
                            "name": "eks-cluster-name",
                            "value": null
                        },
                        {
                            "value_from": {
                                "module_metadata": {
                                    "name": "eks",
                                    "group": "core",
                                    "key": "EksOidcArn"
                                },
                                "env_variable": null,
                                "parameter_store": null,
                                "secrets_manager": null,
                                "parameter_value": null
                            },
                            "name": "eks-oidc-arn",
                            "value": null
                        },
                        {
                            "value_from": {
                                "module_metadata": {
                                    "name": "eks",
                                    "group": "core",
                                    "key": "EksClusterSecurityGroupId"
                                },
                                "env_variable": null,
                                "parameter_store": null,
                                "secrets_manager": null,
                                "parameter_value": null
                            },
                            "name": "eks-cluster-security-group-id",
                            "value": null
                        },
                        {
                            "value_from": {
                                "module_metadata": {
                                    "name": "efs",
                                    "group": "core",
                                    "key": "EFSFileSystemId"
                                },
                                "env_variable": null,
                                "parameter_store": null,
                                "secrets_manager": null,
                                "parameter_value": null
                            },
                            "name": "efs-file-system-id",
                            "value": null
                        },
                        {
                            "value_from": {
                                "module_metadata": {
                                    "name": "efs",
                                    "group": "core",
                                    "key": "EFSSecurityGroupId"
                                },
                                "env_variable": null,
                                "parameter_store": null,
                                "secrets_manager": null,
                                "parameter_value": null
                            },
                            "name": "efs-security-group-id",
                            "value": null
                        },
                        {
                            "value_from": {
                                "module_metadata": {
                                    "name": "efs",
                                    "group": "core",
                                    "key": "VpcId"
                                },
                                "env_variable": null,
                                "parameter_store": null,
                                "secrets_manager": null,
                                "parameter_value": null
                            },
                            "name": "vpc-id",
                            "value": null
                        }
                    ],
                    "deploy_spec": null,
                    "target_account": "primary",
                    "target_region": "us-east-1",
                    "codebuild_image": null
                }
            ],
            "concurrency": null
        },
        {
            "name": "users",
            "path": "manifests/mlops/kf-users.yaml",
            "modules": [
                {
                    "name": "kubeflow-users",
                    "path": "modules/mlops/kubeflow-users",
                    "bundle_md5": null,
                    "manifest_md5": null,
                    "deployspec_md5": null,
                    "parameters": [
                        {
                            "value_from": {
                                "module_metadata": {
                                    "name": "eks",
                                    "group": "core",
                                    "key": "EksClusterAdminRoleArn"
                                },
                                "env_variable": null,
                                "parameter_store": null,
                                "secrets_manager": null,
                                "parameter_value": null
                            },
                            "name": "EksClusterAdminRoleArn",
                            "value": null
                        },
                        {
                            "value_from": {
                                "module_metadata": {
                                    "name": "eks",
                                    "group": "core",
                                    "key": "EksClusterName"
                                },
                                "env_variable": null,
                                "parameter_store": null,
                                "secrets_manager": null,
                                "parameter_value": null
                            },
                            "name": "EksClusterName",
                            "value": null
                        },
                        {
                            "value_from": {
                                "module_metadata": {
                                    "name": "eks",
                                    "group": "core",
                                    "key": "EksOidcArn"
                                },
                                "env_variable": null,
                                "parameter_store": null,
                                "secrets_manager": null,
                                "parameter_value": null
                            },
                            "name": "EksOidcArn",
                            "value": null
                        },
                        {
                            "value_from": {
                                "module_metadata": {
                                    "name": "eks",
                                    "group": "core",
                                    "key": "EksClusterOpenIdConnectIssuer"
                                },
                                "env_variable": null,
                                "parameter_store": null,
                                "secrets_manager": null,
                                "parameter_value": null
                            },
                            "name": "EksClusterOpenIdConnectIssuer",
                            "value": null
                        }
                    ],
                    "deploy_spec": null,
                    "target_account": "primary",
                    "target_region": "us-east-1",
                    "codebuild_image": null
                }
            ],
            "concurrency": null
        }
    ],
    "description": null,
    "target_account_mappings": [
        {
            "alias": "primary",
            "account_id": "123456789012",
            "default": true,
            "parameters_global": {
                "dockerCredentialsSecret": "aws-addf-docker-credentials"
            },
            "region_mappings": [
                {
                    "region": "us-east-1",
                    "default": true,
                    "parameters_regional": {},
                    "network": null,
                    "codebuild_image": null
                }
            ],
            "codebuild_image": null
        }
    ]
}
    """
)

modules_manifest_duplicate = yaml.safe_load(
    """
{
    "name": "core",
    "path": "manifests/mlops/core-modules.yaml",
    "modules": [
        {
            "name": "eks",
            "path": "modules/core/eks/",
            "bundle_md5": null,
            "manifest_md5": null,
            "deployspec_md5": null,
            "parameters": [
                {
                    "value_from": {
                        "module_metadata": {
                            "name": "networking",
                            "group": "optionals",
                            "key": "VpcId"
                        },
                        "env_variable": null,
                        "parameter_store": null,
                        "secrets_manager": null,
                        "parameter_value": null
                    },
                    "name": "vpc-id",
                    "value": null
                },
                {
                    "value_from": {
                        "module_metadata": {
                            "name": "networking",
                            "group": "optionals",
                            "key": "PrivateSubnetIds"
                        },
                        "env_variable": null,
                        "parameter_store": null,
                        "secrets_manager": null,
                        "parameter_value": null
                    },
                    "name": "private-subnet-ids",
                    "value": null
                },
                {
                    "value_from": null,
                    "name": "eks-admin-role-name",
                    "value": "Admin"
                },
                {
                    "value_from": null,
                    "name": "eks-compute",
                    "value": {
                        "eks_nodegroup_config": [
                            {
                                "eks_ng_name": "ng1",
                                "eks_node_quantity": 3,
                                "eks_node_max_quantity": 6,
                                "eks_node_min_quantity": 2,
                                "eks_node_disk_size": 50,
                                "eks_node_instance_types": [
                                    "m5.large"
                                ]
                            }
                        ],
                        "eks_version": 1.23,
                        "eks_node_spot": false
                    }
                }
            ],
            "deploy_spec": null,
            "target_account": "primary",
            "target_region": "us-east-1",
            "codebuild_image": null
        },
        {
            "name": "efs",
            "path": "modules/core/efs",
            "bundle_md5": null,
            "manifest_md5": null,
            "deployspec_md5": null,
            "parameters": [
                {
                    "value_from": {
                        "module_metadata": {
                            "name": "eks",
                            "group": "core",
                            "key": "dummy"
                        },
                        "env_variable": null,
                        "parameter_store": null,
                        "secrets_manager": null,
                        "parameter_value": null
                    },
                    "name": "vpc-id",
                    "value": null
                },
                {
                    "value_from": null,
                    "name": "removal-policy",
                    "value": "DESTROY"
                }
            ],
            "deploy_spec": null,
            "target_account": "primary",
            "target_region": "us-east-1",
            "codebuild_image": null
        }
    ],
    "concurrency": null
}

    """
)

modules_manifest = yaml.safe_load(
    """
{
    "name": "core",
    "path": "manifests/mlops/core-modules.yaml",
    "modules": [
        {
            "name": "eks",
            "path": "modules/core/eks/",
            "bundle_md5": null,
            "manifest_md5": null,
            "deployspec_md5": null,
            "parameters": [
                {
                    "value_from": {
                        "module_metadata": {
                            "name": "networking",
                            "group": "optionals",
                            "key": "VpcId"
                        },
                        "env_variable": null,
                        "parameter_store": null,
                        "secrets_manager": null,
                        "parameter_value": null
                    },
                    "name": "vpc-id",
                    "value": null
                },
                {
                    "value_from": {
                        "module_metadata": {
                            "name": "networking",
                            "group": "optionals",
                            "key": "PrivateSubnetIds"
                        },
                        "env_variable": null,
                        "parameter_store": null,
                        "secrets_manager": null,
                        "parameter_value": null
                    },
                    "name": "private-subnet-ids",
                    "value": null
                },
                {
                    "value_from": null,
                    "name": "eks-admin-role-name",
                    "value": "Admin"
                },
                {
                    "value_from": null,
                    "name": "eks-compute",
                    "value": {
                        "eks_nodegroup_config": [
                            {
                                "eks_ng_name": "ng1",
                                "eks_node_quantity": 3,
                                "eks_node_max_quantity": 6,
                                "eks_node_min_quantity": 2,
                                "eks_node_disk_size": 50,
                                "eks_node_instance_types": [
                                    "m5.large"
                                ]
                            }
                        ],
                        "eks_version": 1.23,
                        "eks_node_spot": false
                    }
                }
            ],
            "deploy_spec": null,
            "target_account": "primary",
            "target_region": "us-east-1",
            "codebuild_image": null
        },
        {
            "name": "efs",
            "path": "modules/core/efs",
            "bundle_md5": null,
            "manifest_md5": null,
            "deployspec_md5": null,
            "parameters": [
                {
                    "value_from": null,
                    "name": "vpc-id",
                    "value": null
                },
                {
                    "value_from": null,
                    "name": "removal-policy",
                    "value": "DESTROY"
                }
            ],
            "deploy_spec": null,
            "target_account": "primary",
            "target_region": "us-east-1",
            "codebuild_image": null
        }
    ],
    "concurrency": null
}

    """
)

deployspec = yaml.safe_load(
    """
publishGenericEnvVariables: true
deploy:
  phases:
    install:
      commands:
      # Install whatever additional build libraries
      - npm install -g aws-cdk@2.20.0
      - pip install -r requirements.txt
    build:
      commands:
      - echo "This Dummy Module does nothing"
destroy:
  phases:
    install:
      commands:
      # Install whatever additional build libraries
      - npm install -g aws-cdk@2.20.0
      - pip install -r requirements.txt
    build:
      commands:
      # execute the CDK
      - echo 'Look Ma....destroying'
                             """
)

sample_metadata = {
    "GlueDBName": "addl-cicd-core-metadata-storage-vsidata",
    "RosbagBagFilePartitionKey": "bag_file_prefix",
    "RosbagBagFileTable": "addl-cicd-core-metadata-storage-Rosbag-BagFile-Metadata",
}
