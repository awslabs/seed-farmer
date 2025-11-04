# SageMaker Hugging Face Foundation Model Endpoint

**Category:** Fmops  
**Module:** `fmops/sagemaker-hugging-face-endpoint`

## Description

Deploys an endpoint for a foundation model supported by [Hugging Face LLM Inference Containers for Amazon SageMaker](https://huggingface.co/blog/sagemaker-huggingface-llm).

The module uses [AWS Generative AI CDK Constructs](https://github.com/awslabs/generative-ai-cdk-constructs/tree/main).

## Input Parameters

#### Required

- `hugging-face-model-id` - ID of the Hugging Face model
- `instance-type` - inference container instance type
- `deep-learning-container-image` - container image repository and tag

## Outputs

- `EndpointArn` - endpoint ARN.
- `RoleArn` - IAM role ARN.

## Source

[View on GitHub](https://github.com/awslabs/aiops-modules/tree/main/modules/fmops/sagemaker-hugging-face-endpoint)
