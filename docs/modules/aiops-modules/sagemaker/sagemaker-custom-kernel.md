# Custom Kernel Module

**Category:** Sagemaker  
**Module:** `sagemaker/sagemaker-custom-kernel`

## Description

This module builds custom kernel for SageMaker studio from a Dockerfile.

## Input Parameters

#### Required

- `ecr-repo-name`: Name of the ECR repo for the image.
- `studio-domain-id`: SageMaker studio domain to attach the kernel to.
- `studio-domain-name`: SageMaker studio name to attach the kernel to.
- `sagemaker-image-name`: Name of the sagemaker image. This variable is also used to find the Dockerfile. The docker build script will be looking for file inside `modules/mlops/custom-kernel/docker/{sagemaker_image_name}`. 1 Dockerfile is added already: `pytorch-10`.
- `studio-execution-role-arn`: SageMaker Studio Domain execution role. Required to associate custom kernel with SageMaker Studio Domain.

## Outputs

- `ECRRepositoryName`: ECR repository name
- `CustomKernelImageName`: Image name
- `CustomKernelImageURI`: Image URI
- `AppImageConfigName`: AppConfig image name
- `SageMakerCustomKernelRoleArn`: Role for custom kernel

## Source

[View on GitHub](https://github.com/awslabs/aiops-modules/tree/main/modules/sagemaker/sagemaker-custom-kernel)
