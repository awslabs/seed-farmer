# Manifests

The CLI is a module-centric deployment manager that follows the GitOps paradigm of code deployment.  Several manifests are required for deployment as defined below.

(deployment_manifest)=
## Deployment Manifest
The deployment manifest is the top level manifest and resides in the `modules` directory.  Below is an example deployment manifest. 

```yaml
name: examples
toolchainRegion: us-west-2
groups:
  - name: optionals
    path: manifests-multi/examples/optional-modules.yaml
  - name: optionals-2
    path: manifests-multi/examples/optional-modules-2.yaml
targetAccountMappings:
  - alias: primary
    accountId:
      valueFrom:
        envVariable: PRIMARY_ACCOUNT
    default: true
    parametersGlobal:
      dockerCredentialsSecret: nameofsecret
      permissionsBoundaryName: policyname
    regionMappings:
      - region: us-west-2
        default: true
        parametersRegional:
          dockerCredentialsSecret: nameofsecret
          permissionsBoundaryName: policyname
      - region: us-east-2
  - alias: secondary
    accountId: 123456789012
    regionMappings:
      - region: us-west-2
        parametersRegional:
          dockerCredentialsSecret: nameofsecret
          permissionsBoundaryName: policyname
      - region: us-east-2
        default: true
```

- **name** : this is the name of your deployment.  There can be only one deployment with this name in a project.
- **toolchainRegion** :the designated region that the `toolchain` is created in
- **groups** : the relative path to the [`module manifests`](module_manifest) that define each module in the group.  This sequential order is preserved in deployment, and reversed in destroy.
  - **name** - the name of the group
  - **path**- the relative path to the [module manifest](module_manifest)
- **targetAccountMappings** - section defining target accounts and configurations, this is a list
  - **alias** - the logical name for an account, referenced by [`module manifests`](module_manifest)
  - **account** - the account id tied to the alias.  This parameter also supports [Environment Variables](envVariable)
  - **default** - this designates this mapping as the default account for all modules unless otherwise specified.  This is primarily for supporting migrating from `seedfarmer v1` to the current version.
  - **parametersGlobal** - these are parameters that apply to all region mappings unless otherwise overridden at the region level
    - **dockerCredentialsSecret** - please see [Docker Credentials Secret](dockerCredentialsSecret)
    - **permissionsBoundaryName** - the name of the [permissions boundary](https://docs.aws.amazon.com/IAM/latest/UserGuide/access_policies_boundaries.html) policy to apply to all module-specific roles created
  - **regionMappings** - section to define region-specific configurations for the defined account, this is a list
    - **region** - the region name
    - **default** - this designates this mapping as the default region for all modules unless otherwise specified.  This is primarily for supporting migrating
    - **parametersRegional** - these are parameters that apply to all region mappings unless otherwise overridden at the region level
      - **dockerCredentialsSecret** - please see [Docker Credentials Secret](dockerCredentialsSecret)
      - **permissionsBoundaryName** - the name of the [permissions boundary](https://docs.aws.amazon.com/IAM/latest/UserGuide/access_policies_boundaries.html) policy to apply to all module-specific roles created


(module_manifest)=
## Module Manifest

The module manifest is referred to by the [deployment manifest](deployment_manifest) and defines the information the CLI needs to deploy a module or a group of modules - as defined by the group.  Each entry in the module manifest is deployed in parallel and ordering is not preserved.
```yaml
name: networking
path: modules/optionals/networking/
targetAccount: primary
parameters:
  - name: internet-accessible
    value: true
---
name: buckets
path: modules/optionals/buckets
targetAccount: secondary
targetRegion: us-west-2
parameters:
  - name: encryption-type
    value: SSE
  - name: some-name
    valueFrom:
      moduleMetadata:
        group: optionals
        name: networking
        key: VpcId
```
- **name** - the name of the group
- **path** - the relative path to the module code in the project
- **targetAccount** - the alias of the account from the [deployment manifest mappings](deployment_manifest)
- **targetRegion** - the name of the region to deploy to - this overrides any mappings 
- **parameters** - the parameters section .... ser [Parameters](parameters)

(parameters)=
## Parameters

Parameters are defined in the [Module Manifests](module_manifest) as Key/Value pairs.  On deployment, values are serialized to JSON and passed to the module’s CodeBuild execution as Environment Variables. 

Modules should be parameterized to promote extensibility.  The CLI and [Module Manifests](module_manifest) support parameters of multiple types:
- [User Defined](user_defined) - a simple key/value string
- [Module Metadata](modulemetadata) from other deployed modules 
- [Environment Variables](envVariable)
- [AWS SSM parameters](ssm_parameter)
- [AWS Secrets Manager](secrets_manager)

They are defined in the module manifest for each module.

(user_defined)=
### User-Defined
These are simple key/value pairs passed in as strings.  Here is an example of a module with user-defined parameters:
```yaml
name: metadata-storage
path: modules/core/metadata-storage/
parameters:
  - name: glue-db-suffix
    value: vsidata
  - name: rosbag-bagfile-table-suffix
    value: Rosbag-BagFile-Metadata
  - name: rosbag-scene-table-suffix
    value: Rosbag-Scene-Metadata
```
In this example, the `glue-db-suffix` parameter will be exposed to the CodeBuild via AWS CodeSeeder as:
```MYAPP_PARAMETER_GLUE_DB_SUFFIX=vsidata```.

See [Parameters in AWS CodeSeeder](params_in_codeseeder)


(envVariable)=
### Environment Variables
`seedfarmer` supports using [Dotenv](https://github.com/theskumar/python-dotenv) for dynamic replacement.  Wen a file names `.env` is placed at the projecr root (where `seedfarmer.yaml` resides), any value in a manifest with a key of `envVariable` will be matched and replaced with the corresponding environment variable.

For example, instead of hard-coding an `account id` in any manifest, that is commited to a repo, you can use `.env` and dynamically replace the value at runtime via the sample below:
```yaml
accountId:
  valueFrom:
    envVariable: PRIMARY_ACCOUNT
```
(modulemetadata)=
### Module Metadata
Parameters can also leverage exported metadata from eisting modules.  You will need to know the group name, module name and the name of the paramter.  It leverages the `valueFrom` keyword (instead of `value') and has a nested definiton. Below is an example:
```yaml
name: opensearch
path: modules/core/opensearch/
parameters:
  - name: vpc-id
    valueFrom:
      moduleMetadata:
        group: optionals
        name: networking
        key: VpcId
```
In this example, the `opensearch` module is referencing a module metadata parameter `VpcId` from the `networking` module in the `optionals` group. <br>

The `opensearch` module deployment will then have an environment parameter set: `MYAPP_PARAMETER_VPC_ID` in the environment to the value of the vpc-id that is exported from the `networking` module.  They can then be referenced as an environment parameter in the deployment


(ssm_parameter)=
### AWS SSM Parameter
Add the stuff here...

(secrets_manager)=
### AWS SecretsManager
Add the stuff here


(dockerCredentialsSecret)=
### Docker Credentials Secret
A named manifest key pointing to an AWS SecretsManager parameter that is use by AWS CodeSeeder when building images to prevent throttling from publically hosted image repositories such as DockerHub
  - the data in the SecretsManager is a json element of the following format:
  ```json
  {
    "docker.io": {
      "username": "username",
      "password": "thepassword"
    }
  }
  ```

  (params_in_codeseeder)=
###  Parameters in AWS CodeSeeder

CodeBuild Environment Variables that are set via AWS CodeSeeder are made known to the module using a naming convention based off the Parameter’s key. Parameter keys are converted from “PascalCase”, “camelCase”, or “kebab-case” to all upper “SNAKE_CASE” and prefixed with “MYAPP_PARAMETER_”. Examples:

``` * someKey will become environment variable MYAPP_PARAMETER_SOME_KEY
* SomeKey will become environment variable MYAPP_PARAMETER_SOME_KEY
* some-key will become environment variable MYAPP_PARAMETER_SOME_KEY
* some_key will become environment variable MYAPP_PARAMETER_SOME_KEY
* somekey will become environment variable MYAPP_PARAMETER_SOMEKEY
```