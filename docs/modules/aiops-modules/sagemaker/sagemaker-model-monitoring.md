# SageMaker Model Monitoring

**Category:** Sagemaker  
**Module:** `sagemaker/sagemaker-model-monitoring`

## Description

This module creates SageMaker Model Monitoring jobs for (optionally) data quality, model quality,
model bias, and model explainability. It requires a deployed model endpoint and the proper check steps
for each monitoring job:

* Data Quality: [QualityCheck step](https://docs.aws.amazon.com/sagemaker/latest/dg/build-and-manage-steps.html#step-type-quality-check)
* Model Quality: [QualityCheck step](https://docs.aws.amazon.com/sagemaker/latest/dg/build-and-manage-steps.html#step-type-quality-check)
* Model Bias: [ClarifyCheck step](https://docs.aws.amazon.com/sagemaker/latest/dg/build-and-manage-steps.html#step-type-clarify-check)
* Model Explainability: [ClarifyCheck step](https://docs.aws.amazon.com/sagemaker/latest/dg/build-and-manage-steps.html#step-type-clarify-check)

Note that updating parameters will require replacing resources. Deployments may be delayed until any
running monitoring jobs complete (and the resources can be destroyed).

## Input Parameters

#### Required

- `endpoint-name`: The name of the endpoint used to run the monitoring job.
- `security-group-id`: The VPC security group IDs, should provide access to the given `subnet-ids`.
- `subnet-ids`: The ID of the subnets in the VPC to which you want to connect your training job or model.
- `model-package-arn`: Model package ARN
- `model-bucket-arn`: S3 bucket ARN for model artifacts
- `kms-key-id`: The KMS key used to encrypted storage and output.

One or more of:

- `enable-data-quality-monitor`: True to enable the data quality monitoring job.
- `enable-model-quality-monitor`: True to enable the model quality monitoring job.
- `enable-model-bias-monitor`: True to enable the model bias monitoring job.
- `enable-model-explainability-monitor`: True to enable the model explainability monitoring job.

## Outputs

- `ModelExecutionRoleArn`: SageMaker Model Execution IAM role ARN
- `ModelName`: SageMaker Model name
- `ModelPackageArn`: SageMaker Model package ARN
- `EndpointName`: SageMaker Endpoint name
- `EndpointUrl`: SageMaker Endpoint Url

## Source

[View on GitHub](https://github.com/awslabs/aiops-modules/tree/main/modules/sagemaker/sagemaker-model-monitoring)
