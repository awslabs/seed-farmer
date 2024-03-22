# Deployment Step-By-Step

This is a logical step-by-step guide to create and deploy a `seedfarmer` project.

## Create a Virtual environment

```bash
python3 -m venv .venv
source .venv/bin/activate
```

##  Install the requirements

```bash
pip install seed-farmer
```

## Bootstrap the Toolchain and Target Accounts
Please see [Bootstrapping](bootstrapping)

## Bootstrap the CDK in Each Account/Region
`seedfarmer` uses the concepts of `toolchain accounts` and `target accounts`.  `Modules` can deployed in any account/region combination.  
Identify EACH account/region of the `target accounts` to be used and bootstrap the AWS CDK in each region.
We use AWS CDK V2 as the standard CDK as it is compatible with V1 - see [HERE](https://docs.aws.amazon.com/cdk/v2/guide/bootstrapping.html).
```bash
cdk bootstrap aws://<account>/<region>
```


## Create a New Project or Clone Existing
You have the option of either:
1. Creating a new project (see [Project Development](project_development.md))
2. Cloning an existing `seedfarmer` compliant Git Repo

If cloning, skip to [Deploying Modules](deploying_modules)


## Add Dockerhub Support if needed
To avoid throttling from `DockerHub` when building images, you should create a parameter/re-use an existing parameter in `AWS Secrets Manager` to store your DockerHub username and password.  There is a corresponding `manifest` parameter that corresponds to the AWS Secret ([see here](deployment_manifest)).

## Create New Project
Please see [Project Development](project_development)

## Create Modules
Please see [Module Development](module_development)


(deploying_modules)=
## Deploy Modules

Manifests should be located at <<project>>/manifests/*.  Change to the project root directory
```bash
cd <<project_root>>
```

Use the [CLI](cli_commands.md) to deploy.
Below is the command to deploy the modules using the main manifest `deployment.yaml`:

```bash
seedfarmer apply manifests/<<somename>>/deployment.yaml
```

## Destroy Modules
`seedfarmer` uses the manifests and GitOps.  To `destroy` a module but leave the other modules intact, just comment out the module definition and apply
```bash
seedfarmer apply manifests/<<somename>>/deployment.yaml
```

## Destroy Deployment
Below is the command to destroy all the modules related to a deployment:

```bash
seedfarmer destroy <<DEPLOYMENT_NAME>>
```



