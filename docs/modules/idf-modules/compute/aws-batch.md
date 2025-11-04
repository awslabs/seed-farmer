# AWS Batch Compute Environments and Job Queues

**Category:** Compute  
**Module:** `compute/aws-batch`

## Description

This module:
- Creates different AWS Batch Compute resources based on the configuration
- Creates AWS Batch Queue(s) based on the user input

## Input Parameters

#### Required

- `vpc-id`: The VPC-ID that the cluster will be created in
- `private-subnet-ids`: The Private Subnets that the AWS Batch Compute resources will be deployed to
- `batch-compute`: The Configuration Map for creating AWS Batch Compute environment(s). Below is a sample snippet for providing `batch-compute` input

## Outputs

- `BatchPolicyString`: Iam Policy for Orchestration Tools like Airflow & Step Functions to Submit Jobs to Batch
- `BatchSecurityGroupId`: Security Group Id of the Batch Compute ECS Cluster
- `OnDemandJobQueueArn`: ARN of the ON_DEMAND AWS Batch Queue
- `SpotJobQueueArn`: ARN of the SPOT AWS Batch Queue
- `FargateJobQueueArn`: ARN of the FARGATE AWS Batch Queue

## Source

[View on GitHub](https://github.com/awslabs/idf-modules/tree/main/modules/compute/aws-batch)
