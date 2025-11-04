# Amazon EMR Serverless

**Category:** Compute  
**Module:** `compute/emr-serverless`

## Description

This module:

- creates an Amazon EMR Serverless Application
- creates an IAM Role and policy for Jobs on the EMR Application

## Outputs

- `EmrApplicationId`: name of the S3 Bucket configured to store MWAA Environment DAG artifacts
- `EmrJobExecutionRoleArn`: name of the path in the S3 Bucket configured to store MWAA Environment DAG artifacts
- `EmrSecurityGroupId`: Security group ID associated with EMR Serverless environment

## Source

[View on GitHub](https://github.com/awslabs/idf-modules/tree/main/modules/compute/emr-serverless)
