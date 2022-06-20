## Project Structure

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
    -- <group> (dir)
        -- <module>(dir)
        -- <module>(dir)
        -- <module>(dir)
- resources (dir)
    -- projectpolicy.yaml
- seedfarmer.yaml
```
The `modules`, `manifests`, and `resources` directories are at the same level. 

The `resources` directory and explanation can be viewed in the [resouces documentation](resources.md).

It is important to have the ```seedfarmer.yaml``` at the root of your project.  This allows the `SeedFarmer CLI` to be executed anywhere within the project subdirectories.  Its content defines the name of the project that is used for deployment and provides a base of reference for all modules:
```yaml
project: <your project name>
description: <your project description>
```
***
There is CLI support for new project creation, and a new project can be created via the following:
```bash
    seedfarmer init project -n <my-project-name>
```

Please refer to our [initalization documetation](cookiecutter.md) for more details

