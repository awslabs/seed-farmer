# Ray Orchestrator

**Category:** Eks  
**Module:** `eks/ray-orchestrator`

## Description

This module orchestrates submission of a Ray training job to the Ray Cluster and an inference job using AWS Step Functions.

## Input Parameters

#### Required

- `namespace` - Kubernetes namespace name
- `eks_cluster_admin_role_arn`- ARN of EKS admin role to authenticate kubectl
- `eks_handler_role_arn`- ARN of EKS admin role to authenticate kubectl
- `eks_cluster_name` - Name of the EKS cluster to deploy to
- `eks_cluster_endpoint` - EKS cluster endpoint
- `eks_oidc_arn` - ARN of EKS OIDC provider for IAM roles
- `eks_cert_auth_data` - Auth certificate

## Source

[View on GitHub](https://github.com/awslabs/aiops-modules/tree/main/modules/eks/ray-orchestrator)
