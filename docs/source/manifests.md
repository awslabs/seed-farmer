# Manifests

The CLI is a module-centric deployment manager that follows the GitOps paradigm of code deployment.  Several manifests are required for deployment as defined below.

(deployment_manifest)=
## Deployment Manifest
The deployment manifest is the top level manifest and resides in the *modules* directory. There can be only one.
Its elements are:

- *name*
  - _REQUIRED_
  - the name of the project - must be unique per AWS region
- *groups*
  - _REQUIRED_
  - a logical grouping of modules in a YAML list
  - the ordering of each group is maintained and each group is deployed sequentially
  - has two required nested elements per entry:
    - _name_ - a unique group name
    - _path_ - relative path to module manifest
- *projectPolicy*
  - _OPTIONAL_
  - a global IAM policy for all modules to use in addition to the *modulestack.yaml policy*.  One is provided by default at [resources/projectpolicy.yaml](../resources/projectpolicy.yaml) with the minimum necessary permissions for the CLI to function, but a custom policy can be used.  If a custom policy is provided, it MUST have the minimum access capabilities as found in the provided policy as the default policy is ignored (if *projectPolicy* is populated).
- *dockerCredentialsSecret*
  - _OPTIONAL_
  -  a global name of a SecretsManager parameter that is use by AWS CodeSeeder when building images to prevent throttling from publically hosted image repositories such as DockerHub
  - the data in the SecretsManager is a json element of the following format:
  ```json
  {
    "docker.io": {
      "username": "username",
      "password": "thepassword"
    }
  }
  ```
- *permissionBoundaryArn*
  - _OPTIONAL_
  - The value should be the Name of the Permission Boundary Managed Policy
  - Below is the command to deploy a sample [Permission Boundary](https://docs.aws.amazon.com/IAM/latest/UserGuide/access_policies_boundaries.html) Managed Policy stack located in the project, however we expect the consumer of the framework to create a permission boundary as per their security requirements/guidelines and provide the ARN to the key `permissionBoundaryArn`:
  ```sh
  aws cloudformation deploy \
    --template-file ./resources/sample-permissionboundary.yaml \
    --stack-name permission-boundary-stack \
    --parameter-overrides ManagedPolicyName=MyAppPermissionBoundary \
    --capabilities CAPABILITY_NAMED_IAM
  ```

Here is a sample DeploymentManifest:

```yaml
name: dev
groups:
  - name: optionals
    path: manifests/example-dev/optional-modules.yaml
  - name: core
    path: manifests/example-dev/core-modules.yaml
projectPolicy: resources/mycustomiampolicy.yaml
dockerCredentialsSecret: aws-myapp-docker-credentials
permissionBoundaryArn: arn:aws:iam::XXXXXXXXXXXX:policy/MyAppPermissionBoundary
```
(module_manifest)=
## Module Manifest

The module manifest resides alongside the deployment manifest and defines the information the CLI needs to deploy a module or a group of modules - as defined by the group. There can be as many as there are groups.   Each entry in the module manifest is deployed in parallel and ordering is not preserved.
Its elements are:
- *name*
  - _REQUIRED_
  - the name of the group - must be unique per deployment
- *path*
  - _REQUIRED_
  - relative path to the modules direectory where the code resides for this module
- *parameters*
  - _OPTIONAL_
  - This is a list of  parameters made available to AWS CodeSeeder for the module to deploy.  Please see [parameters](parameters.md) for more details

Here is a sample ModuleManifest:

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

Using the example from Deployment Manifest above, there would be two (2) Module Manifests named core and optionals.  Here would be their corresponding examples:<br>
_optional-modules.yaml_

```yaml
name: networking
path: modules/optionals/networking/
parameters:
  - name: internet-accessible
    value: true
---
name: datalake-buckets
path: modules/optionals/datalake-buckets
parameters:
  - name: encryption-type
    value: SSE
```

_core-modules.yaml_

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
---
name: opensearch
path: modules/core/opensearch/
parameters:
  - name: opensearch_data_nodes
    value: 1
  - name: opensearch_data_nodes_instance_type
    value: r6g.large.search
  - name: opensearch_master_nodes
    value: 0
  - name: opensearch_master_nodes_instance_type
    value: r6g.large.search
  - name: opensearch_ebs_volume_size
    value: 30
  - name: vpc-id
    valueFrom:
      moduleMetadata:
        group: optionals
        name: networking
        key: VpcId
```
## Parameters

Parameters are defined in the [Module Manifests](module_manifest) as Key/Value pairs.  On deployment, values are serialized to JSON and passed to the module’s CodeBuild execution as Environment Variables. 

Modules should be parameterized to promote extensibility.  The CLI and [Module Manifests](module_manifest) support parameters of two types:
- user defined - a simple key/value string
- exported metadata from other deployed modules (module metadata)

They are defined in the module manifest for each module.

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

See <b>Parameters in AWS CodeSeeder</b> below.

### From Module Metadata
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

####  Parameters in AWS CodeSeeder

Environment Variables are made known to the module using a naming convention based off the Parameter’s key. Parameter keys are converted from “PascalCase”, “camelCase”, or “kebab-case” to all upper “SNAKE_CASE” and prefixed with “MYAPP_PARAMETER_”. Examples:

``` * someKey will become environment variable MYAPP_PARAMETER_SOME_KEY
* SomeKey will become environment variable MYAPP_PARAMETER_SOME_KEY
* some-key will become environment variable MYAPP_PARAMETER_SOME_KEY
* some_key will become environment variable MYAPP_PARAMETER_SOME_KEY
* somekey will become environment variable MYAPP_PARAMETER_SOMEKEY
