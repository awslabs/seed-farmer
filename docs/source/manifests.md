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
- **parameters** - the parameters section .... see [Parameters](parameters)

(parameters)=
## Parameters

Parameters are defined in the [Module Manifests](module_manifest) as Key/Value pairs.  On deployment, values are serialized to JSON and passed to the module’s CodeBuild execution as Environment Variables. 

Modules should be parameterized to promote extensibility.  The CLI and [Module Manifests](module_manifest) support parameters of multiple types:
- [User Defined](user_defined) - a simple key/value string
- [Module Metadata](modulemetadata) from other deployed modules 
- [Environment Variables](envVariable)
- [AWS SSM Parameter](ssm_parameter)
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
In this example, the `glue-db-suffix` parameter will be exposed to the CodeBuild via AWS CodeSeeder as an [environment parameter](params_in_codeseeder).



(envVariable)=
### Environment Variables
`seedfarmer` supports using [Dotenv](https://github.com/theskumar/python-dotenv) for dynamic replacement.  Wen a file names `.env` is placed at the projecr root (where `seedfarmer.yaml` resides), any value in a manifest with a key of `envVariable` will be matched and replaced with the corresponding environment variable.

```yaml
name: opensearch
path: modules/core/opensearch/
parameters:
  - name: vpc-id
    valueFrom:
      envVariable: ENV_VPC_ID
```
In this example, the `opensearch` module is referencing an environment parameter named `ENV_VPC_ID`. <br>

The `opensearch` module deployment will then have an environment parameter set in the environment to the value of the parameter.  It can then be referenced as an [environment parameter](params_in_codeseeder) in the deployment.

`Environment Variables` also support dynamically changing the `account_id` in manifests to avoid hard-coding an `account_id` in any manifest.
```yaml
accountId:
  valueFrom:
    envVariable: PRIMARY_ACCOUNT
```
<br>

(modulemetadata)=
### Module Metadata
Parameters can leverage exported metadata from existing modules.  You will need to know the group name, module name and the name of the parameter.  It leverages the `valueFrom` keyword and has a nested definiton. Below is an example:
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

The `opensearch` module deployment will then have an environment parameter set in the environment to the value of the vpc-id that is exported from the `networking` module.  They can then be referenced as an [environment parameter](params_in_codeseeder) in the deployment.


(ssm_parameter)=
### AWS SSM Parameter
Parameters can leverage key/value pairs stored in [AWS SSM Parameter Store](https://docs.aws.amazon.com/systems-manager/latest/userguide/systems-manager-parameter-store.html).  You will need to know the name of the parameter.  It leverages the `valueFrom` keyword and has a nested definiton. Below is an example:
```yaml
name: opensearch
path: modules/core/opensearch/
parameters:
  - name: vpc-id
    valueFrom:
      parameterStore: my-vpc-id
```
In this example, the `opensearch` module is referencing an SSM parameter named `my-vpc-id` from AWS SSM Parameter Store. <br>

The `opensearch` module deployment will then have an environment parameter set in the environment to the value of the parameter that is fetched.  It can then be referenced as an [environment parameter](params_in_codeseeder) in the deployment.

(secrets_manager)=
### AWS SecretsManager
Parameters can leverage secured secrets in [AWS Secrets Manager](https://docs.aws.amazon.com/secretsmanager/latest/userguide/intro.html).  You will need to know the name of the secret.  It leverages the `valueFrom` keyword and has a nested definiton. Below is an example:
```yaml
name: opensearch
path: modules/core/opensearch/
parameters:
  - name: vpc-id
    valueFrom:
      secretsManager: my-secret-vpc-id
```
In this example, the `opensearch` module is referencing a secret named `my-secret-vpc-id` from AWS Secrets Manager. <br>

The `opensearch` module deployment will then have an environment parameter set in the environment to the value of the secret that is fetched.  It can then be referenced as an [environment parameter](params_in_codeseeder) in the deployment.  NOTE: the value will be obfusticated in the AWS CodeBuild console in the Environments Section for security purposes.


(dockerCredentialsSecret)=
### Docker Credentials Secret
A named manifest key pointing to an [AWS Secrets Manager](https://docs.aws.amazon.com/secretsmanager/latest/userguide/intro.html) entry that is use by AWS CodeSeeder when building images to prevent throttling from publically hosted image repositories such as DockerHub. <br>
<br>
The data in the SecretsManager is a json element of the following format:
  ```json
  {
    "docker.io": {
      "username": "username",
      "password": "thepassword"
    }
  }
  ```

  (params_in_codeseeder)=
### Parameters in AWS CodeSeeder

CodeBuild Environment Variables that are set via AWS CodeSeeder are made known to the module using a naming convention based off the Parameter’s key. Parameter keys are converted from “PascalCase”, “camelCase”, or “kebab-case” to all upper “SNAKE_CASE” and prefixed with “<<project>>_PARAMETER_”.  If the name of our project is "MY_APP" the resulting environment parameters will be:

``` 
* someKey will become environment variable MYAPP_PARAMETER_SOME_KEY
* SomeKey will become environment variable MYAPP_PARAMETER_SOME_KEY
* some-key will become environment variable MYAPP_PARAMETER_SOME_KEY
* some_key will become environment variable MYAPP_PARAMETER_SOME_KEY
* somekey will become environment variable MYAPP_PARAMETER_SOMEKEY
```