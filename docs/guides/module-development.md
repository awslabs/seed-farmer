---
title: Module Development
---

This guide provides comprehensive information on developing individual modules for Seed-Farmer. It covers the practical aspects of creating modules, including required files, deployspec structure, and development best practices.

## Understanding Modules

A Seed-Farmer module is a self-contained Infrastructure as Code (IaC) component that deploys specific AWS resources. Modules are designed to be reusable, composable building blocks that can be combined to create complex infrastructure deployments.

### Module Anatomy

Every module consists of:

- **Core infrastructure code** (CDK, CloudFormation, Terraform, etc.)
- **Deployspec** (`deployspec.yaml`) - deployment instructions
- **Documentation** (`README.md`) - usage and configuration guide
- **Optional permissions** (`modulestack.yaml`) - additional IAM permissions

### Module Types

Modules can be sourced from:

- **Local filesystem** - custom modules in your project
- **Git repositories** - shared modules from version control
- **Archives** - packaged modules from releases

For detailed information about module sources and manifest configuration, see the [Manifests Reference](../reference/manifests.md).

## Required Files

Every module must have these files:

- **`deployspec.yaml`** - Deployment and destruction instructions
- **`README.md`** - Module documentation and usage guide

## Optional Files

- **`modulestack.yaml`** - Additional IAM permissions for the module

## Creating a New Module

The Seed-Farmer CLI provides an `init` method to create your skeleton module code:

```bash
seedfarmer init module -g mygroup -m mymodule
cd modules/mygroup/mymodule
```

This will create the structure for your module. You'll need to edit the `deployspec.yaml` as needed. A `modulestack.template` file is also provided, which can be edited for additional permissions and renamed to `modulestack.yaml` to be used.

## Deployspec

The `deployspec.yaml` file is the execution blueprint for your module. It defines how your infrastructure code gets deployed and destroyed within AWS CodeBuild.

### Basic Structure

The deployspec has two main sections (`deploy` and `destroy`), each with four phases:

```yaml
deploy:
  phases:
    install:      # Install dependencies and tools
      commands:
        - npm install -g aws-cdk@2.100.0
        - pip install -r requirements.txt
    pre_build:    # Pre-deployment setup
      commands:
        - echo "Preparing deployment"
    build:        # Main deployment logic
      commands:
        - cdk deploy --all --require-approval never
    post_build:   # Export metadata for other modules
      commands:
        - seedfarmer metadata convert

destroy:
  phases:
    install:
      commands:
        - npm install -g aws-cdk@2.100.0
    build:
      commands:
        - cdk destroy --all --force

# Configuration
build_type: BUILD_GENERAL1_MEDIUM
publishGenericEnvVariables: true  # Recommended for reusable modules
```

### Key Configuration Options

- **`build_type`**: Controls CodeBuild compute resources (SMALL, MEDIUM, LARGE, 2XLARGE)
- **`publishGenericEnvVariables`**: Set to `true` (default) for reusable modules

### Parameter Access

Module parameters become environment variables in your deployspec:

```yaml
deploy:
  phases:
    build:
      commands:
        # Parameters are available as SEEDFARMER_PARAMETER_* variables
        - echo "VPC ID: $SEEDFARMER_PARAMETER_VPC_ID"
        - cdk deploy --parameters VpcId=$SEEDFARMER_PARAMETER_VPC_ID
```

### Metadata Export

Export outputs for other modules to use:

```yaml
deploy:
  phases:
    post_build:
      commands:
        # For CDK modules
        - cdk deploy --outputs-file cdk-outputs.json
        - seedfarmer metadata convert
        
        # For custom outputs
        - seedfarmer metadata add -k VpcId -v vpc-12345678
        - seedfarmer metadata add -j '{"SubnetIds": ["subnet-123", "subnet-456"]}'
```

For comprehensive information about deployspec structure, parameter handling, metadata management, and examples, see the [Deployspec Reference](../reference/deployspec.md).

## Module README

As part of the process to promote reusability of the modules, each module is required to have a README.md that talks directly to end users and describes:

- The description of the module
- The inputs - parameter names
  - Required
  - Optional
- The outputs - the parameter names in JSON format
  - Having a sample output is highly recommended so other users can quickly reference in their modules

### Example README

Below is a sample of the sections in a README.md for the modules:

```markdown
# OpenSearch Module

## Description

This module creates an OpenSearch cluster

## Inputs/Outputs

### Input Parameters

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
- `OpenSearchDashboardUrl`: URL of the OpenSearch cluster dashboard
- `OpenSearchSecurityGroupId`: name of the DDB table created for OpenSearch usage

#### Output Example

```json
{
  "OpenSearchDashboardUrl": "https://vpc-myapp-test-core-opensearch-aaa.us-east-1.es.amazonaws.com/_dashboards/",
  "OpenSearchDomainName": "vpc-myapp-test-core-opensearch-aaa",
  "OpenSearchDomainEndpoint": "vpc-myapp-test-core-opensearch-aaa.us-east-1.es.amazonaws.com",
  "OpenSearchSecurityGroupId": "sg-0475c9e7efba05c0d"
}
```

## ModuleStack

The modulestack (`modulestack.yaml`) is an optional AWS CloudFormation file that contains the granular permissions that the module role may need to deploy your module. It is recommended to use a least-privilege policy to promote security best practices.

By default, the CLI uses AWS CDK v2, which assumes a role that has the permissions to deploy via CloudFormation and is the recommended practice. You have the ability to use the `modulestack.yaml` to give additional permissions to the module role on your behalf.

Typical cases when you would use a `modulestack.yaml`:

- Any time you are invoking AWS CLI in the deployspec (not in the scope of the CDK) - for example: copying files to S3
- You prefer to use the AWS CLI v1 - in which a least-privilege policy is necessary for ALL AWS Services

### Initial Template

Below is a sample template that is provided by the CLI. The `Parameters` section is populated with the input provided from the CLI when deploying.

!!! warning
    It DOES have a policy definition that is wide-open - you SHOULD CHANGE THIS - it is only a template!

```yaml
AWSTemplateFormatVersion: 2010-09-09
Description: This template deploys a Module specific IAM permissions

Parameters:
  DeploymentName:
    Type: String
    Description: The name of the deployment
  ModuleName:
    Type: String
    Description: The name of the Module
  RoleName:
    Type: String
    Description: The name of the IAM Role

Resources:
  Policy:
    Type: 'AWS::IAM::Policy'
    Properties:
      PolicyDocument:
        Statement:
          - Effect: Allow
            Action: '*'
            Resource: '*'
        Version: 2012-10-17
      PolicyName: "myapp-modulespecific-policy"
      Roles: [!Ref RoleName]
```

### Parameters

As mentioned above, we strongly recommend a least-privilege policy to promote security best practices. The `modulestack.yaml` automatically has access to the parameters that were defined in your manifest file. Those passed parameters can help make your policy more explicit by using parameter names to limit permissions to a resource.

Below is an example of how to make use of this functionality.

Let's say we want to deploy an EKS module that needs to copy configuration files to an S3 bucket after the CDK deployment. We need to give permission to execute S3 operations and we want to restrict access to only the specific bucket created by our module.

Suppose this is our manifest. We want our modulestack.yaml to limit S3 access to our specific bucket:

```yaml
name: eks-cluster
path: modules/compute/eks/
parameters:
  - name: cluster-name
    value: my-data-platform
  - name: bucket-name
    value: my-data-platform-configs
  - name: vpc-id
    value: vpc-12345678
```

The parameter names in your module manifest are resolved in `CamelCase` in the modulestack.yaml file. The `bucket-name` parameter will resolve to `BucketName`. Back in our modulestack.yaml, under `Parameters`, the manifest parameter `bucket-name` is added as `BucketName`. Now we can add a policy that will allow S3 operations on our specific bucket by referencing the parameter we specified:

```yaml
Parameters:
  BucketName:
    Type: String
    Description: The name of the S3 bucket for configurations
  ClusterName:
    Type: String
    Description: The name of the EKS cluster

Resources:
  Policy:
    Type: "AWS::IAM::Policy"
    Properties:
      PolicyDocument:
        Statement:
          - Effect: Allow
            Action:
              - "s3:GetObject"
              - "s3:PutObject"
              - "s3:DeleteObject"
            Resource: !Sub "arn:aws:s3:::${BucketName}/*"
          - Effect: Allow
            Action:
              - "s3:ListBucket"
            Resource: !Sub "arn:aws:s3:::${BucketName}"
```

## Module Integration

Once you've developed your module, you need to integrate it into your project:

1. **Create module manifests** - Define how your module should be deployed using module manifests
2. **Add to deployment** - Include your module manifest in the appropriate deployment group
3. **Test integration** - Verify the module works correctly within the broader deployment

For detailed information about creating and configuring module manifests, see the [Manifests Reference](../reference/manifests.md).

## Best Practices

### Development Best Practices

- **Create generic modules**: Always use `publishGenericEnvVariables: true` (the default) to ensure reusability across projects
- **Use descriptive names**: Choose clear, descriptive names for modules and parameters
- **Follow naming conventions**: Use kebab-case for parameter names (e.g., `vpc-id`, `instance-type`)
- **Handle errors gracefully**: Include proper error handling and meaningful error messages in your deployspec

### Documentation Best Practices

- **Comprehensive README**: Document all inputs, outputs, and provide usage examples
- **Include sample outputs**: Show example JSON outputs to help users understand what to expect
- **Document dependencies**: Clearly state any module dependencies or prerequisites
- **Provide examples**: Include real-world usage examples in your documentation

### Security Best Practices

- **Use least-privilege permissions**: Define minimal required permissions in `modulestack.yaml`
- **Avoid hardcoded values**: Use parameters for all configurable values
- **Secure sensitive data**: Use AWS Secrets Manager or SSM Parameter Store for sensitive information
- **Validate inputs**: Include input validation in your deployspec when possible

### Testing Best Practices

- **Test in isolation**: Verify your module works independently before integration
- **Test both deploy and destroy**: Ensure both deployment and cleanup work correctly
- **Test with different parameters**: Verify the module works with various parameter combinations
- **Integration testing**: Test the module within a complete deployment scenario

### Metadata and Output Best Practices

- **Export meaningful outputs**: Provide outputs that other modules are likely to need
- **Use consistent output naming**: Follow consistent naming patterns for outputs
- **Use metadata CLI commands**: Leverage `seedfarmer metadata` commands for proper output management
- **Document output formats**: Clearly document the structure and format of complex outputs

For detailed information about parameters, environment variables, and module dependencies, see the [Manifests Reference](../reference/manifests.md).
