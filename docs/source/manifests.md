# Manifests

The CLI is a module-centric deployment manager that follows the GitOps paradigm of code deployment.  Several manifests are required for deployment as defined below.

(deployment_manifest)=

## Deployment Manifest
The deployment manifest is the top level manifest and resides in the `modules` directory.  Below is an example deployment manifest. 

```yaml
name: examples
toolchainRegion: us-west-2
forceDependencyRedeploy: False
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
- **forceDependencyRedeploy**: this is a boolean that tells seedfarmer to redeploy ALL dependency modules (see [Force Dependency Redeploy](force-redeploy)) - Default is `False`
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
    - **network** - this section indicates to `seed-farmer` and `aws-codeseeder` that the CodeBuild Project should be run in a VPC on Private Subnets.  This is to support compute resources in private or isloated subnets.  This CANNOT be changed once the `seedkit` is deployed (it either has VPC support or it does not).  ALL THREE parameters are required!
      - **vpcId** - the VPC ID the Codebuild Project should be associated to 
      - **privateSubnetIds** - the private subnets the Codebuild Project should be associated to 
      - **securityGroupIds** - the Security Groups the Codebuild Project should be associated to -- a limit of 5 is allowed

### Network Configuration for Regions
In the above section, we defined VPC support for deployments in CodeBuild.  The values can be hardcoded as denoted but also support:
- HardCoded Values
- Regional Parameters (see below for definition)
- AWS SSM Parameters (see below for definition) - NOTE: the SSM Parameter Name MUST start with the project name (the one in `seedfarmer.yaml`)
- Environment Variables (see below for definition)
  

There are a couple of things to be aware of:
1. The three values (vpcId, privateSubnetIds, securityGroupIds) should be stored as a string (if a vpcId) or stringified JSON lists (if privateSubnetIds or securityGroupIds).  **SeedFarmer predominantly leverages JSON as strings stored in SSM - these values are no different**.
2. Each value is defined independently - and is in no way linked to the other two.  It is up to you (the end user) to make sure the Subnets / Security Groups are in the proper VPC.  SeedFarmer does NOT validate this prior, and the deployment will error out with an ugly stack trace.

Lets look as some examples
#### HardCoded Value Support for Network
  ```yaml
network: 
  vpcId: vpc-XXXXXXXXX    
  privateSubnetIds:
    - subnet-XXXXXXXXX
    - subnet-XXXXXXXXX
  securityGroupsIds:
    - sg-XXXXXXXXX
  ```


#### Regional Parameters Support for Network
See the [above code snippets](deployment_manifest)
```yaml
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
```


#### AWS SSM Parameters Support for Network
This cannot be stressed enough: **the SSM Parameter Name MUST start with the project name**. For example: if the name of your project is `idf` as defined in `seedfarmer.yaml`, then your SSM Parameter name MUST start with `/idf/`.  If you do not leverage this info, then your deployment will NOT have access to the SSM Parameter.

This vale us account/region specific.  In other words, for every target account/region, you MUST populate this SSM Parameter if it is defined the the `deployment manifest`.  This is NOT a global value.

Here is an example.  Lets assume my project name is `idf`
```yaml
network: 
  vpcId: 
    valueFrom:
      parameterStore: /idf/testing/vpcid
  privateSubnetIds:
    valueFrom:
      parameterStore: /idf/testing/privatesubnets
  securityGroupIds:
    valueFrom:
      parameterStore: /idf/testing/securitygroups
```
The corresponding SSM Parameters would look like:
```code
/idf/testing/vpcid --> "vpc-0c4cb9e06c9413222"
/idf/testing/privatesubnets --> ["subnet-0c36d3d5808f67a02","subnet-00fa1e71cddcf57d3"]
/idf/testing/securitygroups --> ["sg-049033188c114a3d2"]
```
*** NOTE the lists above!!

#### Environment Variable Support for Network
Here is an example:
```yaml
network: 
  vpcId: 
    valueFrom:
      envVariable: VPCID
  privateSubnetIds:
    valueFrom:
      envVariable: PRIVATESUBNETS
  securityGroupIds:
    valueFrom:
      envVariable: SECURITYGROUPS
```
The corresponding `.env` file would have the following defined (again, remember the lists!!):
```code
VPCID="vpc-0c4cb9e06c9413222"
PRIVATESUBNETS=["subnet-0c36d3d5808f67a02","subnet-00fa1e71cddcf57d3"]
SECURITYGROUPS=["sg-049033188c114a3d2"]
```
(dependency-management)=
### Dependency Management

SeedFarmer has a shared-responsibilty model for dependency management of modules.  We have put in guardrails within SeedFarmer to inspect your deployment manifest prior to deployment ( ex. we prevent deletion of modules that have downstream modules dependent on it, prevent circular references of modules, etc.), but it is up to the end user to be aware of and manage the relationships between modules to assess impact of changes to modules via redeployment.  If a module is rendered into an inoperable state (ex. a rollback of CloudFormation prevents a ChangeSet from occurring), the user is responsible for resolving any blockers due to an inoperable change incurred by a failed module deployment.


(force-redeploy)=
#### Force Dependency Redeploy

We recommend to destroy / deploy / redeploy modules explicitly via the manifests.

But, we understand that sometimes when a module changes (is redeployed), the other downstream modules that are dependent on it may want to consume those changes. This flag will tell SeedFarmer to force a redeploy of all modules impacted by the redeploy of another module.  This is an indiscriminant feature in that it is not granular enough to detect WHAT is causing a redeploy, only that one needs to occur.

What does this mean?  Well, lets take the following module deployment order: 
```code
 Module-A --> Module-B --> Module-C --> Module-D --> Module-E 
```
 In this scenario, all modules are in their own group and the order of groups is as indicated.  
 `Module-D` is ONLY using metadata from `Module-C`, which is using metadata from `Module-A`.  In other words, `Module-D` has a dependency on  `Module-C` and `Module-C` has a dependency on `Module-A`.  **`Module-D` DOES NOT have a direct dependency on `Module-A`, but will be forced to redeploy because of the direct dependency on `Module-C`**  When the `forceDependencyRedeploy` flag is set, ANY change to `Module-A` will trigger a redeploy of `Module-A`, then in turn force a redeploy of `Module-C` and then force a redeployment of `Module-D`.   `Modules-B` and `Module-E` are unaffected.
 
 **This is an important feature to understand: redeployment is not discriminant.**  SeedFarmer does not know how to assess what has changed in a module and its impact on downstream modules.  Nor does it have the ability to know if a module can incur a redeployment (as opposed to a destroy and deploy process).  That is up to you to determine with respect to the modules you are leveraging.  ANY change to the source code (deployspec, modulestack, comments in cdk code, etc.) will indicate to SeedFarmer that the module needs to be redeployed, even if the underlying logic / artifact has not changed.  

 Also, it is important to understand that this feature could put your deployment in an unusable state if the shared-responsibility model is not followed.
 For example: lets say a deployment has a module (called `networking`) that deploys a VPC with public and private subnets that are restricted to a particular CIDR (as input).  Then, downstream modules reference the metadata of `netowrking`.  If a user were to change the CIDR references and redeploy the `networking` module, this has the potential to render the deployment in an unusable state: the process to change the CIDR's would trigger a destroy of the existing subnets...which would fail due to resources from other modules leveraging those subnets.  The redeployment would fail, and the user would have to manually correct the state.

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
dataFiles:
  - filePath: data/test2.txt
  - filePath: test1.txt
  - filePath: git::https://github.com/awslabs/idf-modules.git//modules/storage/buckets/deployspec.yaml?ref=release/1.0.0&depth=1
```
- **name** - the name of the group
- **path** - this element supports two sources of code:
  - the relative path to the module code in the project
  - a public Git Repository, leveraging the Terraform semantic as denoted [HERE](https://www.terraform.io/language/modules/sources#generic-git-repository)
- **targetAccount** - the alias of the account from the [deployment manifest mappings](deployment_manifest)
- **targetRegion** - the name of the region to deploy to - this overrides any mappings
- **codebuildImage** - a custom build image to use (see [Custom Build Image](custombuildimage))
- **parameters** - the parameters section .... see [Parameters](parameters)
- **dataFiles** - additional files to add to the bundle that are outside of the module code
  - this is LIST and EVERY element in the list must have the keyword **filePath**
  - the **filePath** does support pulls from Git Repository, leveraging the Terraform semantic as denoted [HERE](https://www.terraform.io/language/modules/)

Here is a sample manifest referencing a git repo:
```yaml
name: networking
path: git::https://github.com/awslabs/idf-modules.git//modules/network/basic-cdk?ref=release/1.0.0&depth=1
targetAccount: secondary
parameters:
  - name: internet-accessible
    value: true
```

### A Word About DataFiles ###
The **dataFile** support for modules is intended to take a file(s) located outside of the module code and packaged them as if they were apart of the module.  The use case: there are data files that are shared amongst multiple modules, or are dynamic and can change over time.  As you leverage the Git Path functionality (for sourcing modules in manifest), being able to modify these data files would have meant a change to the module code - which is not feasible as it will cause all deployments that leverage the same code to redeploy.

This feature will allow you to stage files locally in your SeedFarmer Project (MUST be located relative to `seedfarmer.yaml`) or are contained in a Git Repository.  These files will be packaged UNDER the module when deploying as if they are apart of the module code.  The relative paths remain intact UNDER the module when packaged.  

When using this feature, any change to these file(s) (modifying, add to manifest, removing from manifest) will indicate to SeedFarmer that a redeployment is necessary.

***Iceburg, dead ahead!*** Heres the rub: if you deploy with data files sourced from a local filesystem, you MUST provide those same files in order to destroy the module(s)...we are not keeping them stored anywhere (much like the module source code).  ***Iceburg  missed us! (why is everthing so wet??)***


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
`SeedFarmer` supports using [Dotenv](https://github.com/theskumar/python-dotenv) for dynamic replacement.  When a file named `.env` is placed at the projecr root (where `seedfarmer.yaml` resides), any value in a manifest with a key of `envVariable` will be matched and replaced with the corresponding environment variable.  You can pass in overriding `.env` files by using the `--env-file` on CLI command invocation.

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

`SeedFarmer` will respect changes to the SSM parameter via versioning.  If a module is deployed with an SSM Parameter, and then that parameter value is changed (invoking a version change of the parameter), `SeedFarmer` will detect that change and redeploy the module.  

NOTE: AWS CodeBuild does not currently respect passing in versions, so you cannot pass in a particular version in the manifest.  In other words, passing in `my-vpc-id:3` as a value for `parameterStore` will cause a failure.

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

`SeedFarmer` will respect changes to the SecretsManager secret via version-id and version-stage.  If the version-id referenced has changed, `SeedFarmer` will detect and indicate a redeploy of the module(s) that refer to that secret. 

NOTE: AWS CodeBuild does currently respect passing in version-id and version-stage, as defined in the [documentation HERE](https://docs.aws.amazon.com/codebuild/latest/userguide/build-spec-ref.html#build-spec.env.secrets-manager).  If no version-stage or version-id is passed in, then we will look for the version-id corresponding to the version-stage of `AWSCURRENT`. 


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