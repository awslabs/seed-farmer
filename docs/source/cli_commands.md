## SeedFarmer CLI (Command Line Interface)

The SeedFarmer CLI provides the primary way to interface with the orchestration framework that manages a deploymement with AWS CodeSeeder.  It is used by CICD pipelines and individual users to:
 - deploy code (modules) via a deployment and manifest
 - fetch metadata related to currently deployed modules
 - destroy deployments
 - apply changes to deployments (via a GitOps model)

### Summary Commands
These commands are  structured in the format of:
```
seedfarmer <verb> <object> -<parameters>
```
#### Top Level Commands:
```
> seedfarmer
Usage: seedfarmer [OPTIONS] COMMAND [ARGS]...

Options:
  --help  Show this message and exit.

Commands:
  apply    Apply a deployment spec relative path for PROJECT
  destroy  Destroy PROJECT Deployment
  init     Initialize a new module in the proper structure
  list     List the relative data (module or deployment)
  remove   Top Level command to support removing module metadata
  store    Top Level command to support storing module metadata

```

The command listed above are used by the CLI, CICD implementations, and individual users.  There are no restrictions on the use of the commands (i.e users do have the ability to delete metadata and ssm data - so be careful!!) <br>

Each sub-command has help information related to how to use them.  Users typically will use the ```seedfarmer apply```, ```seedfarmer list``` and the ```seedfarmer destroy``` commands regularly.



#### Example Walkthru - Deploy and Apply changes
The first time deploying, a deployment manifest must be created [see here](manifests.md).  The deployment manifests should be in the ```manifests``` directory.  All paths are relative to the project level (at all times).  For this example, we have a deployment manifest  located at ```manifests/walkthru/deployment.yaml``` and and modules manifests located at ```manifests/walkthru/<whatevername>```.  To check our deployment without apply any changes, our command would look like this:
```
seedfarmer apply manifests/walkthru/deployment.yaml --dry-run
```
None of these changes would be applied / deployed until we remove the `dry-run` flag:
```
seedfarmer apply manifests/walkthru/deployment.yaml
```

Once complete, we now have a deployment we can use.  After, if there are modules or groups we want to add OR remove (via altering the manifests), we can apply those changes once again:
```
seedfarmer apply manifests/walkthru/deployment.yaml
```
The CLI will take care of assessing: 
- which modules need to be redeployed due to changes
- which modules are up to date
- which modues or groups of modules need to be destroyed

Once we are finished with the deployment (ex. the ```local``` deployment), we can destroy all artifacts via:
```
seedfarmer destroy local
```



#### Example Walkthru - Fetch Module Metadata

This is an example of how to get the metadata of a module without knowing what is currently deployed.

First, get the list of all deployments in this region:
```
> seedfarmer list deployments
Deployment    
Names         
┏━━━━━━━━━━━━┓
┃ Deployemnt ┃
┡━━━━━━━━━━━━┩
│ local      │
└────────────┘
```
Here, there is one deployment: _local_ <br>
Now, get all the modules deployed in _local_ with their corresponding group:


```
> seedfarmer list modules -d local
Deployed Modules                                     
┏━━━━━━━━━━━━┳━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ Deployemnt ┃ Group       ┃ Module                 ┃
┡━━━━━━━━━━━━╇━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━┩
│ local      │ optionals   │ networking             │
│ local      │ optionals   │ datalake-buckets       │
│ local      │ core        │ metadata-storage       │
│ local      │ core        │ opensearch             │
│ local      │ core        │ eks                    │
│ local      │ blogs       │ rosbag-scene-detection │
│ local      │ blogs       │ rosbag-webviz          │
│ local      │ integration │ opensearch-proxy       │
│ local      │ integration │ rosbag-ddb-to-os       │
└────────────┴─────────────┴────────────────────────┘
```

With the above table, we can fetch all the metadata associated with a module deployment.  The output is in JSON:

```
> seedfarmer list moduledata -d local -g core -m metadata-storage
{
  "GlueDBName": "project-local-core-metadata-storage-vsidata",
  "RosbagBagFilePartitionKey": "bag_file_prefix",
  "RosbagBagFileTable": "project-local-core-metadata-storage-Rosbag-BagFile-Metadata",
  "RosbagSceneMetadataPartitionKey": "bag_file",
  "RosbagSceneMetadataSortKey": "scene_id",
  "RosbagSceneMetadataStreamArn": "arn:aws:dynamodb:us-east-1:123456789012:table/project-local-core-metadata-storage-Rosbag-Scene-Metadata/stream/2022-03-23T17:25:25.958",
  "RosbagSceneMetadataTable": "project-local-core-metadata-storage-Rosbag-Scene-Metadata"
}

```
This metadata is the same metadata that modules reference (as needed).