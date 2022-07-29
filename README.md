# Seed-Farmer

Seed-Farmer (seedfarmer) is an opensource orchestration tool that works with AWS CodeSeeder (see [github](https://github.com/awslabs/aws-codeseeder) or [docs](https://aws-codeseeder.readthedocs.io/en/latest/)) and acts as an orchestration tool modeled after [GitOps deployments](https://www.gitops.tech/).  It has a CommandLine Interface (CLI) based in Python. 

It leverages modular code deployments ([see modules](https://seed-farmer.readthedocs.io/en/latest/usage.html#module-development)) leveraging [manifests](https://seed-farmer.readthedocs.io/en/latest/manifests.html) and [deployspecs](https://seed-farmer.readthedocs.io/en/latest/deployspec.html), keeping track of changes and applying changes as need / detected.


## Getting Started
The Seed-Farmer library is available on PyPi.  Install the library in a python virtual environment.


```bash
python3 -m venv .venv
source .venv/bin/activate
pip install seed-farmer
```

A [project](https://seed-farmer.readthedocs.io/en/latest/project_structure.html) is now necessary to begin create modules.  
