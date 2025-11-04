# Untitled Module

**Category:** Compute  
**Module:** `compute/emr-on-eks`

## Description



## Input Parameters

#### Required

- `vpc-id`: The VPC-ID that the cluster will be created in
- `private-subnet-ids`: The Private Subnets that the AWS Batch Compute resources will be deployed to
- `eks-cluster-admin-role-arn`: The EKS Cluster's Master IAM Role Arn obtained from EKS Module metadata
- `eks-cluster-name`: The EKS Cluster Name obtained from EKS Module metadata
- `eks-oidc-arn`: The EKS Cluster's OIDC Arn for creating EKS Service Accounts obtained from EKS Module metadata
- `eks-openid-issuer`: The EKS Cluster's OPEN ID issuer
- `eks-handler-rolearn`: The EKS Lambda Handler IAM Role Arn
- `emr-eks-namespace`: The K8s namespace to which the EMR Virtual Cluster will be tied to
- `artifacts-bucket-name`: The artifacts bucket to which the datasets will be uploaded
- `logs-bucket-name`: The logs bucket to which you can configure the spark logs to be written to

## Source

[View on GitHub](https://github.com/awslabs/idf-modules/tree/main/modules/compute/emr-on-eks)
