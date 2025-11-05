---
title: Remote Deployments
---

This guide explains how Seed-Farmer executes remote deployments using AWS CodeBuild. Remote deployments are the default and recommended approach for deploying modules in production environments.

## How Remote Deployments Work

When you run `seedfarmer apply`, Seed-Farmer orchestrates deployments through AWS CodeBuild in your target AWS accounts. This provides several advantages:

- **Isolation**: Each module deploys in its own CodeBuild environment
- **Scalability**: Multiple modules can deploy in parallel
- **Auditability**: Complete deployment logs are captured in CloudWatch
- **Security**: Deployments run with least-privilege IAM roles
- **Consistency**: Standardized execution environment across all deployments

## The Remote Deployment Process

### 1. Bundle Creation

Seed-Farmer creates a deployment bundle containing:

- Your module's source code
- Data files (if specified)
- Project configuration (`seedfarmer.yaml`)
- Support scripts for mirrors and Docker credentials

### 2. CodeBuild Project Execution

For each module, Seed-Farmer:

- Uploads the bundle to S3
- Starts a CodeBuild project in the target account
- Executes your module's `deployspec.yaml` phases
- Captures outputs and metadata

### 3. CodeBuild Setup

CodeBuild environments are automatically configured with:

- Python virtual environment
- AWS credentials for the target account/region
- Module parameters as environment variables
- Docker registry authentication
- Package mirror configuration (if specified)

## AWS CodeBuild Integration

### Build Images

Seed-Farmer supports various CodeBuild images:

#### Default Image

- **Image**: `aws/codebuild/amazonlinux2-x86_64-standard:5.0`
- **Runtime**: Amazon Linux 2 with Python 3.11
- **Tools**: Pre-installed AWS CLI, Docker, common build tools

#### Image Overrides

You can override the build image at different levels:

**Global Override** (in deployment manifest):

```yaml
name: my-deployment
toolchainRegion: us-west-2
codebuildImage: aws/codebuild/amazonlinux2-x86_64-standard:4.0
```

**Module-Specific Override** (in module manifest):

```yaml
name: my-module
path: modules/compute/eks/
codebuildImage: aws/codebuild/amazonlinux2-x86_64-standard:5.0
```

#### Supported Images

Any AWS CodeBuild managed image is supported:

- `aws/codebuild/amazonlinux2-x86_64-standard:5.0` (default)
- `aws/codebuild/amazonlinux2-x86_64-standard:4.0`
- `aws/codebuild/amazonlinux2-aarch64-standard:3.0`
- `aws/codebuild/ubuntu-base:20.04`
- Custom images from ECR

### Compute Types

Control CodeBuild compute resources via the `build_type` parameter in your deployspec:

```yaml
# In deployspec.yaml
build_type: BUILD_GENERAL1_LARGE
```

**Available Options**:

- `BUILD_GENERAL1_SMALL`: 3 GB memory, 2 vCPUs
- `BUILD_GENERAL1_MEDIUM`: 7 GB memory, 4 vCPUs
- `BUILD_GENERAL1_LARGE`: 15 GB memory, 8 vCPUs
- `BUILD_GENERAL1_2XLARGE`: 145 GB memory, 72 vCPUs

## Package Mirrors and Registries

### PyPI Mirrors

Configure PyPI mirrors for Python packages:

```yaml
# In deployment manifest
name: my-deployment
pypiMirror: https://pypi.mycompany.com/simple/
pypiMirrorSecret: prod/pypi-credentials

# Or in module manifest
name: my-module
path: modules/compute/eks/
pypiMirror: https://pypi.mycompany.com/simple/
pypiMirrorSecret: prod/pypi-credentials
```

#### PyPI Mirror Authentication

For authenticated PyPI mirrors, store credentials in AWS Secrets Manager:

**Secret Structure**:

```json
{
  "pypi": {
    "username": "your-pypi-username",
    "password": "your-pypi-password"
  }
}
```

**Multiple Mirror Support**:
You can store multiple mirror credentials in a single secret:

```json
{
  "pypi": {
    "username": "internal-pypi-user",
    "password": "internal-pypi-password"
  },
  "artifactory": {
    "username": "artifactory-user", 
    "password": "artifactory-password"
  }
}
```

**Using Specific Keys**:
Reference specific keys within a secret using the `::` syntax:

```yaml
pypiMirrorSecret: prod/mirror-credentials::artifactory
```

### NPM Mirrors

Configure NPM mirrors for Node.js packages:

```yaml
# In deployment manifest
name: my-deployment
npmMirror: https://npm.mycompany.com/
npmMirrorSecret: prod/npm-credentials

# Or in module manifest
name: my-module
path: modules/compute/eks/
npmMirror: https://npm.mycompany.com/
npmMirrorSecret: prod/npm-credentials
```

#### NPM Mirror Authentication

For authenticated NPM mirrors, store credentials in AWS Secrets Manager:

**Basic Authentication**:

```json
{
  "npm": {
    "username": "your-npm-username",
    "password": "your-npm-password"
  }
}
```

**Token-Based Authentication**:

```json
{
  "npm": {
    "ssl_token": "your-npm-auth-token"
  }
}
```

**Multiple Registry Support**:

```json
{
  "npm": {
    "username": "internal-npm-user",
    "password": "internal-npm-password"
  },
  "artifactory": {
    "ssl_token": "artifactory-npm-token"
  }
}
```

**Using Specific Keys**:

```yaml
npmMirrorSecret: prod/registry-credentials::artifactory
```

#### Mirror Secret Configuration Levels

Mirror secrets can be configured at multiple levels with inheritance:

**Global Level** (applies to all accounts/regions):

```yaml
name: my-deployment
pypiMirror: https://pypi.internal.com/simple/
pypiMirrorSecret: global/pypi-credentials
npmMirror: https://npm.internal.com/
npmMirrorSecret: global/npm-credentials
```

**Account Level** (overrides global):

```yaml
targetAccountMappings:
  - alias: production
    accountId: 123456789012
    pypiMirrorSecret: prod/pypi-credentials
    npmMirrorSecret: prod/npm-credentials
```

**Region Level** (overrides account and global):

```yaml
targetAccountMappings:
  - alias: production
    accountId: 123456789012
    regionMappings:
      - region: us-east-1
        pypiMirrorSecret: prod-east/pypi-credentials
        npmMirrorSecret: prod-east/npm-credentials
```

**Module Level** (overrides all others):

```yaml
name: my-module
path: modules/compute/eks/
pypiMirrorSecret: module-specific/pypi-credentials
npmMirrorSecret: module-specific/npm-credentials
```

### AWS CodeArtifact

Seed-Farmer automatically configures CodeArtifact when available:

- Detects CodeArtifact domain and repository from seedkit outputs
- Configures pip and uv to use CodeArtifact
- Sets up authentication tokens automatically

## Docker Registry Authentication

### Automatic Docker Login

Seed-Farmer automatically handles Docker authentication:

- AWS ECR login for the target account
- Docker Hub authentication (if credentials provided)
- Custom registry authentication via secrets

### Docker Credentials Secret

Configure Docker Hub or custom registry credentials:

```yaml
# In deployment manifest
targetAccountMappings:
  - alias: production
    accountId: 123456789012
    parametersGlobal:
      dockerCredentialsSecret: prod/docker-credentials
```

The secret should contain:

```json
{
  "username": "your-docker-username",
  "password": "your-docker-password",
  "registry": "docker.io"
}
```

## Monitoring and Troubleshooting

### CloudWatch Logs

All deployment execution is logged to CloudWatch:

- **Log Group**: `/aws/codebuild/{project-name}`
- **Log Stream**: Contains build ID for easy identification
- **Retention**: Configurable (default: 30 days)

### Build Metadata

Seed-Farmer automatically captures build information:

- CodeBuild build URL
- CloudWatch log stream path
