# SageMaker Model Endpoint

**Category:** Sagemaker  
**Module:** `sagemaker/sagemaker-endpoint`

## Description

This module creates SageMaker Model, Endpoint Configuration Production Variant, and a real-time Inference Endpoint. 
The endpoint is deployed in a VPC inside user-provided subnets.

The module supports provisioning of an endpoint from a model package, or may automatically pull
the latest approved model from model package group to support CI/CD deployment scenarios.

## Input Parameters

#### Required

- `vpc-id`: The VPC-ID that the endpoint will be created in.
- `subnet-ids`: The subnets that the endpoint will be created in.
- `model-package-arn`: Model package ARN `OR`
- `model-package-group-name`: Model package group name to pull latest approved model package from the group.

The user must specify either `model-package-arn` for a specific model or `model-package-group-name` to automatically
pull latest approved model from the model package group and deploy and endpoint. The latter is useful to scenarios
where endpoints are provisioned as part of automated Continuous Integration and Deployment pipeline.

## Outputs

- `ModelExecutionRoleArn`: SageMaker Model Execution IAM role ARN
- `ModelName`: SageMaker Model name
- `ModelPackageArn`: SageMaker Model package ARN
- `EndpointName`: SageMaker Endpoint name
- `EndpointUrl`: SageMaker Endpoint Url
- `KmsKeyId`: The KMS Key ID used for the SageMaker Endpoint assets bucket
- `SecurityGroupId`: The security group ID for the SageMaker Endpoint

## Source

[View on GitHub](https://github.com/awslabs/aiops-modules/tree/main/modules/sagemaker/sagemaker-endpoint)
