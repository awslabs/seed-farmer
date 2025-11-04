# Untitled Module

**Category:** Storage  
**Module:** `storage/fsx-lustre`

## Description

Amazon FSx for Lustre provides fully managed shared storage with the scalability and performance of the popular Lustre file system.

Amazon FSx also integrates with Amazon S3, making it easy for you to process cloud data sets with the Lustre high-performance file system. When linked to an S3 bucket, an FSx for Lustre file system transparently presents S3 objects as files and automatically updates the contents of the linked S3 bucket as files are added to, changed in, or deleted from the file system.

Amazon FSx for Lustre uses parallel data transfer techniques to transfer data to and from S3 at up to hundreds of GB/s. Use Amazon FSx for Lustre for workloads where speed matters.

## Input Parameters

#### Required

- `vpc_id`: The VPC in which to create the security group for your file system
- `private_subnet_ids`: Specifies the IDs of the subnets that the file system will be accessible from
- `fs_deployment_type`:
  - Choose `SCRATCH_1` and `SCRATCH_2` deployment types when you need temporary storage and shorter-term processing of data. The `SCRATCH_2` deployment type provides in-transit encryption of data and higher burst throughput capacity than `SCRATCH_1` .
  - Choose `PERSISTENT_1` for longer-term storage and for throughput-focused workloads that aren’t latency-sensitive. `PERSISTENT_1` supports encryption of data in transit, and is available in all AWS Regions in which FSx for Lustre is available.
  - Choose `PERSISTENT_2` for longer-term storage and for latency-sensitive workloads that require the highest levels of IOPS/throughput. `PERSISTENT_2` supports SSD storage, and offers higher PerUnitStorageThroughput (up to 1000 MB/s/TiB). `PERSISTENT_2` is available in a limited number of AWS Regions.
  - For more information, and an up-to-date list of AWS Regions in which `PERSISTENT_2` is available, see File system deployment options for FSx for Lustre in the Amazon FSx for Lustre User Guide . .. epigraph:: If you choose `PERSISTENT_2` , and you set FileSystemTypeVersion to 2.10, the CreateFileSystem operation fails. Encryption of data in transit is automatically turned on when you access SCRATCH_2 , PERSISTENT_1 and `PERSISTENT_2` file systems from Amazon EC2 instances that [support automatic encryption](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/data- protection.html) in the AWS Regions where they are available. For more information about encryption in transit for FSx for Lustre file systems, see Encrypting data in transit in the Amazon FSx for Lustre User Guide . (Default = SCRATCH_1 )

## Outputs

#### Output Example

```json
{
  "FSxLustreAttrDnsName": "fs-05d205d87c763d71e.fsx.us-east-1.amazonaws.com",
  "FSxLustreFileSystemDeploymentType": "PERSISTENT_2",
  "FSxLustreFileSystemId": "fs-05d205d87c763d71e",
  "FSxLustreMountName": "frinzbev",
  "FSxLustreSecurityGroup": "sg-0ca5da2aebca3459b",
  "FSxLustreVersion": "2.15",
  "FSxLustreStorageCapacity": 1200
}
```

## Example Usage

Stand-alone module manifest example:

```yaml
name: storage
path: modules/core/fsx-lustre/
parameters:
  - name: private_subnet_ids
    value: [subnet-abc1234]
  - name: vpc_id
    value: vpc-123abc34
  - name: data_bucket_name
    value: data_bucket_name
  - name: fs_deployment_type
    value: PERSISTENT_2
  - name: storage_throughput
    value: 125
  # - name: export_path
  #   value: "/fsx/export/"
  # - name: import_path
  #   value: "/fsx/import/"
  - name: dra_export_path # Do not mention import_path and export_path if you mention dra_export_path and dra_import_path
    value: "/ray/export/"
  - name: dra_import_path
    value: "/ray/import/"
  - name: fsx_version 
    value: "2.15"
  - name: import_policy
    value: "NEW_CHANGED_DELETED"
  - name: storage_capacity
    value: 1200
```

Module manifest leveraging the `networking` module:

```yaml
name: storage
path: modules/core/fsx-lustre/
parameters:
  - name: private_subnet_ids
    valueFrom:
      moduleMetadata:
        group: optionals
        name: networking
        key: PrivateSubnetIds
  - name: vpc_id
    valueFrom:
      moduleMetadata:
        group: optionals
        name: networking
        key: VpcId
  ...
```

## Source

[View on GitHub](https://github.com/awslabs/idf-modules/tree/main/modules/storage/fsx-lustre)
