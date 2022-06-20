## Module ReadMe Doc

As part of the process to promote reusability and sharabiltiy of the modules, each module is required to have a README.md that talks directly to end users and describes:

- the description of the module
- the inputs - parameter names
  - required
  - optional
- the outputs - the parameter names in JSON format
  - having a sample output is highly recommneded so other users cancan quickly reference in their modules


### Example 

Below is a sample of the sections in a README.md for the modules:

```
# OpenSearch Module


## Description

This module creates an OpenSearch cluster


## Inputs/Outputs

### Input Paramenters

#### Required

- `vpc-id`: The VPC-ID that the cluster will be created in

#### Optional
- `opensearch_data_nodes`: The number of data nodes, defaults to `1`
- `opensearch_data_nodes_instance_type`: The data node type, defaults to `r6g.large.search`
- `opensearch_master_nodes`: The number of master nodes, defaults to `0`
- `opensearch_master_nodes_instance_type`: The master node type, defaults to `r6g.large.search`
- `opensearch_ebs_volume_size`: The EBS volume size (in GB), defaults to `10`

### Module Metadata Outputs

- `OpenSearchDomainEndpoint`: the endpoint name of the OpenSearch Domain
  `OpenSearchDomainName`: the name of the OpenSearch Domain
- `OpenSeearchDashboardUrl`: URL of the OpenSearch cluster dashboard
- `OpenSearchSecurityGroupId`: name of the DDB table created for Rosbag Scene Data

#### Output Example

```json
{
  "OpenSearchDashboardUrl": "https://vpc-myapp-test-core-opensearch-aaa.us-east-1.es.amazonaws.com/_dashboards/",
  "OpenSearchDomainName": "vpc-myapp-test-core-opensearch-aaa",
  "OpenSearchDomainEndpoint": "vpc-myapp-test-core-opensearch-aaa.us-east-1.es.amazonaws.com",
  "OpenSearchSecurityGroupId": "sg-0475c9e7efba05c0d"
}

```


```