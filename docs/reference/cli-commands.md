# CLI Commands

This page provides a reference for all Seed-Farmer CLI commands.  

It is recommended to use the `--help` command to get detailed information about each CLI command and option that is available in your Seed-Farmer version.

```bash
> seedfarmer --version
seedfarmer, version 7.0.12


> seedfarmer --help   
Usage: seedfarmer [OPTIONS] COMMAND [ARGS]...

  Seed-Farmer CLI interface

Options:
  --version  Show the version and exit.
  --help     Show this message and exit.

Commands:
  apply          Apply manifests to a Seed-Farmer managed deployment
  bootstrap      Bootstrap (initialize) a Toolchain or Target account
  bundle         Manage the bundle in a module deployment execution
  destroy        Destroy a Seed-Farmer managed deployment
  init           Initialize a project or module
  list           List the relative data (module or deployment)
  metadata       Manage the metadata in a module deployment execution
  projectpolicy  Fetch info about the project policy.
  remove         Top Level command to support removing module metadata
  seedkit        Top Level command to support seedkits in Seed-Farmer
  store          Top Level command to support storing module information
  taint          Top Level command to support adding a taint to a...
  version        Get the version Seed-Farmer

```

## Bootstrap Commands

These commands are used to bootstrap the toolchain and target accounts.

### bootstrap toolchain

Bootstrap a toolchain account with the necessary IAM roles and permissions.

```bash
seedfarmer bootstrap toolchain \
  --project PROJECT_NAME \
  --trusted-principal PRINCIPAL_ARN
```

### bootstrap target

Bootstrap a target account with the necessary IAM roles and permissions.

```bash
seedfarmer bootstrap target \
  --project PROJECT_NAME \
  --toolchain-account ACCOUNT_ID \
```

!!! note "Bootstrap Both Toolchain and Target Accounts"
    When bootsrapping a single account as both the toolchain account and the target account, use the `--as-target` command: <br\>
    `seedfarmer bootstrap toolchain --project PROJECT_NAME --trusted-principal PRINCIPAL_ARN --as-target`

## Init Commands

### init project

Initialize a new module.

```bash
seedfarmer init project 
```

### init module

Initialize a new module.

```bash
seedfarmer init module 
```

## Deployment Commands

These commands are used to deploy and destroy a deployment.  

### apply

Apply a deployment manifest to deploy modules.

```bash
seedfarmer apply MANIFEST_PATH 
```

### destroy

Destroy a deployment.

```bash
seedfarmer destroy DEPLOYMENT_NAME 
```

## List Commands

The commands are frequently used to interrogate deployments and modules.  It is recommended to explore these commands as they do not alter the deployments.

!!! warning "Toolchain Region"
    The toolchain account is region-specific.  If you cannot get your deployment or module information, be sure to pass the `--region` of the toolchain account to assure Seed-Farmer interrogates the proper region.

### list deployments

List all deployments in a project.

```bash
seedfarmer list deployments 

seedfarmer list modules -d DEPLOYMENT_NAME

seedfarmer list moduledata -d DEPLOYMENT_NAME -g GROUP_NAME -m MODULE_NAME

seedfarmer list allmoduledata -d DEPLOYMENT_NAME 
```

## Seedkit Commands

These commands are provided as a convenience, but Seed-Farmer will auto-deploy the SeedKit on first deploy.  These commands are used to update the SeedKit when necessary.

### seedkit deploy

Deploy a seedkit in the specified account and region.

```bash
seedfarmer seedkit deploy PROJECT_NAME 
```

### seedkit destroy

Destroy a seedkit in the specified account and region.

```bash
seedfarmer seedkit destroy PROJECT_NAME 
```

## Metadata Commands

These commands help manage metadata for modules.

!!! warning "Only in deployspec.yaml"
    These commands will only work when executed in the `deployspec.yaml`.  

### metadata add

Module metadata can be augmented with additional data.  This is the recommended path for Terraform modules.

```bash
seedfarmer metadata add
```

### metadata convert

Convert CDK output to Seed-Farmer metadata.

```bash
seedfarmer metadata convert --file FILE
```

### metadata depmod

Get the fully resolved deployment name of the module.

```bash

seedfarmer metadata depmod

```

### metadata paramvalue

Get the parameter value based on the suffix.

```bash

seedfarmer metadata paramvalue --suffix SUFFIX

```
