## Manifests

The CLI is a module-centric deployment manager that follows the GitOps paradigm of code deployment.  Several manifests are required for deployment as defined below.

(deployment_manifest)=
### Deployment Manifest
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
  - Below is the command to deploy a sample Permission Boundary Managed Policy stack located in the project:
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
### Module Manifest

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
### Parameters
The module manifest leverages parameters, either user-defined or from an already deployed module (`modulemetadata`).

Please see [parameters](parameters.md) for more details
