# Seed-Farmer

[![PyPi](https://img.shields.io/pypi/v/seed-farmer)](https://pypi.org/project/seed-farmer/)
[![Python Version](https://img.shields.io/pypi/pyversions/seed-farmer.svg)](https://pypi.org/project/seed-farmer/)
[![License](https://img.shields.io/pypi/l/seed-farmer)](https://github.com/awslabs/seed-farmer/blob/main/LICENSE)

Seed-Farmer (seedfarmer) is an opensource orchestration tool modeled after [GitOps deployments](https://www.gitops.tech/). It has a CommandLine Interface (CLI) and is based in Python.

Please see our [SeedFarmer Documentation](https://seed-farmer.readthedocs.io/en/latest/).

For information related to the architecture of Seed-Farmer or the deployment scheme ... please see:

- [Seed-Farmer multi-account architecture](https://seed-farmer.readthedocs.io/en/latest/concepts/architecture/)
- [Seed-Farmer Concepts](https://seed-farmer.readthedocs.io/en/latest/concepts/)

Seed-Farmer uses modular code deployments ([see modules](https://seed-farmer.readthedocs.io/en/latest/guides/module-development/)) leveraging [manifests](https://seed-farmer.readthedocs.io/en/latest/reference/manifests/) and [deployspecs](https://seed-farmer.readthedocs.io/en/latest/reference/deployspec/), keeping track of changes and applying changes as need / detected.

## Getting Started

The Seed-Farmer library is available on PyPi.  Install the library in a python virtual environment.

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install seed-farmer
```

Seed-Farmer also supports [uv](https://docs.astral.sh/uv/guides/tools/), and can be installed as a tool or into a virtual environment.

```bash
uv tool install seed-farmer
```

A [project](https://seed-farmer.readthedocs.io/en/latest/guides/project-development/) is necessary to begin creating modules.  

## Development

To get started with developing you need to setup a virtual environment and install the required python dependencies.

Setup virtual environment and install dependencies:

```bash
make install
```

Run unit tests

```bash
make test
```

Validate ruff formatting and mypy

```bash
make validate
```

Fix ruff formatting issues

```bash
make format
```
