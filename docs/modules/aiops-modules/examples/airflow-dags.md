# Example DAG Module

**Category:** Examples  
**Module:** `examples/airflow-dags`

## Description

This module demonstrates:

- creating a CDK Stack with Role dedicated to the DAGs
  - within the Stack, grant the MWAA Execution Role permission to assume the created DAG Execution Role
- creating DAGs on a shared MWAA Environment by utilizing Input Parameters
  - within the DAG, demonstrate assuming the DAG Execution Role with service and data permissions specific to the DAG
- exporting Metadata by setting the `MLOPS_MODULE_METADATA` env var on completion

## Input Parameters

#### Required

- `dag-bucket-name`: name of the Bucket configured in the shared MWAA Environment to store DAG artifacts
- `dag-path`: name of the path in the Bucket configured in the shared MWAA Environment to store DAG artifacts
- `mwaa-exec-role-arn`: ARN of the MWAA Execution Role

## Outputs

- `DagRoleArn`: ARN of the DAG Execution Role created by the Stack
- `MlOpsBucket`: Name of the Bucket used by the dag
- `SageMakerExecutionRole`: ARN of the Sagemaker Execution Role created by the Stack

## Source

[View on GitHub](https://github.com/awslabs/aiops-modules/tree/main/modules/examples/airflow-dags)
