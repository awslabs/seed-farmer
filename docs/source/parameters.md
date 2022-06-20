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
```



The CLI will populate all parameters defined with a prefix of `MYAPP_PARAMETER_`.  All `name` characters will be converted to upper case and all `-` are converted to `_` for consistency.  The `value` or `valueFrom` fields will be left unchanged. <br>

In the above example, the runtime environment parameter in CodeBuld (AWS CodeSeeder) for the `vpc-id` will be set to `MYAPP_PARAMETER_VPC_ID`.




