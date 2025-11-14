---
title: Getting Started
---

This section provides instructions to get started with Seed-Farmer and be ready to deploy an application.

Seed-Farmer can run on local compute and on compute within a CI/CD pipeline -- the setup requirements are the same.

- **Installation** -  Seed-Farmer needs to be installed where the CLI will be invoked.  It is a one-time event for new compute resources.

- **Bootstrapping** - the steps necessary to prepare your AWS Accounts to use Seed-Farmer.  It is a one-time event for each AWS account to be used for deploying AWS Resources.

Seed-Farmer uses a **toolchain account** and a **target account**.  Though named as _account_, these are region-specific in context:  the toolchain account and target account store their data in their designated region, respectively.

![AccountMulti](../static/sf-diagrams.drawio)

The most basic setup is to configure your toolchain account and target account to be the same.
This is a simple representation of the account / region setup.  The **[Bootstrapping](bootstrapping.md)** guide will follow this setup.

![AccountSingle](../static/sf-diagrams.drawio)

Please review the [Concepts](../concepts/index.md) in detail.

## Installation

Before you can use Seed-Farmer, you need to install it and its dependencies. The [Installation](installation.md) guide walks you through the process of setting up Seed-Farmer.

## Bootstrapping

Before you can deploy with Seed-Farmer, you need to bootstrap your AWS accounts. The [Bootstrapping](bootstrapping.md) guide explains how to set up your toolchain and target accounts with the necessary IAM roles and permissions.

## Quick Start

Once you have Seed-Farmer installed, the [Quick Start](quick-start.md) guide will help you deploy your first project. This guide provides a step-by-step walkthrough of creating and deploying a simple project.

## Next Steps

After completing the getting started guides, you'll have a basic understanding of how to use Seed-Farmer. From here, you can:

- Learn more about the [Concepts](../concepts/index.md) behind Seed-Farmer
- Explore the [Guides](../guides/index.md) for common tasks
- Refer to the [Reference Documentation](../reference/index.md) for detailed information on CLI commands, manifests, and module development
