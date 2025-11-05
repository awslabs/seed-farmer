---
title: Project Development
---

This guide covers how to structure and organize Seed-Farmer projects effectively. It focuses on project-level organization, directory structure, and high-level development patterns.

## Understanding Seed-Farmer Projects

A Seed-Farmer project is a collection of Infrastructure as Code (IaC) modules organized using [GitOps](https://opengitops.dev/) principles. Projects use manifest files to define deployments and orchestrate the deployment of modules across multiple AWS accounts and regions.

### Key Concepts

- **Project**: The top-level container that defines the overall scope and configuration
- **Deployment**: A specific instance of deployed modules (e.g., dev, staging, prod)
- **Groups**: Logical collections of related modules within a deployment
- **Modules**: Individual IaC components that deploy specific AWS resources
- **Manifests**: YAML files that define the configuration and relationships

## Project Structure

A well-organized Seed-Farmer project follows this recommended structure:

```bash
project-root/
├── seedfarmer.yaml           # Project configuration file
├── .env                      # Environment variables
├── README.md                 # Project documentation
├── manifests/                # Deployment and module manifests
│   ├── deployment.yaml       # Main deployment manifest
│   ├── networking-modules.yaml
│   ├── compute-modules.yaml
│   ├── storage-modules.yaml
│   └── database-modules.yaml
├── modules/                  # Custom module code (optional)
│   ├── networking/
│   │   └── custom-vpc/
│   │       ├── README.md
│   │       ├── deployspec.yaml
│   │       ├── modulestack.yaml (optional)
│   │       └── app.py
│   └── compute/
│       └── custom-eks/
│           ├── README.md
│           ├── deployspec.yaml
│           └── app.py
└── data/                     # Data files for modules (optional)
    ├── config/
    └── scripts/
```

### Project Configuration File

Every Seed-Farmer project must have a `seedfarmer.yaml` file at the root and must the the project name defined:

```yaml
project: myprojectname

```

This file defines the project name, which is used throughout the deployment process for resource naming and organization.  It is also used as the reference point for all relative paths.

- **project** (required) - defines the project name for all artifacts and deployments
- **description** (optional) - a textual description of the project
- **project_policy_path** (optional) - an override of the project policy provided by Seed-Farmer
- **manifest_validation_fail_on_unknown_fields** (optional) - a boolean field indicating to Seed-Farmer to stop processing if a named key in the manifests is not apart of the defined keys Seed-Farmer expects.  This is `false` by default.

## Creating a New Project

### Using the CLI (Recommended)

Create a new project using the Seed-Farmer CLI:

```bash
# Create a new project with a specific name
seedfarmer init project --name myprojectname

# Navigate to the project directory
cd myprojectname
```

This command creates the basic project structure with template files.

### Manual Setup

If you prefer to set up manually:

```bash
# Create project directory
mkdir myprojectname
cd myprojectname

# Create seedfarmer.yaml
echo "project: myprojectname" > seedfarmer.yaml

# Create directory structure
mkdir -p manifests modules data
```

## Module Sources

Seed-Farmer supports multiple ways to source modules, providing flexibility in how you organize and distribute your infrastructure code:

### Local Filesystem Modules

Reference modules from your local project directory:

```yaml
name: custom-networking
path: modules/networking/custom-vpc/
targetAccount: primary
```

### Git Repository Modules

Reference modules from Git repositories using [Terraform-style syntax](https://developer.hashicorp.com/terraform/language/modules/sources#generic-git-repository):

```yaml
# From a specific tag/release
name: vpc-network
path: git::https://github.com/awslabs/idf-modules.git//modules/network/basic-cdk?ref=v1.14.0&depth=1
targetAccount: primary

# From a specific branch
name: experimental-module
path: git::https://github.com/myorg/custom-modules.git//modules/compute/experimental?ref=feature-branch&depth=1
targetAccount: primary

# From a specific commit
name: stable-module
path: git::https://github.com/myorg/modules.git//modules/storage/s3?ref=abc123def&depth=1
targetAccount: primary
```

### Archive-Based Modules

Reference modules from ZIP or TAR archives over HTTPS:

```yaml
# From a GitHub release archive
name: archived-module
path: archive::https://github.com/awslabs/idf-modules/archive/refs/tags/v1.14.0.tar.gz?module=modules/network/basic-cdk
targetAccount: primary

# From a custom archive location
name: custom-archive
path: archive::https://releases.mycompany.com/modules/v2.1.0/networking-modules.zip?module=vpc-module
targetAccount: primary
```

!!! tip "Module Source Best Practices"
    - **Use specific versions/tags** for production deployments to ensure reproducibility
    - **Use local modules** for custom code specific to your project
    - **Use Git modules** for shared modules across multiple projects
    - **Use archive modules** for distributing modules without Git access

## Working with Data Files

Modules can include additional data files beyond their core infrastructure code using the `dataFiles` field in module manifests. This is useful for configuration files, scripts, certificates, or other assets needed during deployment.

```yaml
name: application-module
path: modules/applications/webapp/
targetAccount: primary
dataFiles:
  - filePath: data/config/app-config.json
  - filePath: data/scripts/setup.sh
  - filePath: data/certificates/ca-cert.pem
parameters:
  - name: config-file
    value: app-config.json
```

For detailed information about data files, including project structure, accessing files in deployspec, best practices, and common use cases, see the [Working with Data Files](../reference/manifests.md#working-with-data-files) section in the Manifests Reference.

## Environment Variables

Create an `.env` file to store environment variables needed for your deployment:

```bash
# Account IDs
PRIMARY_ACCOUNT=123456789012
SECONDARY_ACCOUNT=210987654321

# Environment-specific settings
ENVIRONMENT=production
REGION=us-west-2

# Sensitive values (consider using AWS Secrets Manager instead)
DB_PASSWORD=your-secure-password
```

These environment variables can be referenced in your deployment manifests. See the [Manifests Reference](../reference/manifests.md#parameters-and-environment-variables) for detailed parameter configuration options.

## Multi-Environment Development

Seed-Farmer supports multi-environment development patterns. For detailed information about managing dependencies, deployment manifests, and environment-specific configurations, see the [Manifests Reference](../reference/manifests.md).

## Best Practices

### Project Organization

- **Use a consistent directory structure**: Follow the recommended project structure to make it easier to navigate and understand your project
- **Use version control**: Track changes to your modules and manifests with Git
- **Document your project**: Provide clear README files explaining the project structure and deployment process
- **Separate environments**: Use different deployment manifests for different environments (dev, staging, prod)

### Module Source Management

- **Pin to specific versions**: Use specific tags or commits for production deployments to ensure reproducibility
- **Use semantic versioning**: When creating your own modules, follow semantic versioning practices
- **Test module updates**: Always test module updates in non-production environments first
- **Organize by functionality**: Group related modules together logically (networking, compute, storage, etc.)

### Security

- **Use environment variables**: Store sensitive information like account IDs in environment variables, not in manifest files
- **Apply least privilege**: Use IAM permissions boundaries and minimal permissions for deployment roles
- **Secure data files**: Be cautious with data files containing sensitive information; consider using AWS Secrets Manager instead

For detailed information about manifests, parameters, dependencies, and deployment patterns, see the [Manifests Reference](../reference/manifests.md).
