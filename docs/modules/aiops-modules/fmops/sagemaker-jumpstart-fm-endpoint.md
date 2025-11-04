# SageMaker JumpStart Foundation Model Endpoint

**Category:** Fmops  
**Module:** `fmops/sagemaker-jumpstart-fm-endpoint`

## Description

Deploys an endpoint for a foundation model from [SageMaker JumpStart Foundation Models](https://docs.aws.amazon.com/sagemaker/latest/dg/jumpstart-foundation-models.html).

The module uses [AWS Generative AI CDK Constructs](https://github.com/awslabs/generative-ai-cdk-constructs/tree/main).

## Input Parameters

#### Required

- `jump-start-model-name` - model name from SageMaker JumpStart Foundation Models
- `instance-type` - inference container instance type

## Outputs

- `EndpointArn` - endpoint ARN.
- `RoleArn` - IAM role ARN.

## Source

[View on GitHub](https://github.com/awslabs/aiops-modules/tree/main/modules/fmops/sagemaker-jumpstart-fm-endpoint)
