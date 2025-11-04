# Buckets

**Category:** Storage  
**Module:** `storage/buckets`

## Description

This module creates the below AWS S3 buckets and policies:

  - Logs Data Bucket
  - Artifact Data Bucket
  - creates access policies for the buckets
    - READ-ONLY
    - FULL ACCESS

## Outputs

- `ArtifactsBucketName`: name of the bucket housing artifacts used for processing
- `LogsBucketName`: name of the bucket housing logs
- `ReadOnlyPolicyArn`: ARN of the policy generated giving read-only access to content
- `FullAccessPolicyArn`: ARN of the policy generated giving full access to content

## Source

[View on GitHub](https://github.com/awslabs/idf-modules/tree/main/modules/storage/buckets)
