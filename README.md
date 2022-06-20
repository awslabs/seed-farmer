# Seed-Farmer

Seed-Farmer (seedfarmer) in an opensource orchestration tool that works with AWS CodeSeeder (see [github](https://github.com/awslabs/aws-codeseeder) or [docs](https://aws-codeseeder.readthedocs.io/en/latest/)) and acts as an orchestration tool modeled after [GitOps deployments](https://www.gitops.tech/).  It has a CommandLine Interface (CLI) based in Python. 

It leverages modular code deployments ([see modules](docs/module_development.md)) leveraging [manifests](docs/manifests.md) and [deployspecs](docs/deployspec.md), keeping track of changes and applying changes as need / detected.


## Architecture
Seed-Farmer does not create its own deployments, rather it helps to deploy YOUR modules by acting as the broker between your module code and the AWS Cloud via AWS CodeSeeder.

![Seed-Farmer](docs/source/_static/SeedFarmer.png)


## Getting Started
The Seed-Farmer library is available on PyPi.  Install the library in a python virtual environment.


```bash
python3 -m venv .venv
source .venv/bin/activate
pip install seed-farmer
```

A [project](docs/source/project_structure.md) is now necessary to begin create modules.  
