# Sequence Diagrams

These sequence diagrams represent the order of processing of important workflows within Seed-Farmer.

## Deployment Workflow

The [deployment workflow](./deployment-workflow.md) is an end-to-end sequence of what Seed-Farmer does to deploy the modules in a deployment.

## Module Deployment Strategies

The [module deployment strategies](./module-deployment-strategies.md) refer to how Seed-Farmer will leverage one of two options available:

- [Remote Deployments](../guides/remote-deployments.md) - on AWS Codebuild
- [Local Deployments](../guides/local-deployments.md)  - on AWS Codebuild Local images running on local compute

Both of these strategies deploy to module IaC to an AWS Account.  The _local_ and _remote_ refer to where the codebuild job executes.

## SSM Metadata Tracking

Seed-Farmer [stores and tracks metadata](./ssm-metadata-tracking.md) by using [AWS SSM parameters](https://docs.aws.amazon.com/systems-manager/latest/userguide/systems-manager-parameter-store.html).
The data stored and the order in which they are stored indicate to Seed-Farmer the state of the deployments.  
