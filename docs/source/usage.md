# Usage

## Install SeedFarmer

Seed-Farmer can be installed from PyPi.  It is suggested to create a virtual environment in Python to isolate / separate your libraries.

Create a new directory and create a new virtual env under that dir.
```bash
python -m venv .venv
source .venv/bin/activate
```
Then install seedfarmer:
```bash
pip install seed-farmer
```

***
## Project Structure
Once SeedFarmer is installed, it is important to initialize a project structure properly.  The project encapsulates everything SeedFarmer needs to deploy and manage your project as a deployment.

The project for a Seed-Farmer compliant deployment is as follows:

```
<project-name>
- manifests (dir)
    -- <group>
- modules (dir)
    -- <group> (dir)
        -- <module>(dir)
        -- <module>(dir)
        -- <module>(dir)
    ...
- resources (dir)
    -- projectpolicy.yaml
- seedfarmer.yaml
```
The `modules`, `manifests`, and `resources` directories are at the same level. 

It is important to have the ```seedfarmer.yaml``` at the root of your project. 

Please see [project structure documentation](project_structure.md) for details and the content of `seedfarmer.yaml`
* [Create a New Project](cookiecutter_new_project)
* [Create a New Module](cookiecutter_new_module)
* [Project Policy Reference](project_policy)

***
## Module Development
Once the project is defined, you can start adding modules to your project.  

To create a new module, there are certain requirements needed to allow the CLI (and AWS CodeSeedeer) to deploy your code.
### Required Files
Every module must have the following:
- [deployment manifest](deployment_manifest)
- [module manifest](module_manifest)
- [deployspec.yaml](deployspec.md)
- [README.md of module](module_readme.md)

### Optional Files
- [modulestack.yaml](modulestack.md)


### Create a new module

#### Create the Module Skeleton
The [CLI](cli_commands.md) provides an `init` method to create your skeleton module code.  We will create a new module named `mymodule` in the group `mygroup`
```
> seedfarmer init module -g mygroup -m mymodule
> cd modules/mygroup/mymodule
```
The strucuture for your module is in place.  Edit the `deploysepc.yaml` as needed.  We provde a `modulestack.template` file that can be edited for additional permissions, and that file needs to be renamed to `modulestack.yaml` in order to be used.  

Please refer to our [initalization documetation](cookiecutter.md) for more details

#### Add the Manifests
Create a new module manifest (see [manifests](module_manifest)) and place it in the `manifests/` directory, under a logical directory.  If the `deployment.yaml` manifest does not exist, create it also.  Add your `module manifest` to the `deployment manifest`.

#### Start Developing
Your code is now seedfarmer-enabled for deployment.

## Module Development Best Practices Guide
We try to standardize module creation for re-usabilty and consistency.  Please see the [Best Practices Guide](module_best_practices.md) when creating new modules.

***
## Manifests
All deployments are driven by manifests.  Please see [manifests](manifests.md) for details.
- [deployment manifest](deployment_manifest)
- [module manifest](module_manifest)

***
## Parameters
The manifests support passing custom data as parameters to each module (via the [manifests](module_manifest)), and that data can also be sourced from already deployed modules.  
</br>Please see [parameters](parameters.md) for detailed information.

***
## CLI
The CLI is the primary way to interact with your deployments in a project.  Please take the time to execute some [commands](cli_commands.md) to get a feel for them!

***
## FAQ
Please see the [FAQ section](faq.md)