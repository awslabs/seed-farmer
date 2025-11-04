# Local Deployments

This guide explains how to deploy Seed-Farmer projects locally using Docker for development and testing purposes. Local deployments provide a fast feedback loop for module development while maintaining consistency with remote deployments.

## What are Local Deployments?

Local deployments execute your module code via the deployspec using Docker containers on your local machine instead of AWS CodeBuild. This approach:

- **Speeds up development**: No need to wait for CodeBuild project startup
- **Reduces costs**: No CodeBuild charges during development
- **Maintains consistency**: Uses the same container images as remote deployments
- **Enables offline development**: Work without constant AWS connectivity

## Key Differences from Remote Deployments

| Aspect | Local Deployments | Remote Deployments |
|--------|------------------|-------------------|
| **Execution Environment** | Docker on local machine | AWS CodeBuild |
| **Account/Region Support** | Single account/region only | Multi-account/region |
| **Manifest Changes** | Automatic region override | Uses manifest as-is |
| **Performance** | Faster startup | Slower startup, better for production |
| **Cost** | No AWS charges | CodeBuild charges apply |
| **Networking** | Local machine network | AWS VPC (configurable) |

## Prerequisites

Before you can deploy locally, ensure you have:

### Required Software

- **Docker**: Must be installed and running on your local machine
- **Seed-Farmer**: Installed via pip (`pip install seed-farmer`)
- **AWS CLI**: Configured with appropriate credentials

### AWS Setup

- **AWS credentials**: Configured for the target account
- **AWS CDK bootstrap**: Completed in the target account/region
- **Seed-Farmer bootstrap**: Toolchain and target accounts bootstrapped
- **Seedkit infrastructure**: Deployed in the target account/region

### Docker Requirements

Local deployments require Docker to run CodeBuild-compatible container images:

```bash
# Verify Docker is installed and running
docker --version
docker info
```

**Docker Images**:

These images are required for using Local Deployments:

- `public.ecr.aws/codebuild/local-builds:latest` - used for management of the deployment execution
- `public.ecr.aws/codebuild/amazonlinux2-x86_64-standard:5.0`- the codebuild image used for deployment

!!! note "Image Support"
    Currently, local deployments only support the Amazon Linux 2 x86_64 standard image. Support for additional CodeBuild images will be added in future releases. The image used is driven by your deployment and module manifest configuration.

!!! note "Image Conversion"
    Seed-Farmer automatically converts AWS CodeBuild image references (e.g., `aws/codebuild/amazonlinux2-x86_64-standard:5.0`) to their public ECR equivalents for local use.

!!! info "CodeBuild Agent"
    Local deployments use Docker to simulate the AWS CodeBuild environment. For more information about CodeBuild's local execution capabilities, see the [AWS CodeBuild Agent documentation](https://docs.aws.amazon.com/codebuild/latest/userguide/use-codebuild-agent.html).

## Environment Variables

Create an `.env` file to store environment variables needed for your deployment:

```bash
echo AWS_DEFAULT_REGION=us-east-1 >> .env
echo PRIMARY_ACCOUNT=210987654321 >> .env
echo BUCKET_NAME=loggingbucket >> .env
```

## Authentication

Seed-Farmer local deployments use AWS IAM for authentication, including [AWS CLI profiles](https://docs.aws.amazon.com/cli/v1/userguide/cli-configure-files.html#cli-configure-files-format-profile) and temporary security credentials via [AWS Session credentials](https://docs.aws.amazon.com/cli/v1/userguide/cli-configure-envvars.html). For example, the following can be set in the active session or in the environment file:

```bash
export AWS_ACCESS_KEY_ID=ACCESS7EXAMPLE
export AWS_SECRET_ACCESS_KEY=wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY
export AWS_SESSION_TOKEN=AQoEXAMPLE4aoAH0gNCAPy...truncated...WJOgQs8IZZaIv2BXIa2R4O
export AWS_REGION=us-east-1
```

## Single Account/Region Limitation

**Important**: Local deployments are limited to a **single AWS account and region**. This is a fundamental constraint of the local deployment architecture.

### Automatic Region Override

When using local deployments, Seed-Farmer automatically overrides all target regions in your manifests to use your current AWS session's region. This means:

- **No manifest changes required**: Your existing multi-region manifests work without modification
- **Automatic conversion**: All modules deploy to your session's region regardless of manifest settings
- **Simplified development**: Focus on module logic without worrying about region configuration

### Example Behavior

If your manifest specifies multiple regions:

```yaml
targetAccountMappings:
  - alias: primary
    accountId: 123456789012
    regionMappings:
      - region: us-east-1  # Will be overridden
      - region: us-west-2  # Will be overridden
      - region: eu-west-1  # Will be overridden
```

During local deployment, all modules will deploy to your current AWS session's region (e.g., `us-west-2` if that's your configured region).

## Local Deployment Process

### 1. Verify Prerequisites

Ensure Docker is running and AWS credentials are configured:

```bash
# Check Docker
docker info

# Check AWS credentials and region
aws sts get-caller-identity
aws configure get region
```

### 2. Enable Local Mode

Use the `--local` flag to enable local deployments:

```bash
seedfarmer apply manifests/examples/deployment.yaml --local --env-file .env
```

### 3. Local Deployment Flow

When you run a local deployment, Seed-Farmer:

1. **Creates a bundle**: Packages your module code and data files
2. **Starts Docker container**: Uses the specified CodeBuild image
3. **Mounts the bundle**: Makes your code available in the container
4. **Executes deployspec**: Runs your module's deployment commands
5. **Captures outputs**: Stores metadata and logs locally and in AWS
6. **Cleans up**: Removes temporary containers and files

### 4. Monitor Progress

Local deployments provide real-time output:

```bash
seedfarmer apply manifests/examples/deployment.yaml --local
# Output shows Docker container execution in real-time
# No need to check CloudWatch logs
```

### 5. Verify Deployment

Check your deployment status:

```bash
seedfarmer list deployments
seedfarmer list modules -d examples
```

### 6. Iterate and Test

Make changes to your modules and redeploy:

```bash
# Edit your module code
vim modules/mymodule/app.py

# Redeploy with local execution
seedfarmer apply manifests/examples/deployment.yaml --local
```

### 7. Clean Up

Destroy the deployment when finished:

```bash
seedfarmer destroy examples --local
```

These files will be included in the module bundle and available to the module during deployment.

## Conclusion

Local deployments are a powerful way to test changes to your Seed-Farmer projects before deploying them to production environments. By following the steps in this guide, you can set up a local development environment and iterate on your modules quickly and safely.
