# AppSync endpoint for Question and Answering using RAG

**Category:** Fmops  
**Module:** `fmops/qna-rag`

## Description

Deploys an AWS AppSync endpoint for ingestion of data and use it as knowledge base for a Question and Answering model using RAG 

The module uses [AWS Generative AI CDK Constructs](https://github.com/awslabs/generative-ai-cdk-constructs/tree/main).

## Input Parameters

#### Required

- `cognito-pool-id` - ID of the cognito user pool, used to secure GraphQl API
- `os-domain-endpoint` - Open Search domain url used as knowledge base
- `os-security-group-id` - Security group of open search cluster
- `vpc-id` - VPC id

## Outputs

- `IngestionGraphqlApiId` - Ingestion Graphql API ID.
- `IngestionGraphqlArn` - Ingestion Graphql API ARN.
- `QnAGraphqlApiId` - Graphql API ID.
- `QnAGraphqlArn` - Graphql API ARN.
- `InputAssetBucket` - Input S3 bucket.
- `ProcessedInputBucket` - S3 bucket for storing processed output.

## Source

[View on GitHub](https://github.com/awslabs/aiops-modules/tree/main/modules/fmops/qna-rag)
