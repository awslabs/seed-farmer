# IDF Modules

The **Industry Data Framework (IDF)** modules provide foundational infrastructure components for building scalable data processing and analytics solutions on AWS. These modules follow AWS best practices and provide consistent, reusable patterns for common infrastructure needs.

## Repository

**Source**: [AWS IDF Modules](https://github.com/awslabs/idf-modules)

## Available Modules

- **[Compute](./compute/index.md)** - EKS clusters, EMR, and AWS Batch configurations
- **[Database](./database/index.md)** - RDS and Neptune database services
- **[Dummy](./dummy/index.md)** - Template and example modules for development
- **[Integration](./integration/index.md)** - Integration patterns and connectors for data workflows
- **[Network](./network/index.md)** - VPCs, subnets, and security groups
- **[Orchestration](./orchestration/index.md)** - Amazon MWAA (Managed Apache Airflow)
- **[Replication](./replication/index.md)** - Data and container image replication utilities
- **[Service Catalog](./service-catalog/index.md)** - AWS Service Catalog and application registry
- **[Storage](./storage/index.md)** - S3 buckets, EFS, FSx Lustre, and OpenSearch
- **[Testing](./testing/index.md)** - Testing frameworks and integration utilities

## Key Features

- **AWS Native**: Built using AWS CDK and CloudFormation
- **Production Ready**: Tested and validated for production workloads
- **Configurable**: Extensive parameterization for different use cases
- **Integrated**: Designed to work together as part of larger solutions
- **Documented**: Comprehensive documentation and examples

## Usage Example

```yaml
# Reference IDF modules in your deployment manifest
name: data-platform-networking
path: git::https://github.com/awslabs/idf-modules.git//modules/network/basic-cdk?ref=release/1.0.0&depth=1
targetAccount: primary
parameters:
  - name: internet-accessible
    value: true
  - name: nat-gateway-strategy
    value: SINGLE_NAT_GATEWAY
```

## Getting Started

1. **Browse the categories** above to find modules that match your infrastructure needs
2. **Review individual module documentation** for parameters and configuration options
3. **Reference modules in your Seed-Farmer deployment manifests**
4. **Deploy using standard Seed-Farmer commands**

For more information about module development and usage patterns, see the [Module Development Guide](../../guides/module-development.md).
