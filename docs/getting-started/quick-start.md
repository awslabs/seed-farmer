# Quick Start Guide for Seed-Farmer

This quick start guide will help you get up and running with Seed-Farmer quickly. It provides a step-by-step walkthrough of creating and deploying a simple project using [public modules](../modules/index.md).

!!! note
    This is an abbreviated version of the deployment process. For a more detailed guide, see the [Deployment Guide](../guides/project-development.md).

## Prerequisites

Before you begin, make sure you have:

- Installed Seed-Farmer (see [Installation](installation.md))
- AWS credentials configured
- AWS CDK bootstrapped in your account/region

## Create a Simple Project

Create a directory and navigate to that directory.

We will create the skeleton of a new project named `myproject`.

```bash
seedfarmer init project --project-name myproject
```

A default project structure is provided.

```bash
└── myproject
    ├── manifests
    │   └── examples
    │       └── deployment.yaml
    ├── modules
    │   └── examples
    │       └── README
    ├── README.md
    ├── resources
    │   └── sample-permissionboundary.yaml
    └── seedfarmer.yaml

```

The is a valid project structure with `seedfarmer.yaml` at the root of the project.  All references to filepaths are relative to `seedfarmer.yaml`.

The `modules` , `manifests` , and `resources` directories are only for logical separation and can be used at discretion.  In this sample case, they will not be needed. But the `deployment.yaml` is critical for use.  We will move that up to be parallel with `seedfarmer.yaml`, and remove the extra directories.

```bash
cd myproject

mv manifests/examples/deployment.yaml .
rm -rf manifests modules resources
```

The resulting structure now looks like this:

```bash
└── myproject
    ├── deployment.yaml
    ├── README.md
    └── seedfarmer.yaml

```

The `deployment.yaml` contains the information necessary for Seed-Farmer to AWS Sessions to access the AWS Accounts via the bootstrap roles, the paths to the definitions of the module(s) to deploy, and other deployment-specific information.  The provided `deployment.yaml` has a large, commented-out section for reference.  In our use case, we do not need this, so we can replace it with the minimal information necessary.

```bash
mv deployment.yaml deployment.orig
touch deployment.yaml
```

In the newly created `deployment.yaml`, add the following yaml content:

```yaml
name: verysimple    # The name of my deployment
toolchainRegion: <REPLACE WITH REGION>  # The toolchain region
forceDependencyRedeploy: True
groups:
    - name: group1   # A Logical name of the module group
      path: simple-modules.yaml   # the module definition via relative path
targetAccountMappings:
    - alias: primary
      accountId: <REPLACE WITH ACCOUNT IT>  # The target account the module will go to 
      default: true
      regionMappings:
        - region: <REPLACE WITH REGION> # The target region the module will go to 
          default: true  
```

## Add a Module

In the `deployment.yaml` a module manifest `simple-modules.yaml` was referred.  It creates the module configuration that we want to deploy.  We will deploy one module, the module code will be sourced from a [public module repository](../modules/idf-modules/index.md).

Add the new module manifest.

```bash
touch simple-modules.yaml
```

Populate it with a module definition.

```yaml
name: simplebucket
path: git::https://github.com/awslabs/idf-modules.git//modules/storage/buckets?ref=release/1.13.0&depth=1
parameters:
  - name: EncryptionType
    value: SSE
  - name: RetentionType
    value: DESTROY
```

The above module definition will deploy an S3 bucket in the target account.  The code is pull directly from the public IDF Github repository.

```bash
└── myproject
    ├── deployment.yaml
    ├── README.md
    ├── seedfarmer.yaml
    └── simple-modules.yaml
```

## Deploy the Sample Project

Now the deployment is ready for deployment.

```bash
seedfarmer apply deployment.yaml
```

Since this is the first deployment for the project `myproject`, Seed-Farmer will add the necessary artifacts to support the project (a generic [module role](../concepts/architecture.md/#3-module-role), the [SeedKit](../concepts/architecture.md#seedkit-infrastructure), and a [Seed-Farmer Artifacts](../concepts/architecture.md/#seed-farmer-artifacts) bucket).  These items are created once and reused by all deployments in the project.

You should see output similar to:

```bash

Modules Deployed: verysimple                                
┏━━━━━━━━━┳━━━━━━━━━━━┳━━━━━━━━━━━━┳━━━━━━━━┳━━━━━━━━━━━━━━┓
┃ Account ┃ Region    ┃ Deployment ┃ Group  ┃ Module       ┃
┡━━━━━━━━━╇━━━━━━━━━━━╇━━━━━━━━━━━━╇━━━━━━━━╇━━━━━━━━━━━━━━┩
│ primary │ us-east-1 │ verysimple │ group1 │ simplebucket │
└─────────┴───────────┴────────────┴────────┴──────────────┘
To see all deployed modules, run seedfarmer list modules -d verysimple
```

## Verify the Deployment

You can verify the deployment by checking the AWS resources created in your account, or by using the Seed-Farmer CLI:

```bash
seedfarmer list deployments


Deployment    
Names         
┏━━━━━━━━━━━━┓
┃ Deployment ┃
┡━━━━━━━━━━━━┩
│ verysimple │
└────────────┘
```

```bash
seedfarmer list modules -d verysimple 

Deployed Modules                                            
┏━━━━━━━━━┳━━━━━━━━━━━┳━━━━━━━━━━━━┳━━━━━━━━┳━━━━━━━━━━━━━━┓
┃ Account ┃ Region    ┃ Deployment ┃ Group  ┃ Module       ┃
┡━━━━━━━━━╇━━━━━━━━━━━╇━━━━━━━━━━━━╇━━━━━━━━╇━━━━━━━━━━━━━━┩
│ primary │ us-east-1 │ verysimple │ group1 │ simplebucket │
└─────────┴───────────┴────────────┴────────┴──────────────┘

```

And to check if there are any module outputs, you can get that information (note, in the below, [jq](https://github.com/jqlang/jq) is used to parse the output since is it json...but is not necessary to use).

```bash
seedfarmer list allmoduledata -d verysimple | jq .
```

This returns all the module metadata:

```json
{
  "group1-simplebucket": {
    "ArtifactsBucketName": "myproject-verysimple-artifacts-bucket-074ff5b4-9a01f6e68e54b",
    "CloudWatchLogStream": "/aws/codebuild/codeseeder-myproject/codeseeder-random/39ace228-9956-416b-bc58-0887ffe09824",
    "CloudWatchLogStreamArn": "arn:aws:logs:us-east-1:123456789012:log-group:/aws/codebuild/codeseeder-myproject:log-stream:codeseeder-random/REDACTED",
    "CodeBuildBuildUrl": "https://us-east-1.console.aws.amazon.com/codebuild/home?region=us-east-1#/builds/codeseeder-myproject:REDACTED/view/new",
    "FullAccessPolicyArn": "arn:aws:iam::123456789012:policy/myproject-verysimple-group1-simplebucket-us-east-1-123456789012-full-access",
    "LogsBucketName": "myproject-verysimple-logs-bucket-074ff5b4-9a01f6e68e54bd9784",
    "ModuleDeploymentRoleName": "myproject-verysimple-us-east-1-deployment-role",
    "ReadOnlyPolicyArn": "arn:aws:iam::123456789012:policy/myproject-verysimple-group1-simplebucket-us-east-1-123456789012-readonly-access",
    "Seed-FarmerDeployed": "7.0.12",
    "Seed-FarmerModuleCommitHash": "589a5a5606e859929e7c4d88ac138b7962ed0cff"
  }
}
```

## Clean Up

To clean up the resources created by the deployment:

```bash
seedfarmer destroy verysimple

Modules Destroyed: verysimple                               
┏━━━━━━━━━┳━━━━━━━━━━━┳━━━━━━━━━━━━┳━━━━━━━━┳━━━━━━━━━━━━━━┓
┃ Account ┃ Region    ┃ Deployment ┃ Group  ┃ Module       ┃
┡━━━━━━━━━╇━━━━━━━━━━━╇━━━━━━━━━━━━╇━━━━━━━━╇━━━━━━━━━━━━━━┩
│ primary │ us-east-1 │ verysimple │ group1 │ simplebucket │
└─────────┴───────────┴────────────┴────────┴──────────────┘

```

This will destroy all the modules in the deployment in the reverse order of their deployment.

## Next Steps

Now that you've deployed your first project with Seed-Farmer, you can:

- Explore the [Concepts](../concepts/index.md) behind Seed-Farmer
- Learn how to [Create Your Own Modules](../guides/module-development.md)
- Check out the [Guides](../guides/index.md) for common tasks
