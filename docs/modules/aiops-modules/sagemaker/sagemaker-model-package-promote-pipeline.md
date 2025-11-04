# SageMaker Model Package Promote Pipeline Module

**Category:** Sagemaker  
**Module:** `sagemaker/sagemaker-model-package-promote-pipeline`

## Description

A Seedfarmer module to deploy a Pipeline to promote SageMaker Model Packages in a multi-account setup. The pipeline can be triggered through an EventBridge rule in reaction of a SageMaker Model Package Group state event change (Approved/Rejected). Once the pipeline is triggered, it will promote the latest approved model package, if one is found.

## Input Parameters

#### Required

- `source_model_package_group_arn`: The SageMaker Model Package Group ARN to get the latest approved model package. The model package can be in another account (Source AWS Account).
- `target_bucket_name`: The S3 bucket name in the target account (Target AWS Account) to store model artifacts.

## Outputs

- `PipelineArn`: the CodePipeline ARN.
- `PipelineName`: the CodePipeline name.

## Source

[View on GitHub](https://github.com/awslabs/aiops-modules/tree/main/modules/sagemaker/sagemaker-model-package-promote-pipeline)
