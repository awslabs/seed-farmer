# Project Development

Once `seedfarmer` is installed and bootstrapped, it is important to initialize a project structure properly.  The project encapsulates everything `seedfarmer` needs to deploy and manage your project as a deployment.

The project for a `seedfarmer` compliant deployment is as follows:

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
- seedfarmer.yaml
```
The `modules`, `manifests`, and `resources` directories are at the same level. 


It is important to have the ```seedfarmer.yaml``` at the root of your project.  This allows the `seedfarmer` CLI to be executed anywhere within the project subdirectories.  Its content defines the name of the project that is used for deployment and provides a base of reference for all modules:
```yaml
project: <your project name>
description: <your project description>
projectPolicyPath: <relativepath/policyname.yaml>
seedfarmer_version: <minimum required seedfermer version>
manifestValidationFailOnUnknownFields: <whether to fail on unknown fields in the manifest>
```
- **project** (REQUIRED) - this is the name of the project that all deployments will reference 
- **description** (OPTIONAL) - this is the description of the project
- **projectPolicyPath** (OPTIONAL) - this allows advanced users change the project policy that has the basic minimim permissions seedfarmer needs
  - it consists of a path relative to the project root and MUST be a valid relative path
  - to synth the existing project policy, run `seedfarmer projectpolicy synth` 
- **seedfarmer_version** (OPTIONAL) - this specifies what is the minimum allowable version of `seed-farmer` the project supports
  - if this value is set AND the runtime version of seedfarmer is greater, `seed-farmer` will exit immediately
- **manifestValidationFailOnUnknownFields** (OPTIONAL) - this specifies whether SeedFarmer will fail if it finds unknown fields ion the manifest
  - possible values are `true` or `false`, where `false` is the default


(project_initalization)=
## Initialization
On your local compute resource, pick a directory and add a file named `seedfarmer.yaml` that has the name of your new project.  For example, a new project named `mynewproject` can be seeded via the following:
```bash
echo project: mynewproject > seedfarmer.yaml
```


Now you are ready to create the new project.  

```bash
seedfarmer init project --help
Usage: seedfarmer init project [OPTIONS]

  Initialize a project. Make sure seedfarmer.yaml is present in the same
  location you execute this command!!

Options:
  -t, --template-url TEXT  The template URL. If not specified, the default
                           template repo is `https://github.com/awslabs/seed-
                           farmer`
  --help                   Show this message and exit.
```
This example will create a new directory in your current working directory that contains some bare structure to support development with seedfarmer:

```bash
seedfarmer init project
```
Your project is created and configured to use the `seedfarmer` CLI.

`seedfarmer` uses [CookieCutter](cookiecutter.md) for templating.
If you want to use a different project template, you can override the default template url. For example:
```
seedfarmer init project -t https://github.com/briggySmalls/cookiecutter-pypackage
```
NOTE: your project template for a new `seedfarmer` project must contain at least the required project structure.



(permissions_boundary)=
### Permissions Boundary Support
`seedfarmer` supports the concept of a [permissions boundary](https://docs.aws.amazon.com/IAM/latest/UserGuide/access_policies_boundaries.html).  This should already be deployed in your AWS account prior to use.


Please see the [deployment manifest](deployment_manifest) definition for details of configuring `seedfarmer` to use your customized resources.
