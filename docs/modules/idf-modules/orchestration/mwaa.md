# Amazon Managed Workflows for Apache Airflow (MWAA)

**Category:** Orchestration  
**Module:** `orchestration/mwaa`

## Description

This module:

- creates an Amazon Managed Airflow Environment to execute DAGs created by other modules
- creates an IAM Role (the MWAA Execution Role) with least privilege permissions
- *Optionally* creates an S3 Bucket to store DAG artifacts

## Outputs

- `DagBucketName`: name of the S3 Bucket configured to store MWAA Environment DAG artifacts
- `DagPath`: name of the path in the S3 Bucket configured to store MWAA Environment DAG artifacts
- `MwaaExecRoleArn`: ARN of the MWAA Execution Role created by the Stack

## Source

[View on GitHub](https://github.com/awslabs/idf-modules/tree/main/modules/orchestration/mwaa)
