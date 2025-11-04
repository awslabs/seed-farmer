# Seed-Farmer Documentation

Welcome to the official documentation for Seed-Farmer, a Python-based CI/CD library that leverages the [GitOps](https://opengitops.dev/) paradigm to manage deployed code.

## What is Seed-Farmer?

Seed-Farmer is a deployment framework that supports AWS CDK, CloudFormation, Terraform, and other infrastructure-as-code tools. It uses declarative manifests to define deployable code modules and manages the state of deployed code, detecting and applying changes as needed.

Key features include:

- **Multi-Account Support**: Deploy across multiple AWS accounts with proper IAM role assumption
- **Security-First**: Least-privilege IAM roles and permissions boundaries
- **Metadata Sharing**: Modules can export metadata for use by dependent modules
- **Module Dependency Management**: Modules that share metadata are properly managed for application integrity
- **Flexible Parameterization**: Support for various parameter sources including environment variables, [AWS SSM Parameter Store](https://docs.aws.amazon.com/systems-manager/latest/userguide/systems-manager-parameter-store.html), and [AWS Secrets Manager](https://docs.aws.amazon.com/secretsmanager/latest/userguide/intro.html)

- **Tooling Agnostic**: Support for various IaC tools (CDK, CloudFormation, Terraform)
- **[GitOps](https://opengitops.dev/) Workflow**: Code-driven deployments with state management

## Concepts

Seed-Farmer organizes deployments within scoped hierarchies to insulate artifacts from one another, following the principals of least-privilege and dedicated access roles.  Within a scoped unit, SeedFarmer artifacts are named according to a structured pattern, assuring a unique name to prevent collisions.

- **Project**: Represents all deployments scoped to a single logical name
- **Deployment**: Represents all modules leveraging AWS resources in one or many accounts
- **Group**: Contains modules that can be deployed concurrently (no inter-dependencies)
- **Module**: The actual deployable unit of code

Seed-Farmer supports multi-account / multi-region deployments scoped to individual modules within a project.

Please see the [Concepts](concepts/index.md) page for an in-depth explanation.

## Documentation Structure

This documentation is organized into the following sections:

- **Getting Started**: Installation and initial setup guides
- **Concepts**: Core concepts and architecture
- **Guides**: How-to guides for common tasks
- **Sequence Diagrams**: Sequence diagrams of important processes with SeedFarmer
- **Reference**: Detailed reference documentation for CLI commands, manifests, and module development
- **Public Modules**: Listing of Seed-Farmer compliant OpenSource modules ready for use
- **AI Support**: Artificial Intelligence support for Seed-Farmer module development

## Next Steps

To get started with Seed-Farmer, please see the [Getting Started](getting-started/index.md) Section which includes:

- [Installation](getting-started/installation.md): Install Seed-Farmer and its dependencies
- [Quick Start](getting-started/quick-start.md): Deploy your first project with Seed-Farmer
- [Bootstrapping](getting-started/bootstrapping.md): Set up your AWS accounts for Seed-Farmer
