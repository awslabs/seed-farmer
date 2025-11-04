# Ray Cluster

**Category:** Eks  
**Module:** `eks/ray-cluster`

## Description

This module creates a Ray cluster in AWS EKS Kubernetes cluster. It deploys a RayClsuter via [kuberay-helm](https://github.com/ray-project/kuberay-helm) and a ClusterIP service. Requires a RayOperator.

## Input Parameters

#### Required

- `eks_cluster_name` - Name of the EKS cluster to deploy to
- `eks_cluster_admin_role_arn`- ARN of EKS admin role to authenticate kubectl
- `eks_oidc_arn` - ARN of EKS OIDC provider for IAM roles
- `namespace` - Kubernetes namespace name
- `service_account_name` - Service account name

## Source

[View on GitHub](https://github.com/awslabs/aiops-modules/tree/main/modules/eks/ray-cluster)
