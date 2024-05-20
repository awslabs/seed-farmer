deployment_manifest = {
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
                    "parameters": [{"name": "internet-accessible", "value": True}],
                    "target_account": "primary",
                    "target_region": "us-east-1",
                },
                {
                    "name": "datalake-buckets",
                    "path": "modules/optionals/datalake-buckets",
                    "parameters": [{"name": "encryption-type", "value": "SSE"}],
                    "target_account": "primary",
                    "target_region": "us-east-1",
                },
            ],
        },
        {
            "name": "core",
            "path": "manifests/mlops/core-modules.yaml",
            "modules": [
                {
                    "name": "eks",
                    "path": "modules/core/eks/",
                    "parameters": [
                        {
                            "value_from": {
                                "module_metadata": {"name": "networking", "group": "optionals", "key": "VpcId"},
                            },
                            "name": "vpc-id",
                        },
                        {
                            "value_from": {
                                "module_metadata": {
                                    "name": "networking",
                                    "group": "optionals",
                                    "key": "PrivateSubnetIds",
                                },
                            },
                            "name": "private-subnet-ids",
                        },
                        {"name": "eks-admin-role-name", "value": "Admin"},
                        {
                            "name": "eks-compute",
                            "value": {
                                "eks_nodegroup_config": [
                                    {
                                        "eks_ng_name": "ng1",
                                        "eks_node_quantity": 3,
                                        "eks_node_max_quantity": 6,
                                        "eks_node_min_quantity": 2,
                                        "eks_node_disk_size": 50,
                                        "eks_node_instance_types": ["m5.large"],
                                    }
                                ],
                                "eks_version": 1.23,
                                "eks_node_spot": False,
                            },
                        },
                        {
                            "name": "eks-addons",
                            "value": {
                                "deploy_aws_lb_controller": True,
                                "deploy_external_dns": True,
                                "deploy_aws_ebs_csi": True,
                                "deploy_aws_efs_csi": True,
                                "deploy_aws_fsx_csi": True,
                                "deploy_cluster_autoscaler": True,
                                "deploy_metrics_server": True,
                                "deploy_secretsmanager_csi": True,
                                "deploy_external_secrets": False,
                                "deploy_cloudwatch_container_insights_metrics": True,
                                "deploy_cloudwatch_container_insights_logs": False,
                                "cloudwatch_container_insights_logs_retention_days": 7,
                                "deploy_amp": False,
                                "deploy_grafana_for_amp": False,
                            },
                        },
                    ],
                    "target_account": "primary",
                    "target_region": "us-east-1",
                },
                {
                    "name": "efs",
                    "path": "modules/core/efs",
                    "parameters": [
                        {
                            "value_from": {
                                "module_metadata": {"name": "networking", "group": "optionals", "key": "VpcId"},
                            },
                            "name": "vpc-id",
                        },
                        {"name": "removal-policy", "value": "DESTROY"},
                    ],
                    "target_account": "primary",
                    "target_region": "us-east-1",
                },
            ],
        },
        {
            "name": "platform",
            "path": "manifests/mlops/kf-platform.yaml",
            "modules": [
                {
                    "name": "kubeflow-platform",
                    "path": "modules/mlops/kubeflow-platform/",
                    "parameters": [
                        {
                            "value_from": {
                                "module_metadata": {"name": "eks", "group": "core", "key": "EksClusterMasterRoleArn"},
                            },
                            "name": "EksClusterMasterRoleArn",
                        },
                        {
                            "value_from": {
                                "module_metadata": {"name": "eks", "group": "core", "key": "EksClusterName"},
                            },
                            "name": "EksClusterName",
                        },
                        {"name": "InstallationOption", "value": "kustomize"},
                        {"name": "DeploymentOption", "value": "vanilla"},
                        {"name": "KubeflowReleaseVersion", "value": "v1.6.1"},
                        {"name": "AwsKubeflowBuild", "value": "1.0.0"},
                    ],
                    "target_account": "primary",
                    "target_region": "us-east-1",
                },
                {
                    "name": "efs-on-eks",
                    "path": "modules/integration/efs-on-eks",
                    "parameters": [
                        {
                            "value_from": {
                                "module_metadata": {"name": "eks", "group": "core", "key": "EksClusterAdminRoleArn"},
                            },
                            "name": "eks-cluster-admin-role-arn",
                        },
                        {
                            "value_from": {
                                "module_metadata": {"name": "eks", "group": "core", "key": "EksClusterName"},
                            },
                            "name": "eks-cluster-name",
                        },
                        {
                            "value_from": {
                                "module_metadata": {"name": "eks", "group": "core", "key": "EksOidcArn"},
                            },
                            "name": "eks-oidc-arn",
                        },
                        {
                            "value_from": {
                                "module_metadata": {"name": "eks", "group": "core", "key": "EksClusterSecurityGroupId"},
                            },
                            "name": "eks-cluster-security-group-id",
                        },
                        {
                            "value_from": {
                                "module_metadata": {"name": "efs", "group": "core", "key": "EFSFileSystemId"},
                            },
                            "name": "efs-file-system-id",
                        },
                        {
                            "value_from": {
                                "module_metadata": {"name": "efs", "group": "core", "key": "EFSSecurityGroupId"},
                            },
                            "name": "efs-security-group-id",
                        },
                        {
                            "value_from": {
                                "module_metadata": {"name": "efs", "group": "core", "key": "VpcId"},
                            },
                            "name": "vpc-id",
                        },
                    ],
                    "target_account": "primary",
                    "target_region": "us-east-1",
                },
            ],
        },
        {
            "name": "users",
            "path": "manifests/mlops/kf-users.yaml",
            "modules": [
                {
                    "name": "kubeflow-users",
                    "path": "modules/mlops/kubeflow-users",
                    "parameters": [
                        {
                            "value_from": {
                                "module_metadata": {"name": "eks", "group": "core", "key": "EksClusterAdminRoleArn"},
                            },
                            "name": "EksClusterAdminRoleArn",
                        },
                        {
                            "value_from": {
                                "module_metadata": {"name": "eks", "group": "core", "key": "EksClusterName"},
                            },
                            "name": "EksClusterName",
                        },
                        {
                            "value_from": {
                                "module_metadata": {"name": "eks", "group": "core", "key": "EksOidcArn"},
                            },
                            "name": "EksOidcArn",
                        },
                        {
                            "value_from": {
                                "module_metadata": {
                                    "name": "eks",
                                    "group": "core",
                                    "key": "EksClusterOpenIdConnectIssuer",
                                },
                            },
                            "name": "EksClusterOpenIdConnectIssuer",
                        },
                        {
                            "name": "KubeflowUsers",
                            "value": [
                                {
                                    "policyArn": "arn:aws:iam::aws:policy/AdministratorAccess",
                                    "secret": "addf-dataservice-users-kubeflow-users-kf-dgraeber",
                                }
                            ],
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
            "parameters_global": {"dockerCredentialsSecret": "aws-addf-docker-credentials"},
            "region_mappings": [
                {
                    "region": "us-east-1",
                    "default": True,
                    "parameters_regional": {},
                }
            ],
        }
    ],
}


deployment_manifest_batch_replace = {
    "name": "${DEP_NAME}",
    "toolchain_region": "${REGION}",
    "groups": [
        {
            "name": "optionals",
            "path": "manifests/mlops/optional-modules.yaml",
            "modules": [
                {
                    "name": "networking",
                    "path": "modules/optionals/networking/",
                    "parameters": [{"name": "internet-accessible", "value": True}],
                    "target_account": "primary",
                    "target_region": "us-east-1",
                },
                {
                    "name": "datalake-buckets",
                    "path": "modules/optionals/datalake-buckets",
                    "parameters": [{"name": "encryption-type", "value": "SSE"}],
                    "target_account": "primary",
                    "target_region": "us-east-1",
                },
            ],
        }
    ],
    "target_account_mappings": [
        {
            "alias": "primary",
            "account_id": "${ACCOUNT_ID}",
            "default": True,
            "parameters_global": {"dockerCredentialsSecret": "aws-addf-docker-credentials"},
            "region_mappings": [
                {
                    "region": "us-east-1",
                    "default": True,
                    "parameters_regional": {},
                }
            ],
        }
    ],
}
