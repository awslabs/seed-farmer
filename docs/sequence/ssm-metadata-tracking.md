---
title: SSM Metadata Tracking
---

This sequence diagram shows how Seed-Farmer tracks module metadata and MD5 checksums in SSM Parameter Store.

```mermaid
sequenceDiagram
    participant Deploy as Module Deploy
    participant MetadataMgr as Metadata Manager
    participant Checksum as Checksum Utils
    participant SSM as SSM Parameter Store
    participant CodeBuild as CodeBuild Process
    participant ModuleInfo as Module Info

    Note over Deploy,ModuleInfo: Module Deployment Phase
    
    Deploy->>Checksum: resolve_params_for_checksum()
    Checksum->>Checksum: calculate parameter hash
    Checksum-->>Deploy: param_checksum
    
    Deploy->>Checksum: calculate_module_md5()
    Checksum->>Checksum: hash deployspec.yaml
    Checksum->>Checksum: hash source files
    Checksum->>Checksum: hash resolved parameters
    Checksum-->>Deploy: module_md5
    
    Deploy->>MetadataMgr: get_module_metadata()
    MetadataMgr->>SSM: get_parameter()
    Note over SSM: /sf/{project}/{deployment}/{group}-{module}/metadata
    
    alt Metadata exists
        SSM-->>MetadataMgr: existing metadata
        MetadataMgr->>MetadataMgr: compare MD5 hashes
        
        alt MD5 unchanged
            MetadataMgr-->>Deploy: skip deployment (no changes)
        else MD5 changed
            MetadataMgr-->>Deploy: proceed with deployment
        end
        
    else No metadata exists
        MetadataMgr-->>Deploy: first deployment
    end
    
    alt Deployment proceeds
        Deploy->>CodeBuild: execute deployment
        
        Note over CodeBuild: CodeBuild Execution Phase
        CodeBuild->>CodeBuild: run build commands
        CodeBuild->>CodeBuild: run deploy commands
        CodeBuild->>CodeBuild: capture outputs
        
        CodeBuild->>ModuleInfo: write_module_metadata()
        ModuleInfo->>SSM: put_parameter(metadata)
        Note over SSM: Store: MD5, outputs, timestamps, status
        
        ModuleInfo->>SSM: put_parameter(md5)
        Note over SSM: /sf/{project}/{deployment}/{group}-{module}/md5
        
        ModuleInfo->>SSM: put_parameter(outputs)
        Note over SSM: /sf/{project}/{deployment}/{group}-{module}/outputs
        
        CodeBuild-->>Deploy: deployment complete
    end
    
    Deploy->>MetadataMgr: update_deployment_manifest()
    MetadataMgr->>SSM: put_parameter(deployment_manifest)
    Note over SSM: /sf/{project}/{deployment}/manifest
```

## SSM Parameter Structure

### Deployment Manifest

```bash
Parameter: /{project}/{deployment}/manifest
Value: <complete deployment manifest JSON>
```

Successful deployment

```bash
Parameter: /{project}/{deployment}/manifest/deployed
Value: <complete deployment manifest JSON>
```

### Module Manifest

```bash
Parameter: /{project}/{deployment}/{group}/{module}/manifest
Value: <complete module manifest JSON>
```

### Module Metadata

```bash
Parameter: /{project}/{deployment}/{group}/{module}/metadata
Value: {
  "VpcId": "vpc-12345",
  "SubnetIds": ["subnet-123", "subnet-456"],
  "SecurityGroupId": "sg-789"
}
```

### Module MD5 Hash

```bash
Parameter: /{project}/{deployment}/{group}/{module}/md5/deployspec
Parameter: /{project}/{deployment}/{group}/{module}/md5/manifest
Parameter: /{project}/{deployment}/{group}/{module}/md5/bundle


Value: "abc123def456ghi789..."
```

### Deployspec

```bash
Parameter: /{project}/{deployment}/{group}/{module}/deployspec
Value: <complete module manifest YAML>
```

## MD5 Calculation Components

1. **Manifest Hash**: Resolved parameter values
2. **Bundle Hash**: Bundled module code (if remote deployment)
3. **Deployspec Hash**: Content of deployspec.yaml
