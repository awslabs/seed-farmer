---
title: IDF Modules
---

The **Industry Data Framework (IDF)** modules provide foundational infrastructure components for building scalable data processing and analytics solutions on AWS. These modules follow AWS best practices and provide consistent, reusable patterns for common infrastructure needs.

## Repository

**Source**: [AWS IDF Modules](https://github.com/awslabs/idf-modules)

## Available Modules

**_Coming Soon_** - _Feel free to directly access the Git Repository listed above in the meantime._

We will provide a comprehensive list of:

- current modules available
- description of each module
- input and output definitions
- example manifest configurations


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
