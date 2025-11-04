# Deployment Guide

**Category:** Examples  
**Module:** `examples/mlops-stepfunctions`

## Description

This module shows how to integrate the AWS Step Functions with SageMaker, to create robust and scalable MLOps pipelines that automate the entire machine learning lifecycle.

Here's a typical workflow:

1. Data Preprocessing: Using AWS SageMaker Processing, you can preprocess your data by performing tasks such as data cleaning, feature engineering, and data splitting.

2. Model Training: Leverage SageMaker's built-in algorithms or bring your own custom code to train your machine learning model on the preprocessed data.

3. Model Evaluation: Evaluate the trained model's performance using metrics like accuracy, precision, recall, or custom metrics specific to your use case.

4. Model Approval: Implement manual or automated approval steps to review the model's performance and decide whether to proceed with deployment.

5. Model Deployment: Deploy your trained model to a SageMaker endpoint, making it available for real-time inference or batch processing.

## Input Parameters

#### Required

- `schedule`: cron expression to schedule the event to run the statemachine.

## Outputs

- `MlOpsBucket`: Name of the Bucket where Model Artifacts are stored.
- `SageMakerExecutionRole`: Execution Roles used by SageMaker Service.
- `ImageUri`: Docker Image URI used by SageMaker Jobs.
- `StateMachine`: ARN of State Machine.
- `LambdaFunction`: ARN of Lambda function which starts the execution of State Machine.

## Source

[View on GitHub](https://github.com/awslabs/aiops-modules/tree/main/modules/examples/mlops-stepfunctions)
