---
title: Guides
---

This section provides how-to guides for common tasks with Seed-Farmer. These guides are designed to help you accomplish specific goals and solve common problems.

## Project Development

The [Project Development](project-development.md) guide covers how to structure and organize Seed-Farmer projects. It includes best practices for project organization, managing multi-environment deployments, working with dependencies between modules, and using environment variables and remote modules effectively.

## Module Development

The [Module Development](module-development.md) guide provides comprehensive information on creating individual modules for Seed-Farmer. It covers required files (deployspec.yaml, README.md), optional files (modulestack.yaml), deployspec structure and parameters, metadata management, and best practices for creating reusable, generic modules.

## Local Deployments

The [Local Deployments](local-deployments.md) guide explains how to deploy Seed-Farmer projects locally for development and testing purposes. It covers environment setup, working with local and remote modules, using data files, and best practices for iterative development and testing before production deployment.

## Remote Deployments

The [Remote Deployments](remote-deployments.md) guide covers deploying Seed-Farmer projects using AWS CodeBuild in the cloud. It explains how Seed-Farmer leverages the Seedkit for remote deployments, working with different CodeBuild images, image overrides, and the deployment process in AWS environments.

## Common Tasks

### Creating a New Module

To create a new module, you can use the `seedfarmer init module` command:

```bash
seedfarmer init module -g mygroup -m mymodule
```

This will create a new module in the `modules/mygroup/mymodule` directory with the necessary files.

### Deploying a Project

To deploy a project, you can use the `seedfarmer apply` command:

```bash
seedfarmer apply manifests/mydeployment/deployment.yaml --env-file .env
```

This will deploy the modules defined in the deployment manifest.

### Destroying a Deployment

To destroy a deployment, you can use the `seedfarmer destroy` command:

```bash
seedfarmer destroy mydeployment --env-file .env
```

This will destroy all the modules in the deployment in the reverse order of their deployment.

## Advanced Topics

### Working with Multiple Accounts

Seed-Farmer supports deploying across multiple AWS accounts. The [Multi-Account Support](../concepts/multi-account.md) page explains how to configure and use this feature.

### Custom Module Development

For information on developing custom modules, see the [Module Development](module-development.md) reference.

### Troubleshooting

If you encounter issues with Seed-Farmer, check the [FAQ](../reference/faq.md) for common problems and solutions.
