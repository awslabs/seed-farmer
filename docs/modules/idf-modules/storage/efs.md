# Untitled Module

**Category:** Storage  
**Module:** `storage/efs`

## Description

This module will create a new EFS service endpoint and security group tied to the provide VPC.

## Input Parameters

#### Required

- `vpc-id` - the VPC ID where this EFS will be tied to via Security Groups
- `removal-policy` - the retention policy to put on the EFS service
  - defaults to `RETAIN`
  - supports `DESTROY` and `RETAIN` only

## Outputs

- `EFSFileSystemArn` - the ARN of the EFS
- `EFSFileSystemId` - the unique EFS ID
- `EFSSecurityGroupId` - the created Security Group tied to the EFS
- `VPCId` - the VPC tied to the new EFS

## Example Usage

```yaml
  - name: vpc-id
    valueFrom:
      moduleMetadata:
        group: optionals
        name: networking
        key: VpcId
  - name: removal-policy
    value: RETAIN
```

## Source

[View on GitHub](https://github.com/awslabs/idf-modules/tree/main/modules/storage/efs)
