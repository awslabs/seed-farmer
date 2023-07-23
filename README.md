# Seed-Farmer

Seed-Farmer (seedfarmer) is an opensource orchestration tool that works with AWS CodeSeeder (see [github](https://github.com/awslabs/aws-codeseeder) or [docs](https://aws-codeseeder.readthedocs.io/en/latest/)) and acts as an orchestration tool modeled after [GitOps deployments](https://www.gitops.tech/).  It has a CommandLine Interface (CLI) based in Python. 

Please see our [SeedFarmer Documentation](https://seed-farmer.readthedocs.io/en/latest/).

For information related to the architecture of Seed-Farmer or the deployment scheme...please see:
- [Seed-Farmer multi-account architecture](https://seed-farmer.readthedocs.io/en/latest/architecture.html)
- [Seed-Farmer processing steps](https://seed-farmer.readthedocs.io/en/latest/architecture.html#method-of-processing)

Seed-Farmer uses modular code deployments ([see modules](https://seed-farmer.readthedocs.io/en/latest/module_development.html)) leveraging [manifests](https://seed-farmer.readthedocs.io/en/latest/manifests.html) and [deployspecs](https://seed-farmer.readthedocs.io/en/latest/module_development.html#deployspec), keeping track of changes and applying changes as need / detected.


## Getting Started
The Seed-Farmer library is available on PyPi.  Install the library in a python virtual environment.


```bash
python3 -m venv .venv
source .venv/bin/activate
pip install seed-farmer
```

A [project](https://seed-farmer.readthedocs.io/en/latest/project_development.html) is now necessary to begin create modules.  
