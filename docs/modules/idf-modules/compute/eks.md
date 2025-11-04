# EKS

**Category:** Compute  
**Module:** `compute/eks`

## Description

This module creates an EKS Cluster with the following features and addons available for use:

- Can create EKS Control plane and data plane in Private Subnets (having NATG in the route tables)
- Can create EKS Control plane in Private Subnets and data plane in Isolated Subnets (having Link local route in the route tables)
- Can launch application pods in secondary CIDR to save IP exhaustion in the primary CIDR
- Encrypts the root EBS volumes of managed node groups
- Can encrypt the EKS Control plane using Envelope encryption

## Outputs

- `EksClusterName`: The EKS Cluster Name
- `EksClusterAdminRoleArn`: The EKS Cluster's Admin Role Arn
- `EksClusterSecurityGroupId`: The EKS Cluster's SecurityGroup ID
- `EksOidcArn`: The EKS Cluster's OIDC Arn
- `EksClusterOpenIdConnectIssuer`: EKS Cluster's OPEN ID Issuer
- `EksClusterMasterRoleArn` - the masterrole used for cluster creation
- `EksNodeRoleArn` - the role assigned to nodes when nodes are spinning up in node groups.

## Source

[View on GitHub](https://github.com/awslabs/idf-modules/tree/main/modules/compute/eks)
