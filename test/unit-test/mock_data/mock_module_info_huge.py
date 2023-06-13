module_index_info_huge = {
    "/addf/mlops/core/efs/deployspec": {
        "build_type": "BUILD_GENERAL1_SMALL",
        "deploy": {
            "phases": {
                "build": {
                    "commands": [
                        'cdk deploy --require-approval never --progress events --app "python app.py" --outputs-file ./cdk-exports.json',
                        "export ADDF_MODULE_METADATA=$(python -c \"import json; file=open('cdk-exports.json'); print(json.load(file)['addf-${ADDF_DEPLOYMENT_NAME}-${ADDF_MODULE_NAME}']['metadata'])\")",
                    ]
                },
                "install": {"commands": ["npm install -g aws-cdk@2.49.1", "pip install -r requirements.txt"]},
                "post_build": {"commands": []},
                "pre_build": {"commands": []},
            }
        },
        "destroy": {
            "phases": {
                "build": {"commands": ['cdk destroy --force --app "python app.py"']},
                "install": {"commands": ["npm install -g aws-cdk@2.49.1", "pip install -r requirements.txt"]},
                "post_build": {"commands": []},
                "pre_build": {"commands": []},
            }
        },
        "publish_generic_env_variables": False,
    },
    "/addf/mlops/core/efs/manifest": {
        "bundle_md5": "fdabb0934b891dcb913ac412f90f9d7a",
        "deployspec_md5": "0e63e3c67f886a8cff15790485b1ae08",
        "manifest_md5": "259ac4decc9055d838f90baf8722f06b",
        "name": "efs",
        "parameters": [
            {
                "name": "vpc-id",
                "value_from": {
                    "module_metadata": {"group": "optionals", "key": "VpcId", "name": "networking"},
                },
            },
            {
                "name": "removal-policy",
                "value": "DESTROY",
            },
        ],
        "path": "modules/core/efs",
        "target_account": "primary",
        "target_region": "us-east-1",
    },
    "/addf/mlops/core/efs/md5/bundle": {"hash": "fdabb0934b891dcb913ac412f90f9d7a"},
    "/addf/mlops/core/efs/md5/deployspec": {"hash": "0e63e3c67f886a8cff15790485b1ae08"},
    "/addf/mlops/core/efs/md5/manifest": {"hash": "259ac4decc9055d838f90baf8722f06b"},
    "/addf/mlops/core/efs/metadata": {
        "EFSFileSystemArn": "arn:aws:elasticfilesystem:us-east-1:123456789012:file-system/fs-0fe786322349dc734",
        "EFSFileSystemId": "fs-0fe786322349dc734",
        "EFSSecurityGroupId": "sg-0275b1f7fe988476f",
        "VPCId": "vpc-01e556d052f429282",
    },
    "/addf/mlops/core/eks/deployspec": {
        "build_type": "BUILD_GENERAL1_SMALL",
        "deploy": {
            "phases": {
                "build": {
                    "commands": [
                        'cdk deploy --require-approval never --progress events --app "python app.py" --outputs-file ./cdk-exports.json',
                        "export ADDF_MODULE_METADATA=$(python -c \"import json; file=open('cdk-exports.json'); print(json.load(file)['addf-${ADDF_DEPLOYMENT_NAME}-${ADDF_MODULE_NAME}']['metadata'])\")",
                        'export CNI_METRICS_ROLE_NAME=$(echo ${ADDF_MODULE_METADATA} | jq -r ".CNIMetricsHelperRoleName")',
                        "eval $(aws sts assume-role --role-arn arn:aws:iam::${AWS_ACCOUNT_ID}:role/addf-${ADDF_DEPLOYMENT_NAME}-${ADDF_MODULE_NAME}-${AWS_REGION}-masterrole --role-session-name aws-auth-ops | jq -r '.Credentials | \"export AWS_ACCESS_KEY_ID=\\(.AccessKeyId)\\nexport AWS_SECRET_ACCESS_KEY=\\(.SecretAccessKey)\\nexport AWS_SESSION_TOKEN=\\(.SessionToken)\\n\"')",
                        "aws iam get-policy --policy-arn arn:aws:iam::${AWS_ACCOUNT_ID}:policy/AmazonEKSVPCCNIMetricsHelperPolicy || aws iam create-policy --policy-name AmazonEKSVPCCNIMetricsHelperPolicy --policy-document file://addons-iam-policies/cni-metrics-helper-policy.json",
                        "eksctl create iamserviceaccount --name cni-metrics-helper --namespace kube-system --cluster addf-${ADDF_DEPLOYMENT_NAME}-${ADDF_MODULE_NAME}-cluster --role-name ${CNI_METRICS_ROLE_NAME} --attach-policy-arn arn:aws:iam::${AWS_ACCOUNT_ID}:policy/AmazonEKSVPCCNIMetricsHelperPolicy --approve",
                        "curl -o cni-metrics-helper.yaml https://raw.githubusercontent.com/aws/amazon-vpc-cni-k8s/v1.11.0/config/master/cni-metrics-helper.yaml",
                        'sed -i.bak -e "s/us-west-2/$AWS_REGION/" cni-metrics-helper.yaml',
                        "aws eks update-kubeconfig --name addf-${ADDF_DEPLOYMENT_NAME}-${ADDF_MODULE_NAME}-cluster --region ${AWS_REGION}",
                        "kubectl apply -f cni-metrics-helper.yaml",
                        "kubectl rollout restart deployment cni-metrics-helper -n kube-system",
                        'if [ -n "$ADDF_PARAMETER_EKS_ADMIN_ROLE_NAME" ] ; then\n  eksctl get iamidentitymapping --cluster addf-${ADDF_DEPLOYMENT_NAME}-${ADDF_MODULE_NAME}-cluster --arn arn:aws:iam::${AWS_ACCOUNT_ID}:role/${ADDF_PARAMETER_EKS_ADMIN_ROLE_NAME} \\\n  && echo "IAM Identity Mapping already found" \\\n  || eksctl create iamidentitymapping --cluster addf-${ADDF_DEPLOYMENT_NAME}-${ADDF_MODULE_NAME}-cluster --arn arn:aws:iam::${AWS_ACCOUNT_ID}:role/${ADDF_PARAMETER_EKS_ADMIN_ROLE_NAME} --username addf-${ADDF_PARAMETER_EKS_ADMIN_ROLE_NAME} --group system:masters\nfi \n',
                        "unset AWS_ACCESS_KEY_ID && unset AWS_SECRET_ACCESS_KEY && unset AWS_SESSION_TOKEN",
                    ]
                },
                "install": {"commands": ["npm install -g aws-cdk@2.20.0", "pip install -r requirements.txt"]},
                "post_build": {"commands": []},
                "pre_build": {"commands": []},
            }
        },
        "destroy": {
            "phases": {
                "build": {
                    "commands": [
                        "eval $(aws sts assume-role --role-arn arn:aws:iam::${AWS_ACCOUNT_ID}:role/addf-${ADDF_DEPLOYMENT_NAME}-${ADDF_MODULE_NAME}-${AWS_REGION}-masterrole --role-session-name aws-auth-ops | jq -r '.Credentials | \"export AWS_ACCESS_KEY_ID=\\(.AccessKeyId)\\nexport AWS_SECRET_ACCESS_KEY=\\(.SecretAccessKey)\\nexport AWS_SESSION_TOKEN=\\(.SessionToken)\\n\"')",
                        "eksctl delete iamserviceaccount --name cni-metrics-helper --cluster addf-${ADDF_DEPLOYMENT_NAME}-${ADDF_MODULE_NAME}-cluster --namespace kube-system",
                        "unset AWS_ACCESS_KEY_ID && unset AWS_SECRET_ACCESS_KEY && unset AWS_SESSION_TOKEN",
                        'cdk destroy --force --app "python app.py"',
                    ]
                },
                "install": {"commands": ["npm install -g aws-cdk@2.20.0", "pip install -r requirements.txt"]},
                "post_build": {"commands": []},
                "pre_build": {"commands": []},
            }
        },
        "publish_generic_env_variables": False,
    },
    "/addf/mlops/core/eks/manifest": {
        "bundle_md5": "b013f6f640b24eabd246b8f4747ee568",
        "deployspec_md5": "1536833a81c1a855654836b4e74ab289",
        "manifest_md5": "9991c994dcdf37e8f6a8c56c7173ae84",
        "name": "eks",
        "parameters": [
            {
                "name": "vpc-id",
                "value_from": {
                    "module_metadata": {"group": "optionals", "key": "VpcId", "name": "networking"},
                },
            },
            {
                "name": "private-subnet-ids",
                "value_from": {
                    "module_metadata": {"group": "optionals", "key": "PrivateSubnetIds", "name": "networking"},
                },
            },
            {
                "name": "eks-admin-role-name",
                "value": "Admin",
            },
            {
                "name": "eks-compute",
                "value": {
                    "eks_node_spot": False,
                    "eks_nodegroup_config": [
                        {
                            "eks_ng_name": "ng1",
                            "eks_node_disk_size": 50,
                            "eks_node_instance_types": ["m5.large"],
                            "eks_node_max_quantity": 6,
                            "eks_node_min_quantity": 2,
                            "eks_node_quantity": 3,
                        }
                    ],
                    "eks_version": 1.23,
                },
            },
            {
                "name": "eks-addons",
                "value": {
                    "cloudwatch_container_insights_logs_retention_days": 7,
                    "deploy_amp": False,
                    "deploy_aws_ebs_csi": True,
                    "deploy_aws_efs_csi": True,
                    "deploy_aws_fsx_csi": True,
                    "deploy_aws_lb_controller": True,
                    "deploy_cloudwatch_container_insights_logs": False,
                    "deploy_cloudwatch_container_insights_metrics": True,
                    "deploy_cluster_autoscaler": True,
                    "deploy_external_dns": True,
                    "deploy_external_secrets": False,
                    "deploy_grafana_for_amp": False,
                    "deploy_metrics_server": True,
                    "deploy_secretsmanager_csi": True,
                },
            },
        ],
        "path": "modules/core/eks/",
        "target_account": "primary",
        "target_region": "us-east-1",
    },
    "/addf/mlops/core/eks/metadata": {
        "CNIMetricsHelperRoleName": "addf-mlops-core-eks-CNIMetricsHelperRole",
        "EksClusterAdminRoleArn": "arn:aws:iam::123456789012:role/addf-mlops-core-eks-clusterCreationRole2B3B5002-1V1K2PO1IL6I5",
        "EksClusterKubectlRoleArn": "arn:aws:iam::123456789012:role/addf-mlops-core-eks-clusterCreationRole2B3B5002-1V1K2PO1IL6I5",
        "EksClusterMasterRoleArn": "arn:aws:iam::123456789012:role/addf-mlops-core-eks-us-east-1-masterrole",
        "EksClusterName": "addf-mlops-core-eks-cluster",
        "EksClusterOpenIdConnectIssuer": "oidc.eks.us-east-1.amazonaws.com/id/84FF84FA3B953B7AA8EEBD37E9D9C9E5",
        "EksClusterSecurityGroupId": "sg-0b72f310f50faab20",
        "EksOidcArn": "arn:aws:iam::123456789012:oidc-provider/oidc.eks.us-east-1.amazonaws.com/id/84FF84FA3B953B7AA8EEBD37E9D9C9E5",
    },
    "/addf/mlops/manifest": {
        "groups": [
            {"modules": [], "name": "optionals", "path": "manifests/mlops/optional-modules.yaml"},
            {"modules": [], "name": "core", "path": "manifests/mlops/core-modules.yaml"},
            {"modules": [], "name": "platform", "path": "manifests/mlops/kf-platform.yaml"},
            {"modules": [], "name": "users", "path": "manifests/mlops/kf-users.yaml"},
        ],
        "name": "mlops",
        "target_account_mappings": [
            {
                "account_id": "123456789012",
                "alias": "primary",
                "default": True,
                "parameters_global": {"dockerCredentialsSecret": "aws-addf-docker-credentials"},
                "region_mappings": [{"default": True, "parameters_regional": {}, "region": "us-east-1"}],
            }
        ],
        "toolchain_region": "us-east-1",
    },
    "/addf/mlops/core/eks/md5/bundle": {"hash": "b013f6f640b24eabd246b8f4747ee568"},
    "/addf/mlops/core/eks/md5/deployspec": {"hash": "1536833a81c1a855654836b4e74ab289"},
    "/addf/mlops/core/eks/md5/manifest": {"hash": "9991c994dcdf37e8f6a8c56c7173ae84"},
    "/addf/mlops/manifest/deployed": {
        "groups": [
            {"name": "optionals", "path": "manifests/mlops/optional-modules.yaml"},
            {"name": "core", "path": "manifests/mlops/core-modules.yaml"},
            {"name": "platform", "path": "manifests/mlops/kf-platform.yaml"},
            {"name": "users", "path": "manifests/mlops/kf-users.yaml"},
        ],
        "name": "mlops",
        "target_account_mappings": [
            {
                "account_id": "123456789012",
                "alias": "primary",
                "default": True,
                "parameters_global": {"dockerCredentialsSecret": "aws-addf-docker-credentials"},
                "region_mappings": [{"default": True, "parameters_regional": {}, "region": "us-east-1"}],
            }
        ],
        "toolchain_region": "us-east-1",
    },
    "/addf/mlops/optionals/datalake-buckets/deployspec": {
        "build_type": "BUILD_GENERAL1_SMALL",
        "deploy": {
            "phases": {
                "build": {
                    "commands": [
                        'cdk deploy --require-approval never --progress events --app "python app.py" --outputs-file ./cdk-exports.json',
                        "export ADDF_MODULE_METADATA=$(python -c \"import json; file=open('cdk-exports.json'); print(json.load(file)['addf-${ADDF_DEPLOYMENT_NAME}-${ADDF_MODULE_NAME}']['metadata'])\")",
                    ]
                },
                "install": {"commands": ["npm install -g aws-cdk@2.20.0", "pip install -r requirements.txt"]},
                "post_build": {"commands": []},
                "pre_build": {"commands": []},
            }
        },
        "destroy": {
            "phases": {
                "build": {"commands": ['cdk destroy --force --app "python app.py"']},
                "install": {"commands": ["npm install -g aws-cdk@2.20.0", "pip install -r requirements.txt"]},
                "post_build": {"commands": []},
                "pre_build": {"commands": []},
            }
        },
        "publish_generic_env_variables": False,
    },
    "/addf/mlops/optionals/datalake-buckets/manifest": {
        "bundle_md5": "a4e00e858e962dbd7a8436fa2e667498",
        "deployspec_md5": "8ab1e223db6e1e9193438b77e65e7233",
        "manifest_md5": "626d829d21af282c13d9d8ef56997c00",
        "name": "datalake-buckets",
        "parameters": [
            {
                "name": "encryption-type",
                "value": "SSE",
            }
        ],
        "path": "modules/optionals/datalake-buckets",
        "target_account": "primary",
        "target_region": "us-east-1",
    },
    "/addf/mlops/optionals/datalake-buckets/md5/bundle": {"hash": "a4e00e858e962dbd7a8436fa2e667498"},
    "/addf/mlops/optionals/datalake-buckets/md5/deployspec": {"hash": "8ab1e223db6e1e9193438b77e65e7233"},
    "/addf/mlops/optionals/datalake-buckets/md5/manifest": {"hash": "626d829d21af282c13d9d8ef56997c00"},
    "/addf/mlops/optionals/datalake-buckets/metadata": {
        "ArtifactsBucketName": "addf-mlops-artifacts-bucket-074ff5b4",
        "CuratedBucketName": "addf-mlops-curated-bucket-074ff5b4",
        "FullAccessPolicyArn": "arn:aws:iam::123456789012:policy/addf-mlops-optionals-datalake-buckets-us-east-1-123456789012-full-access",
        "IntermediateBucketName": "addf-mlops-intermediate-bucket-074ff5b4",
        "LogsBucketName": "addf-mlops-logs-bucket-074ff5b4",
        "RawBucketName": "addf-mlops-raw-bucket-074ff5b4",
        "ReadOnlyPolicyArn": "arn:aws:iam::123456789012:policy/addf-mlops-optionals-datalake-buckets-us-east-1-123456789012-readonly-access",
    },
    "/addf/mlops/optionals/networking/deployspec": {
        "build_type": "BUILD_GENERAL1_SMALL",
        "deploy": {
            "phases": {
                "build": {
                    "commands": [
                        'cdk deploy --require-approval never --progress events --app "python app.py" --outputs-file ./cdk-exports.json',
                        "export ADDF_MODULE_METADATA=$(python -c \"import json; file=open('cdk-exports.json'); print(json.load(file)['addf-${ADDF_DEPLOYMENT_NAME}-${ADDF_MODULE_NAME}']['metadata'])\")",
                    ]
                },
                "install": {"commands": ["npm install -g aws-cdk@2.20.0", "pip install -r requirements.txt"]},
                "post_build": {"commands": []},
                "pre_build": {"commands": []},
            }
        },
        "destroy": {
            "phases": {
                "build": {"commands": ['cdk destroy --force --app "python app.py"']},
                "install": {"commands": ["npm install -g aws-cdk@2.20.0", "pip install -r requirements.txt"]},
                "post_build": {"commands": []},
                "pre_build": {"commands": []},
            }
        },
        "publish_generic_env_variables": False,
    },
    "/addf/mlops/optionals/networking/manifest": {
        "bundle_md5": "77f951ba81c10c5dcdf0240ec12ad6a3",
        "deployspec_md5": "063a842e34c45de927f20243bafda4bc",
        "manifest_md5": "82a3c7cae1c244c3308ca6619c93b144",
        "name": "networking",
        "parameters": [
            {
                "name": "internet-accessible",
                "value": True,
            }
        ],
        "path": "modules/optionals/networking/",
        "target_account": "primary",
        "target_region": "us-east-1",
    },
    "/addf/mlops/optionals/networking/md5/bundle": {"hash": "77f951ba81c10c5dcdf0240ec12ad6a3"},
    "/addf/mlops/optionals/networking/md5/deployspec": {"hash": "063a842e34c45de927f20243bafda4bc"},
    "/addf/mlops/optionals/networking/md5/manifest": {"hash": "82a3c7cae1c244c3308ca6619c93b144"},
    "/addf/mlops/optionals/networking/metadata": {
        "IsolatedSubnetIds": [],
        "PrivateSubnetIds": ["subnet-0758c0b5ba97e0fc9", "subnet-0dc60fe4557261145"],
        "PublicSubnetIds": ["subnet-089b632dada2c71e8", "subnet-0296fff0ba0fa48c0"],
        "VpcId": "vpc-01e556d052f429282",
    },
    "/addf/mlops/platform/efs-on-eks/deployspec": {
        "build_type": "BUILD_GENERAL1_SMALL",
        "deploy": {
            "phases": {
                "build": {
                    "commands": [
                        'cdk deploy --require-approval never --progress events --app "python app.py" --outputs-file ./cdk-exports.json',
                        "export ADDF_MODULE_METADATA=$(python -c \"import json; file=open('cdk-exports.json'); print(json.load(file)['addf-${ADDF_DEPLOYMENT_NAME}-${ADDF_MODULE_NAME}']['metadata'])\")",
                    ]
                },
                "install": {"commands": ["npm install -g aws-cdk@2.49.1", "pip install -r requirements.txt"]},
                "post_build": {"commands": []},
                "pre_build": {"commands": []},
            }
        },
        "destroy": {
            "phases": {
                "build": {"commands": ['cdk destroy --force --app "python app.py"']},
                "install": {"commands": ["npm install -g aws-cdk@2.49.1", "pip install -r requirements.txt"]},
                "post_build": {"commands": []},
                "pre_build": {"commands": []},
            }
        },
        "publish_generic_env_variables": False,
    },
    "/addf/mlops/platform/efs-on-eks/manifest": {
        "bundle_md5": "3be7473efa2e1699727f16e94d67c9ed",
        "deployspec_md5": "0e63e3c67f886a8cff15790485b1ae08",
        "manifest_md5": "b51b5eee187ceaddff2af366554a6895",
        "name": "efs-on-eks",
        "parameters": [
            {
                "name": "eks-cluster-admin-role-arn",
                "value_from": {
                    "module_metadata": {"group": "core", "key": "EksClusterAdminRoleArn", "name": "eks"},
                },
            },
            {
                "name": "eks-cluster-name",
                "value_from": {
                    "module_metadata": {"group": "core", "key": "EksClusterName", "name": "eks"},
                },
            },
            {
                "name": "eks-oidc-arn",
                "value_from": {
                    "module_metadata": {"group": "core", "key": "EksOidcArn", "name": "eks"},
                },
            },
            {
                "name": "eks-cluster-security-group-id",
                "value_from": {
                    "module_metadata": {"group": "core", "key": "EksClusterSecurityGroupId", "name": "eks"},
                },
            },
            {
                "name": "efs-file-system-id",
                "value_from": {
                    "module_metadata": {"group": "core", "key": "EFSFileSystemId", "name": "efs"},
                },
            },
            {
                "name": "efs-security-group-id",
                "value_from": {
                    "module_metadata": {"group": "core", "key": "EFSSecurityGroupId", "name": "efs"},
                },
            },
            {
                "name": "vpc-id",
                "value_from": {
                    "module_metadata": {"group": "core", "key": "VpcId", "name": "efs"},
                },
            },
        ],
        "path": "modules/integration/efs-on-eks",
        "target_account": "primary",
        "target_region": "us-east-1",
    },
    "/addf/mlops/platform/efs-on-eks/md5/deployspec": {"hash": "0e63e3c67f886a8cff15790485b1ae08"},
    "/addf/mlops/platform/efs-on-eks/metadata": {
        "EFSStorageClassName": "platform-efs-on-eks-efs",
        "EKSClusterName": "addf-mlops-core-eks-cluster",
    },
    "/addf/mlops/platform/efs-on-eks/md5/bundle": {"hash": "3be7473efa2e1699727f16e94d67c9ed"},
    "/addf/mlops/platform/efs-on-eks/md5/manifest": {"hash": "b51b5eee187ceaddff2af366554a6895"},
    "/addf/mlops/platform/kubeflow-platform/deployspec": {
        "build_type": "BUILD_GENERAL1_SMALL",
        "deploy": {
            "phases": {
                "build": {
                    "commands": [
                        "export ROOT_DIR=$(pwd)",
                        "export CLUSTER_NAME=${ADDF_PARAMETER_EKS_CLUSTER_NAME}",
                        "export CLUSTER_REGION=${AWS_DEFAULT_REGION}",
                        "export INSTALLATION_OPTION=${ADDF_PARAMETER_INSTALLATION_OPTION}",
                        "export DEPLOYMENT_OPTION=${ADDF_PARAMETER_DEPLOYMENT_OPTION}",
                        "export KUBEFLOW_RELEASE_VERSION=${ADDF_PARAMETER_KUBEFLOW_RELEASE_VERSION}",
                        "export AWS_KUBEFLOW_BUILD=${ADDF_PARAMETER_AWS_KUBEFLOW_BUILD}",
                        "export AWS_RELEASE_VERSION=${KUBEFLOW_RELEASE_VERSION}-aws-b${AWS_KUBEFLOW_BUILD}",
                        "export KF_POLICY_NAME=addf-${ADDF_DEPLOYMENT_NAME}-${ADDF_MODULE_NAME}-${AWS_DEFAULT_REGION}-kf",
                        "python manage_admin_user.py create ${KF_POLICY_NAME} ${ADDF_PARAMETER_EKS_CLUSTER_MASTER_ROLE_ARN}",
                        "git clone https://github.com/awslabs/kubeflow-manifests.git && cd kubeflow-manifests",
                        "git checkout $AWS_RELEASE_VERSION",
                        "git clone --branch ${KUBEFLOW_RELEASE_VERSION} https://github.com/kubeflow/manifests.git upstream",
                        "git status",
                        "python3.8 -m pip install -r tests/e2e/requirements.txt",
                        "cd $ROOT_DIR/kubeflow-manifests",
                        "eval $(aws sts assume-role --role-arn ${ADDF_PARAMETER_EKS_CLUSTER_MASTER_ROLE_ARN} --role-session-name aws-auth-ops | jq -r '.Credentials | \"export AWS_ACCESS_KEY_ID=\\(.AccessKeyId)\\nexport AWS_SECRET_ACCESS_KEY=\\(.SecretAccessKey)\\nexport AWS_SESSION_TOKEN=\\(.SessionToken)\\n\"')",
                        "aws eks update-kubeconfig --name ${CLUSTER_NAME}",
                        "kubectl get pods -n kube-system",
                        "make deploy-kubeflow INSTALLATION_OPTION=$INSTALLATION_OPTION DEPLOYMENT_OPTION=$DEPLOYMENT_OPTION",
                        "cd $ROOT_DIR/",
                        "bash install_role_irsa.sh",
                        "export PLUGIN=${ADDF_PARAMETER_NVIDIA_DEVICE_PLUGIN_VERSION:=0.13.0}",
                        "helm repo add nvdp https://nvidia.github.io/k8s-device-plugin",
                        "helm repo update",
                        "helm upgrade -i nvdp nvdp/nvidia-device-plugin --version=${PLUGIN} --namespace nvidia-device-plugin --create-namespace --set-file config.map.config=gpu/nvidia-plugin-configmap.yaml || True",
                        "unset AWS_ACCESS_KEY_ID && unset AWS_SECRET_ACCESS_KEY && unset AWS_SESSION_TOKEN",
                        "export ADDF_MODULE_METADATA=\"{'EksClusterName':'${ADDF_PARAMETER_EKS_CLUSTER_NAME}'}\"",
                    ]
                },
                "install": {"commands": ["bash install_build.sh"]},
                "post_build": {"commands": []},
                "pre_build": {"commands": []},
            }
        },
        "destroy": {
            "phases": {
                "build": {
                    "commands": [
                        "eval $(aws sts assume-role --role-arn ${ADDF_PARAMETER_EKS_CLUSTER_MASTER_ROLE_ARN} --role-session-name aws-auth-ops | jq -r '.Credentials | \"export AWS_ACCESS_KEY_ID=\\(.AccessKeyId)\\nexport AWS_SECRET_ACCESS_KEY=\\(.SecretAccessKey)\\nexport AWS_SESSION_TOKEN=\\(.SessionToken)\\n\"')",
                        "export DEP_MOD=${AWS_CODESEEDER_NAME}-${ADDF_DEPLOYMENT_NAME}-${ADDF_MODULE_NAME}-${AWS_DEFAULT_REGION}",
                        "export POLICY_NAME=${DEP_MOD}-policy",
                        "export SA_ROLE_NAME=${DEP_MOD}-sa-role",
                        "export SA_NAME=profiles-controller-service-account",
                        "eksctl delete iamserviceaccount --name ${SA_NAME} --namespace kubeflow --cluster ${ADDF_PARAMETER_EKS_CLUSTER_NAME}",
                        "sleep 10;",
                        "aws iam delete-policy  --policy-arn arn:aws:iam::${AWS_ACCOUNT_ID}:policy/${POLICY_NAME:0:60} || True",
                        "export ROOT_DIR=$(pwd)",
                        "export CLUSTER_NAME=${ADDF_PARAMETER_EKS_CLUSTER_NAME}",
                        "export CLUSTER_REGION=${AWS_DEFAULT_REGION}",
                        "export INSTALLATION_OPTION=${ADDF_PARAMETER_INSTALLATION_OPTION}",
                        "export DEPLOYMENT_OPTION=${ADDF_PARAMETER_DEPLOYMENT_OPTION}",
                        "export KUBEFLOW_RELEASE_VERSION=${ADDF_PARAMETER_KUBEFLOW_RELEASE_VERSION}",
                        "export AWS_KUBEFLOW_BUILD=${ADDF_PARAMETER_AWS_KUBEFLOW_BUILD}",
                        "export AWS_RELEASE_VERSION=${KUBEFLOW_RELEASE_VERSION}-aws-b${AWS_KUBEFLOW_BUILD}",
                        "export KF_POLICY_NAME=addf-${ADDF_DEPLOYMENT_NAME}-${ADDF_MODULE_NAME}-${AWS_DEFAULT_REGION}-kf",
                        "git clone https://github.com/awslabs/kubeflow-manifests.git && cd kubeflow-manifests",
                        "git checkout $AWS_RELEASE_VERSION",
                        "git clone --branch ${KUBEFLOW_RELEASE_VERSION} https://github.com/kubeflow/manifests.git upstream",
                        "git status",
                        "python3.8 -m pip install -r tests/e2e/requirements.txt",
                        "aws eks update-kubeconfig --name ${CLUSTER_NAME}",
                        "helm uninstall nvdp -n nvidia-device-plugin || True",
                        "kubectl get profiles -o json |  jq -r '.items[].metadata.name' >> profiles.out",
                        'for name in $(cat profiles.out); do kubectl patch profile $name --type json -p \'{"metadata":{"finalizers":null}}\' --type=merge; done  || True',
                        "make delete-kubeflow INSTALLATION_OPTION=$INSTALLATION_OPTION DEPLOYMENT_OPTION=$DEPLOYMENT_OPTION",
                        "aws iam detach-role-policy --role-name kf-ack-sm-controller-role-${CLUSTER_NAME} --policy-arn arn:aws:iam::aws:policy/AmazonSageMakerFullAccess || True",
                        "aws iam detach-role-policy --role-name kf-ack-sm-controller-role-${CLUSTER_NAME} --policy-arn arn:aws:iam::${AWS_ACCOUNT_ID}:policy/sm-studio-full-access-${CLUSTER_NAME} || True",
                        "aws iam delete-policy --policy-arn arn:aws:iam::${AWS_ACCOUNT_ID}:policy/sm-studio-full-access-${CLUSTER_NAME} || True",
                        "aws iam delete-role --role-name kf-ack-sm-controller-role-${CLUSTER_NAME} || True",
                        "unset AWS_ACCESS_KEY_ID && unset AWS_SECRET_ACCESS_KEY && unset AWS_SESSION_TOKEN",
                        "cd $ROOT_DIR",
                        "python manage_admin_user.py delete ${KF_POLICY_NAME} ${ADDF_PARAMETER_EKS_CLUSTER_MASTER_ROLE_ARN}",
                    ]
                },
                "install": {"commands": ["bash install_build.sh"]},
                "post_build": {"commands": []},
                "pre_build": {"commands": []},
            }
        },
        "publish_generic_env_variables": False,
    },
    "/addf/mlops/platform/kubeflow-platform/manifest": {
        "bundle_md5": "24618ab8e830d47166984b06f2df5e3f",
        "deployspec_md5": "d105924122e8abcaf7f560bc815ba602",
        "manifest_md5": "38324f55655e2915dbbf3efab77b57e2",
        "name": "kubeflow-platform",
        "parameters": [
            {
                "name": "EksClusterMasterRoleArn",
                "value_from": {
                    "module_metadata": {"group": "core", "key": "EksClusterMasterRoleArn", "name": "eks"},
                },
            },
            {
                "name": "EksClusterName",
                "value_from": {
                    "module_metadata": {"group": "core", "key": "EksClusterName", "name": "eks"},
                },
            },
            {
                "name": "InstallationOption",
                "value": "kustomize",
            },
            {
                "name": "DeploymentOption",
                "value": "vanilla",
            },
            {
                "name": "KubeflowReleaseVersion",
                "value": "v1.6.1",
            },
            {
                "name": "AwsKubeflowBuild",
                "value": "1.0.0",
            },
        ],
        "path": "modules/mlops/kubeflow-platform/",
        "target_account": "primary",
        "target_region": "us-east-1",
    },
    "/addf/mlops/platform/kubeflow-platform/md5/bundle": {"hash": "24618ab8e830d47166984b06f2df5e3f"},
    "/addf/mlops/platform/kubeflow-platform/md5/deployspec": {"hash": "d105924122e8abcaf7f560bc815ba602"},
    "/addf/mlops/platform/kubeflow-platform/md5/manifest": {"hash": "38324f55655e2915dbbf3efab77b57e2"},
    "/addf/mlops/platform/kubeflow-platform/metadata": {"EksClusterName": "addf-mlops-core-eks-cluster"},
    "/addf/mlops/users/kubeflow-users/deployspec": {
        "build_type": "BUILD_GENERAL1_SMALL",
        "deploy": {
            "phases": {
                "build": {
                    "commands": [
                        "if [[ ${ADDF_PARAMETER_KUBEFLOW_USERS} ]]; then\n    cdk deploy --require-approval never --progress events --app \"python app.py\" --outputs-file ./cdk-exports.json;\n    export ADDF_MODULE_METADATA=$(python -c \"import json; file=open('cdk-exports.json'); print(json.load(file)['addf-${ADDF_DEPLOYMENT_NAME}-${ADDF_MODULE_NAME}']['metadata'])\");\n    python manage_kustomize_users.py $ADDF_MODULE_METADATA;\n    eval $(aws sts assume-role --role-arn ${ADDF_PARAMETER_EKS_CLUSTER_ADMIN_ROLE_ARN} --role-session-name aws-auth-ops | jq -r '.Credentials | \"export AWS_ACCESS_KEY_ID=\\(.AccessKeyId)\\nexport AWS_SECRET_ACCESS_KEY=\\(.SecretAccessKey)\\nexport AWS_SESSION_TOKEN=\\(.SessionToken)\\n\"');\n    aws eks update-kubeconfig --name ${ADDF_PARAMETER_EKS_CLUSTER_NAME};\n    kubectl kustomize ./kustomize >> profiles/config-map.yaml;\n    ls -al profiles/;\n    kubectl apply -f profiles/;\n    sleep 10;\n    ls -al poddefaults/;\n    kubectl apply -f poddefaults/; \n    kubectl rollout restart deployment dex -n auth;\n    unset AWS_ACCESS_KEY_ID && unset AWS_SECRET_ACCESS_KEY && unset AWS_SESSION_TOKEN;\nelse\n    echo \"No Kubeflow Users configured....please see the module README regarding the usage of this module\";\nfi;\n"
                    ]
                },
                "install": {
                    "commands": [
                        "npm install -g aws-cdk@2.20.0",
                        "pip install -r requirements.txt",
                        "wget https://github.com/kubernetes-sigs/kustomize/releases/download/kustomize/v3.2.1/kustomize_kustomize.v3.2.1_linux_amd64",
                        "chmod +x kustomize_kustomize.v3.2.1_linux_amd64",
                        "mv kustomize_kustomize.v3.2.1_linux_amd64 /usr/local/bin/kustomize",
                        "kustomize version",
                    ]
                },
                "post_build": {"commands": ['echo "Deploy successful"']},
                "pre_build": {"commands": []},
            }
        },
        "destroy": {
            "phases": {
                "build": {
                    "commands": [
                        'if [[ ${ADDF_PARAMETER_KUBEFLOW_USERS} ]]; then\n  cdk destroy --force --app "python app.py";\nfi;\n'
                    ]
                },
                "install": {"commands": ["npm install -g aws-cdk@2.20.0", "pip install -r requirements.txt"]},
                "post_build": {"commands": []},
                "pre_build": {"commands": []},
            }
        },
        "publish_generic_env_variables": False,
    },
    "/addf/mlops/users/kubeflow-users/metadata": {
        "EksClusterName": "addf-mlops-core-eks-cluster",
        "KubeflowUsers": [
            {
                "policyArn": "arn:aws:iam::aws:policy/AdministratorAccess",
                "roleArn": "arn:aws:iam::123456789012:role/addf-mlops-users-kubeflow-users-us-east-1-0",
                "secret": "addf-dataservice-users-kubeflow-users-kf-dgraeber",
            }
        ],
    },
    "/addf/mlops/users/kubeflow-users/manifest": {
        "bundle_md5": "03c4cce1b534053ab2e9907c00ffef3e",
        "deployspec_md5": "b13401fb18d61964e1e39e2a1474a205",
        "manifest_md5": "d3e04a0cffa57cef83a57fb4f077ad50",
        "name": "kubeflow-users",
        "parameters": [
            {
                "name": "EksClusterAdminRoleArn",
                "value_from": {
                    "module_metadata": {"group": "core", "key": "EksClusterAdminRoleArn", "name": "eks"},
                },
            },
            {
                "name": "EksClusterName",
                "value_from": {
                    "module_metadata": {"group": "core", "key": "EksClusterName", "name": "eks"},
                },
            },
            {
                "name": "EksOidcArn",
                "value_from": {
                    "module_metadata": {"group": "core", "key": "EksOidcArn", "name": "eks"},
                },
            },
            {
                "name": "EksClusterOpenIdConnectIssuer",
                "value_from": {
                    "module_metadata": {"group": "core", "key": "EksClusterOpenIdConnectIssuer", "name": "eks"},
                },
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
        "path": "modules/mlops/kubeflow-users",
        "target_account": "primary",
        "target_region": "us-east-1",
    },
    "/addf/mlops/users/kubeflow-users/md5/bundle": {"hash": "03c4cce1b534053ab2e9907c00ffef3e"},
    "/addf/mlops/users/kubeflow-users/md5/deployspec": {"hash": "b13401fb18d61964e1e39e2a1474a205"},
    "/addf/mlops/users/kubeflow-users/md5/manifest": {"hash": "d3e04a0cffa57cef83a57fb4f077ad50"},
}
