# Ray Operator

**Category:** Eks  
**Module:** `eks/ray-operator`

## Description

This module runs Ray Operator in AWS EKS Kubernetes cluster. It deploys a KubeRay Operator via [kuberay-helm](https://github.com/ray-project/kuberay-helm).

## Input Parameters

#### Required

- `eks_cluster_name` - Name of the EKS cluster to deploy to
- `eks_cluster_admin_role_arn`- ARN of EKS admin role to authenticate kubectl
- `eks_oidc_arn` - ARN of EKS OIDC provider for IAM roles
- `eks_openid_issuer` - OIDC issuer
- `eks_cluster_endpoint` - EKS cluster endpoint
- `eks_cert_auth_data` - Auth certificate
- `namespace` - Kubernetes namespace name

## Outputs

- `EksServiceAccountName`: Service Account Name.
- `EksServiceAccountRoleArn`: Service Account Role ARN.
- `NamespaceName`: Name of the namespace.

## Source

[View on GitHub](https://github.com/awslabs/aiops-modules/tree/main/modules/eks/ray-operator)
