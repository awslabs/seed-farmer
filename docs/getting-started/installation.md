---
title: Installation
---

This guide will walk you through the process of installing Seed-Farmer and its dependencies.

## Prerequisites

Before installing Seed-Farmer, ensure you have the following prerequisites:

- **Python >=3.11** - Seed-Farmer runs in python
- **AWS CLI** - For configuring credentials on compute
- **AWS CDK and CDK Bootstrap** (recommended) - the majority of Seed-Farmer [Public Modules](../modules/index.md) use AWS CDkv2
- **Python Management Tool** - [uv](https://docs.astral.sh/uv/) or [pip](https://pypi.org/project/pip/)

## Installing Seed-Farmer

Seed-Farmer supports [uv](https://docs.astral.sh/uv/) and [pip](https://pypi.org/project/pip/) for installation for use.

It is recommended to [install uv](https://docs.astral.sh/uv/getting-started/installation/) as the primary installation tool.

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### Using uv

Install Seed-Farmer as a tool.

```bash
## you can use your preferred version of python

uv tool install --python 3.13 seed-farmer 

```

You can pin to a particular version by referring to the version in the install ( see the [pypi release history](https://pypi.org/project/seed-farmer/#history) )

### Using pip

Install Seed-Farmer using [pip](https://pypi.org/project/pip/)

```bash
python -m venv .venv
source .venv/bin/activate
pip install seed-farmer
```

### From Source

You can also install Seed-Farmer from source using your installation of choice:

```bash
git clone https://github.com/awslabs/seed-farmer.git
cd seed-farmer

## Via Source Code with uv 
uv pip install -e .

## -- OR -- 

## Via Source Code with pip 
pip install -e .
```

## Verifying the Installation

To verify that Seed-Farmer is installed correctly, run:

```bash
seedfarmer --version

seedfarmer, version 7.0.12
```

This should display the version of Seed-Farmer that you have installed.

## Setting Up Your Environment

### AWS CLI and Credentials

Install the [AWS CLI](https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html) and configure your preferred method of [AWS Credentials](https://docs.aws.amazon.com/cli/v1/userguide/cli-configure-files.html).

### AWS CDK

Run the [AWS CDK Bootstrap](https://docs.aws.amazon.com/cdk/v2/guide/bootstrapping.html) in each target account using the [AWS CDK](https://docs.aws.amazon.com/cdk/v2/guide/getting-started.html).

## Next Steps

Now that you have Seed-Farmer installed, you can:

- Learn how to [Bootstrap](bootstrapping.md) your AWS accounts for Seed-Farmer
- Follow the [Quick Start](quick-start.md) guide to deploy your first project
- Explore the [Concepts](../concepts/index.md) behind Seed-Farmer
