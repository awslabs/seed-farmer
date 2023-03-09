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
    codebuildImage:  XXXXXXXXXXXX.dkr.ecr.us-east-1.amazonaws.com/aws-codeseeder/code-build-base:5.5.0
    parametersGlobal:
      dockerCredentialsSecret: nameofsecret
      permissionsBoundaryName: policyname
    regionMappings:
      - region: us-east-2
        default: true
        codebuildImage:  XXXXXXXXXXXX.dkr.ecr.us-east-1.amazonaws.com/aws-codeseeder/code-build-base:4.4.0
        parametersRegional:
          dockerCredentialsSecret: nameofsecret
          permissionsBoundaryName: policyname
          vpcId: vpc-XXXXXXXXX
          publicSubnetIds:
            - subnet-XXXXXXXXX
            - subnet-XXXXXXXXX
          privateSubnetIds:
            - subnet-XXXXXXXXX
            - subnet-XXXXXXXXX
          isolatedSubnetIds:
            - subnet-XXXXXXXXX
            - subnet-XXXXXXXXX
          securityGroupsId:
            - sg-XXXXXXXXX
        network: 
          vpcId:
            valueFrom:
              parameterValue: vpcId
          privateSubnetIds:
            valueFrom:
              parameterValue: privateSubnetIds
          securityGroupIds:
            valueFrom:
              parameterValue: securityGroupIds
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
  - **codebuildImage** - a custom build image to use (see [Custom Build Image](custombuildimage))
  - **parametersGlobal** - these are parameters that apply to all region mappings unless otherwise overridden at the region level
    - **dockerCredentialsSecret** - please see [Docker Credentials Secret](dockerCredentialsSecret)
    - **permissionsBoundaryName** - the name of the [permissions boundary](https://docs.aws.amazon.com/IAM/latest/UserGuide/access_policies_boundaries.html) policy to apply to all module-specific roles created
  - **regionMappings** - section to define region-specific configurations for the defined account, this is a list
    - **region** - the region name
    - **default** - this designates this mapping as the default region for all modules unless otherwise specified.  This is primarily for supporting migrating
    - **codebuildImage** - a custom build image to use (see [Custom Build Image](custombuildimage))
    - **parametersRegional** - these are parameters that apply to all region mappings unless otherwise overridden at the region level
      - **dockerCredentialsSecret** - please see [Docker Credentials Secret](dockerCredentialsSecret)
        - This is a NAMED PARAMETER...in that `dockerCredentialsSecret` is recognized by `seed-farmer`
      - **permissionsBoundaryName** - the name of the [permissions boundary](https://docs.aws.amazon.com/IAM/latest/UserGuide/access_policies_boundaries.html) policy to apply to all module-specific roles created
        - This is a NAMED PARAMETER...in that `permissionsBoundaryName` is recognized by `seed-farmer`
      - Any other parameter in this list is NOT a NAMED PARAMETER (ex. `vpcId`,`privateSubnetIds`,`publicSubnetIds`, etc,) and is soley for the use of lookup in:
        - module manifests
        - the `network` object in the `regionMappings` (see examples above)
    - **network** - this section indicates to `seed-farmer` and `aws-codeseeder` that the CodeBuild Project should be run in a VPC on Private Subnets.  This is to support compute resources in private or isloated subnets.  This CANNOT be changed once the `seedkit` is deployed (it either has VPC support or it does not).  ALL THREEE parameters are required!
      - **vpcId** - the VPC ID the Codebuild Project should be associated to 
      - **privateSubnetIds** - the private subnets the Codebuild Project should be associated to 
      - **securityGroupIds** - the Security Groups the Codebuild Project should be associated to -- a limit of 5 is allowed


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
codebuildImage:  XXXXXXXXXXXX.dkr.ecr.us-east-1.amazonaws.com/aws-codeseeder/code-build-base:3.3.0
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
- **path** - this element supports two sources of code:
  - the relative path to the module code in the project
  - a public Git Repository, leveraging the Terraform semantic as denoted [HERE](https://www.terraform.io/language/modules/sources#generic-git-repository)
- **targetAccount** - the alias of the account from the [deployment manifest mappings](deployment_manifest)
- **targetRegion** - the name of the region to deploy to - this overrides any mappings
- **codebuildImage** - a custom build image to use (see [Custom Build Image](custombuildimage))
- **parameters** - the parameters section .... see [Parameters](parameters)

Here is a sample manifest referencing a git repo:
```yaml
name: networking
path: git::git@github.com:awslabs/seed-farmer.git//examples/exampleproject/modules/optionals/networking/?ref=release/0.1.4&depth=1
targetAccount: secondary
parameters:
  - name: internet-accessible
    value: true
```

(custombuildimage)=
## Custom Codebuild Image
`seed-farmer` is preconfigued to use the optimal build image and we recommend using it as-is (no need to leverage the `codebuildImage` manifest named paramter).  But, we get it....no one wants to be boxed in.</br>
<b>USER BEWARE</b> - this is a feature meant for advanced users...use at own risk!

### The Build Image
An AWS Codebuild complaint image is provided for use with `seed-farmer` and the CLI is configured by default to use this image.  Advanced users have the option of building their own image and configuring their deployment to use it.  If an end user wants to build their own image, it is STRONGLY encouraged to use [this Dockerfile from AWS public repos](https://github.com/awslabs/aws-codeseeder/blob/main/images/code-build-image/Dockerfile) as the base layer.  `seed-farmer` leverages this as the base for its default image ([see HERE](https://github.com/awslabs/aws-codeseeder/blob/main/images/code-build-image/Dockerfile)).

### Logic for Rules -- Application
There are three (3) places to configure a custom build image:
- at the module level
- at the account/region mapping level
- at the account level

`seed-farmer` is an module-centric deployment framework.  You CAN have a custom image configured at each of the levels defined above, and the following logic is applied:
1. if the image is defined at the module level --- USE IT... ELSE
2. if the image is defined at the account/region level --- USE IT... ELSE
3. if the image is defined at the account level --- USE IT... ELSE
4. use the default image 



(parameters)=
## Parameters

Parameters are defined in the [Module Manifests](module_manifest) as Key/Value pairs.  On deployment, values are serialized to JSON and passed to the module’s CodeBuild execution as Environment Variables. 

Modules should be parameterized to promote extensibility.  The CLI and [Module Manifests](module_manifest) support parameters of multiple types:
- [User Defined](user_defined) - a simple key/value string
- [Module Metadata](modulemetadata) from other deployed modules
- [Global and Regional Parameters](globalregionalparameters)  
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


(globalregionalparameters)=
### Global and Regional Parameters
Global and Regional Parameters are simple name/value pairs that can be defined and are applied to the account referenced in their affiliated sections.  The Global Parameters are available to all regions in the defiend account  The Regional Parameters are available in the region they are defined in.
```yaml
targetAccountMappings:
  - alias: primary
    accountId: 123456789012
    default: true
    parametersGlobal:
      dockerCredentialsSecret: nameofsecret
      permissionsBoundaryName: policyname
      mygreatkey: mygreatvalue
    regionMappings:
      - region: us-east-2
        default: true
        parametersRegional:
          dockerCredentialsSecret: nameofsecret
          permissionsBoundaryName: policyname
          vpcId: vpc-XXXXXXXXX
          publicSubnetIds:
            - subnet-XXXXXXXXX
            - subnet-XXXXXXXXX
          privateSubnetIds:
            - subnet-XXXXXXXXX
            - subnet-XXXXXXXXX
          isolatedSubnetIds:
            - subnet-XXXXXXXXX
            - subnet-XXXXXXXXX
          securityGroupsId:
            - sg-XXXXXXXXX
```
In the above example, the Global and Regional Parameters are defined (ex. `mygreatkey` in Global and `privateSubnetIds` in Regional).  They can be referenced by a module in the module manifest using the `parameterValue` keyword:

```yaml
name: efs
path: modules/core/efs/
parameters:
  - name: vpc-id
    valueFrom:
      parameterValue: vpcId
  - name: removal-policy
    value: DESTROY
  - name: testitout
    valueFrom:
      parameterValue: mygreatkey
```
`seed-farrmer` will first look in the Regional Parameters for a matching key, and return a string object (all json convert to a string) represening the value.  If not found, `seed-farrmer` will look in the Global Parameters for the same key and return that string-ified value.

NOTE: the `network` section of the [deployment manifest](deployment_manifest) leverages Regional Parameters only!

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