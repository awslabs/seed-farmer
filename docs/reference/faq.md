---
title: Frequently Asked Questions
---

This page answers common questions about Seed-Farmer and provides solutions to common problems.

## General Questions

### What is Seed-Farmer?

Seed-Farmer is a Python-based CI/CD library that leverages the [GitOps](https://opengitops.dev/) paradigm to manage deployed code. It is a tooling-agnostic deployment framework that supports AWS CDK, CloudFormation, Terraform, and other infrastructure-as-code tools.

### How does Seed-Farmer differ from other deployment tools?

Seed-Farmer is designed to be tooling-agnostic, meaning it can work with various infrastructure-as-code tools. It also provides multi-account support, dependency management, and metadata sharing between modules.

### What are the key features of Seed-Farmer?

Key features include:

- **Multi-Account Support**: Deploy across multiple AWS accounts with proper IAM role assumption
- **Dependency Management**: Modules can reference outputs from other modules
- **Metadata Sharing**: Modules can export metadata for use by dependent modules
- **Flexible Parameterization**: Support for various parameter sources including environment variables, AWS SSM Parameter Store, and AWS Secrets Manager
- **Security-Focused**: Least-privilege IAM roles and permissions boundaries
- **Tooling Agnosticism**: Support for various IaC tools (CDK, CloudFormation, Terraform)
- **GitOps Workflow**: Code-driven deployments with state management

## Installation and Setup

### How do I install Seed-Farmer?

The recommended way to install Seed-Farmer is using `uv`:

```bash
# Install uv if not already installed
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install Seed-Farmer as a tool (recommended)
uv tool install seed-farmer

# Or create a virtual environment and install
uv venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
uv pip install seed-farmer
```

For more details, see the [Installation](../getting-started/installation.md) guide.

### How do I bootstrap my AWS accounts for Seed-Farmer?

You need to bootstrap both your toolchain account and target accounts. For detailed instructions, see the [Bootstrapping](../getting-started/bootstrapping.md) guide.

### What are the prerequisites for using Seed-Farmer?

- Python 3.10 or later
- AWS CLI configured with appropriate credentials
- AWS CDK (for CDK-based modules)
- Docker (for local deployments)

## Deployments

### How do I create a deployment?

To create a deployment, you need to:

1. Create a deployment manifest
2. Create module manifests for each module
3. Run `seedfarmer apply` with the deployment manifest

For more details, see the [Quick Start](../getting-started/quick-start.md) guide.

### How do I destroy a deployment?

To destroy a deployment, run:

```bash
seedfarmer destroy DEPLOYMENT_NAME --env-file .env
```

This will destroy all the modules in the deployment in the reverse order of their deployment.

### How do I update a deployment?

To update a deployment, modify the deployment manifest or module manifests as needed, then run:

```bash
seedfarmer apply MANIFEST_PATH --env-file .env
```

Seed-Farmer will detect the changes and update the deployment accordingly.

### How do I list all deployments?

To list all deployments in a project, run:

```bash
seedfarmer list deployments --project PROJECT_NAME
```

### How do I list all modules in a deployment?

To list all modules in a deployment, run:

```bash
seedfarmer list modules -d DEPLOYMENT_NAME
```

### How do I deploy locally for development?

You can deploy locally using Docker containers instead of AWS CodeBuild by adding the `--local` flag:

```bash
seedfarmer apply MANIFEST_PATH --local --env-file .env
```

Local deployments are faster for development but are limited to single account/region deployments. For more details, see the [Local Deployments](../guides/local-deployments.md) guide.

### How do I destroy a local deployment?

To destroy a local deployment, use the `--local` flag with the destroy command:

```bash
seedfarmer destroy DEPLOYMENT_NAME --local --env-file .env
```

## Modules

### How do I create a new module?

You can create a new module using the `seedfarmer init module` command:

```bash
seedfarmer init module -g mygroup -m mymodule
```

This will create a new module in the `modules/mygroup/mymodule` directory with the necessary files.

### How do I reference outputs from one module in another?

You can reference outputs from one module in another using the `moduleMetadata` parameter source:

```yaml
parameters:
  - name: vpc-id
    valueFrom:
      moduleMetadata:
        group: optionals
        name: networking
        key: VpcId
```

### How do I add metadata to a module?

You can add metadata to a module using the `seedfarmer metadata add` command in the deployspec:

```yaml
deploy:
  phases:
    build:
      commands:
        - seedfarmer metadata add -k VpcId -v vpc-12345678
```

### How do I convert CDK output to metadata?

You can convert CDK output to metadata using the `seedfarmer metadata convert` command in the deployspec:

```yaml
deploy:
  phases:
    build:
      commands:
        - cdk deploy --all --require-approval never --outputs-file ./cdk-exports.json
        - seedfarmer metadata convert
```

## Multi-Account Support

### How do I deploy to multiple accounts?

You can deploy to multiple accounts by defining target account mappings in the deployment manifest:

```yaml
targetAccountMappings:
  - alias: primary
    accountId:
      valueFrom:
        envVariable: PRIMARY_ACCOUNT
    default: true
  - alias: secondary
    accountId: 123456789012
```

Then, in the module manifest, you can specify which account to deploy to:

```yaml
name: networking
path: modules/optionals/networking/
targetAccount: primary
```

### How do I bootstrap multiple accounts?

You need to bootstrap each account separately. First, bootstrap the toolchain account:

```bash
seedfarmer bootstrap toolchain \
  --project myproject \
  --trusted-principal arn:aws:iam::123456789012:role/Admin \
  --as-target
```

Then, bootstrap each target account:

```bash
seedfarmer bootstrap target \
  --project myproject \
  --toolchain-account 123456789012
```

### How do I use qualifiers for roles?

You can use qualifiers to segregate target deployments when using a multi-account structure:

```bash
seedfarmer bootstrap toolchain \
  --project myproject \
  --trusted-principal arn:aws:iam::123456789012:role/Admin \
  --qualifier dev123
```

!!! important
    The qualifier **must be the same** on the toolchain role and each target role.

## Security

### How do I apply permissions boundaries?

You can apply permissions boundaries to the toolchain and deployment roles:

```bash
seedfarmer bootstrap toolchain \
  --project myproject \
  --trusted-principal arn:aws:iam::123456789012:role/Admin \
  --permissions-boundary arn:aws:iam::123456789012:policy/MyBoundary
```

### How do I use IAM path prefixes?

You can use IAM path prefixes for the toolchain role, target account deployment roles, and policies:

```bash
seedfarmer bootstrap toolchain \
  --project myproject \
  --trusted-principal arn:aws:iam::123456789012:role/Admin \
  --role-prefix /myproject/ \
  --policy-prefix /myproject/
```

### How do I define module-specific permissions?

You can define module-specific permissions using the `modulestack.yaml` file. This file contains the granular permissions that the module role may need to deploy your module.

## Troubleshooting

### I'm getting an error about missing parameters

Make sure all required parameters are defined in the module manifest or referenced correctly from other sources (environment variables, module metadata, etc.).

### I'm getting an error about circular dependencies

Seed-Farmer prevents circular references between modules. Check your module dependencies to ensure there are no circular references.

### I'm getting an error about missing metadata

Make sure the module you're referencing has been deployed and is exporting the metadata you're trying to reference.

### I'm getting an error about missing roles

Make sure you've bootstrapped the toolchain and target accounts with the correct project name and qualifier.

### I'm getting an error about missing seedkit

Seed-Farmer automatically deploys the seedkit during the first deployment to each account/region. If you're getting an error about a missing seedkit, you can:

1. Let Seed-Farmer automatically deploy it during your next `seedfarmer apply`
2. Manually deploy the seedkit:

   ```bash
   seedfarmer seedkit deploy myproject --region us-east-1
   ```

3. If the seedkit is corrupted, destroy and redeploy it:
  
   ```bash
   seedfarmer seedkit destroy myproject --region us-east-1
   seedfarmer seedkit deploy myproject --region us-east-1
   ```

### I'm getting Docker errors during local deployment

Make sure Docker is installed and running on your local machine:

```bash
docker --version
docker info
```

Local deployments require Docker to run CodeBuild-compatible container images. If Docker is not available, use remote deployments instead.

### I'm getting an error about missing AWS CDK bootstrap

Make sure you've bootstrapped AWS CDK in each account/region combination you're deploying to:

```bash
cdk bootstrap aws://ACCOUNT-NUMBER/REGION
```

## Best Practices

### Use least-privilege permissions

Define the minimum permissions required for your modules in the `modulestack.yaml` file.

### Document your modules

Provide a comprehensive README.md that describes the module, its inputs, and its outputs.

### Use generic environment variables

If your module is intended to be reused across different projects, set `publishGenericEnvVariables: true` in the deployspec.

### Provide sample outputs

Include sample outputs in your README.md to help users understand what to expect.

### Use consistent naming conventions

Use consistent naming conventions for parameters and outputs to make it easier for users to understand your module.

### Handle errors gracefully

Include error handling in your deployspec commands to ensure that failures are reported clearly.

### Test your modules

Test your modules in isolation before integrating them into a larger deployment.

### Use the metadata CLI helper commands

Use the metadata CLI helper commands to manage and manipulate metadata in your module deployments.

### Optimize for reusability

Design your modules to be reusable across different deployments and projects.

### Follow the shared-responsibility model

Be aware of and manage the relationships between your modules and other modules to assess the impact of changes via redeployment.
