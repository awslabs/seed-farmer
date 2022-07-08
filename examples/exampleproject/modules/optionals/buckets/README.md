# Buckets

## Description

This module creates buckets and policies . 

This module:
- creates buckets
  - Logs Data Bucket
  - Artifact Data Bucket
- creates access policies for the buckets
  - READ-ONLY
  - FULL ACCESS 


## Inputs/Outputs

### Input Paramenters
None

#### Required

None

#### Optional
- `encryption-type`: the type of encryption on data stored in the buckets
  - `SSE` or `KMS` 
  - Assumed to be `SSE`
- `retention-type`: type of data retention policy when deleteing the buckets
  - `DESTROY` or `RETAIN`
  - Assumed to be `DESTROY`


### Module Metadata Outputs
- `ArtifactsBucketName`: name of the bucket housing artifacts used for processing
- `LogsBucketName`: name of the bucket housing logs
- `ReadOnlyPolicyArn`: ARN of the policy generated giving read-only access to content
- `FullAccessPolicyArn`: ARN of the policy generated giving full access to content



#### Output Example

```json
{
  "ArtifactsBucketName": "examples-dep-artifacts-bucket-us-east-1-12345678901",
  "LogsBucketName": "examples-dep-logs-bucket-us-east-1-123456789012",
  "FullAccessPolicyArn": "arn:aws:iam::123456789012:policy/examples-dep-optionals-datalake-buckets-us-east-1-123456789012-full-access",
  "ReadOnlyPolicyArn": "arn:aws:iam::123456789012:policy/examples-dep-optionals-datalake-buckets-us-east-1-123456789012-readonly-access"
}
```
