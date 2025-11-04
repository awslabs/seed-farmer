# SageMaker Model Package Group

**Category:** Sagemaker  
**Module:** `sagemaker/sagemaker-model-package-group`

## Description

This module creates a SageMaker Model Package Group to register and version SageMaker Machine Learning (ML) models and setups an Amazon EventBridge Rule to send model package group state change events to an Amazon EventBridge Bus.

## Input Parameters

#### Required

- `model_package_group_name`: SageMaker Package Group Name to setup event rules.

## Outputs

- `SagemakerModelPackageGroupArn`: the SageMaker Model Package Group ARN.
- `SagemakerModelPackageGroupName`: the SageMaker Model Package Group name.

## Source

[View on GitHub](https://github.com/awslabs/aiops-modules/tree/main/modules/sagemaker/sagemaker-model-package-group)
