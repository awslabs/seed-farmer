# Untitled Module

**Category:** Replication  
**Module:** `replication/dockerimage-replication`

## Description

This module replicates Docker images and Helm charts from the list of provided Helm charts and any docker image from a public registry into an AWS account's Private ECR. For deploying EKS module or any container related apps in isolated subnets (which has access to AWS APIs via Private endpoints), the respective docker images and helm charts should be available internally in an ECR repo as a prerequisite. This module will generate two files for internal processing:

- `replication_result.json` - an inventory of the charts and image information, this provides the source and target address of the charts
- `updated_images.json` - the src and target of all images referenced

The `replication_result.json` gets copied to a new filename as indicated by the output parameter `S3Object` (see below).  This file serves as the chart value overrides when the helm charts are applied.  NOTE: this file can also apply changes to values when the charts are deployed on EKS.

ALL resulting ECR repositories (images and helm charts) are scoped to the project, not the deployment, so they can be used across deployments within a project.  




***CLEANUP***

The cleanup workflow invokes a python script which deletes the replicated docker images from ECR whose prefix starts with `project_name`. This may cause issues if the replicated images are being used by other applications in the same/cross account.  To prevent inadvertent deletion of the ECR repos, this module supports a configurable parameter `RetentionType`.  This is by default set to `RETAIN`.  If configured with the string `DESTROY`, then all ECR repositories with the prefix of the project will be permanently deleted. An end-user can also run `delete_repos.py` with the project name to remove all ECR repos manually:

```bash
python delete_repos.py <project-name>
```

## Input Parameters

#### Required Parameters

- `eks_version`: The EKS Cluster version to lock the version to

## Outputs

- `S3Bucket` - the name of the bucket created to house the output values file used by EKS
- `S3FullPath` - the full path of the output values file (use this in the eks manifest!!)
- `S3Object` - the name of the file with the values 
- `s3_bucket`: same as `S3Bucket` but is considered deprecated
- `s3_full_path`: same as `S3FullPath` but is considered deprecated
- `s3_object`: same as `S3Object` but is considered deprecated

```json
{
  "repl": {
    "S3Bucket": "idftest-dkr-img-rep-md-us-east-1-123456789012",
    "S3FullPath": "idftest-dkr-img-rep-md-us-east-1-123456789012/repltestrepl-repl-repl-metadata.json",
    "S3Object": "repltestrepl-repl-repl-metadata.json",
    "s3_bucket": "idftest-dkr-img-rep-md-us-east-1-123456789012", // For backward compatibility
    "s3_full_path": "idftest-dkr-img-rep-md-us-east-1-123456789012/repltestrepl-repl-repl-metadata.json", // For backward compatibility
    "s3_object": "repltestrepl-repl-repl-metadata.json" // For backward compatibility
  }
}
```

## Source

[View on GitHub](https://github.com/awslabs/idf-modules/tree/main/modules/replication/dockerimage-replication)
