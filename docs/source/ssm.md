## SSM Deployment Data Layout

The CLI leverages a persistent store (currently AWS Systems Manager - SSM) for all metadata related to the deployment.  This includes 
- the deployment manifest
- the module manifests
- the modules deployspecs
- module metadata (output)
- MD5 hashes of various artifacts

All metadata is stored for use by the CLI and other modules.  

### Structure
The persisted data is segemented based on use and function.  Below is a generalized description
```
    /<project>/<deployment_name>/manifest
    /<project>/<deployment_name>/manifest/deployed
    /<project>/<deployment_name>/<group_name>/manifest  
    /<project>/<deployment_name>/<group_name>/<module_name>/manifest              
    /<project>/<deployment_name>/<group_name>/<module_name>/deployspec
    /<project>/<deployment_name>/<group_name>/<module_name>/metadata
    /<project>/<deployment_name>/<group_name>/<module_name>/md5/deployspec
    /<project>/<deployment_name>/<group_name>/<module_name>/md5/bundle
    /<project>/<deployment_name>/<group_name>/<module_name>/md5/manifest
```
       
#### Example Data Stored
For example, we have a deployment named 'local' with two groups/modules:
- core/metadata-storage
- core/opensearch

We would have the following persisted SSM parameters:
```
    /project/local/manifest
    /project/local/manifest/deployed
    /project/local/core/manifest  
    /project/local/core/metadata-storeage/manifest              
    /project/local/core/metadata-storeage/deployspec
    /project/local/core/metadata-storeage/metadata
    /project/local/core/metadata-storeage/md5/deployspec
    /project/local/core/metadata-storeage/md5/bundle
    /project/local/core/metadata-storeage/md5/manifest
    /project/local/core/opensearch/manifest              
    /project/local/core/opensearch/deployspec
    /project/local/core/opensearch/metadata
    /project/local/core/opensearch/md5/deployspec
    /project/local/core/opensearch/md5/bundle
    /project/local/core/opensearch/md5/manifest
```






