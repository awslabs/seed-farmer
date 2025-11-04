# Mlflow on AWS Fargate

**Category:** Mlflow  
**Module:** `mlflow/mlflow-fargate`

## Description

This module runs Mlflow on AWS Fargate as a load-balanced Elastic Container Service.

By default, uses Elastic File System for backend storage and S3 for artifact storage. Optionally, a Relational Database Storage instance can be used for metadata.

## Input Parameters

#### Required

- `vpc-id`: The VPC-ID that the ECS cluster will be created in.
- `subnet-ids`: The subnets that the Fargate task will use.
- `ecr-repository-name`: The name of the ECR repository to pull the image from.
- `artifacts-bucket-name`: Name of the artifacts store bucket

## Outputs

- `ECSClusterName`: Name of the ECS cluster.
- `ServiceName`: Name of the service.
- `LoadBalancerDNSName`: Load balancer DNS name.
- `LoadBalancerAccessLogsBucketArn`: Load balancer access logs bucket arn
- `EFSFileSystemId`: EFS file system id.

## Source

[View on GitHub](https://github.com/awslabs/aiops-modules/tree/main/modules/mlflow/mlflow-fargate)
