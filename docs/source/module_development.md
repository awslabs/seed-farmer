##  Creating a New Module

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


