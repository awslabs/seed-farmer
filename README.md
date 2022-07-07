# Seed-Farmer

Seed-Farmer (seedfarmer) is an opensource orchestration tool that works with AWS CodeSeeder (see [github](https://github.com/awslabs/aws-codeseeder) or [docs](https://aws-codeseeder.readthedocs.io/en/latest/)) and acts as an orchestration tool modeled after [GitOps deployments](https://www.gitops.tech/).  It has a CommandLine Interface (CLI) based in Python. 

It leverages modular code deployments ([see modules](https://seed-farmer.readthedocs.io/en/latest/usage.html#module-development)) leveraging [manifests](https://seed-farmer.readthedocs.io/en/latest/manifests.html) and [deployspecs](https://seed-farmer.readthedocs.io/en/latest/deployspec.html), keeping track of changes and applying changes as need / detected.


## Architecture
Seed-Farmer does not create its own deployments, rather it helps to deploy YOUR modules by acting as the broker between your module code and the AWS Cloud via AWS CodeSeeder.

![Seed-Farmer](docs/source/_static/SeedFarmer.png)

Steps:
1. Invoke `seedfarmer` CLI
2. `seedfarmer` reads/writes deployment metadata with AWS Systems Manager
3. `seedfarmer` invokes AWS IAM to create module-specific roles, attaching the proper least-privilege policies
4. `seedfarmer` leverages `AWS CodeSeeder` for remote deployment on AWS CodeBuild
5. `AWS CodeSeeder` prepares AWS CodeBuild 
6. AWS CodeBuild via `AWS CodeSeeder` inspects and fetches data from AWS SecretsManager (if necessary)
7. AWS CodeBuild via `AWS CodeSeeder` executes the custom `deployspec` for the module
8. AWS CodeBuild via `AWS CodeSeeder` updates AWS Systems Manager with completed module metadata
9. `seedfarmer` updates deployment metadata in AWS Systems Manager

## Getting Started
The Seed-Farmer library is available on PyPi.  Install the library in a python virtual environment.


```bash
python3 -m venv .venv
source .venv/bin/activate
pip install seed-farmer
```

A [project](https://seed-farmer.readthedocs.io/en/latest/project_structure.html) is now necessary to begin create modules.  
