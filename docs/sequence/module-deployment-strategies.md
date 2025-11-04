# Module Deployment Strategies

This sequence diagram shows how Seed-Farmer determines and executes module deployment strategies (Local vs Remote).

```mermaid
sequenceDiagram
    participant CLI as CLI Command
    participant Factory as DeployModuleFactory
    participant SessionMgr as SessionManager
    participant LocalDeploy as DeployLocalModule
    participant RemoteDeploy as DeployRemoteModule
    participant CodeBuild as AWS CodeBuild
    participant LocalExec as Local Executor

    CLI->>Factory: create(ModuleDeployObject)
    Factory->>SessionMgr: get session instance
    SessionMgr-->>Factory: session type
    
    alt SessionManagerLocalImpl
        Factory->>LocalDeploy: new DeployLocalModule(mdo)
        Factory-->>CLI: LocalDeploy instance
        
        CLI->>LocalDeploy: deploy_module()
        LocalDeploy->>LocalDeploy: _prebuilt_bundle_check()
        
        alt Bundle exists in S3
            LocalDeploy->>LocalDeploy: use prebuilt bundle
        else No prebuilt bundle
            LocalDeploy->>LocalExec: execute deployspec locally
            LocalExec->>LocalExec: run build commands
            LocalExec->>LocalExec: run deploy commands
            LocalExec-->>LocalDeploy: deployment result
        end
        
        LocalDeploy-->>CLI: ModuleDeploymentResponse
        
    else SessionManagerRemoteImpl
        Factory->>RemoteDeploy: new DeployRemoteModule(mdo)
        Factory-->>CLI: RemoteDeploy instance
        
        CLI->>RemoteDeploy: deploy_module()
        RemoteDeploy->>RemoteDeploy: _prebuilt_bundle_check()
        
        alt Bundle exists in S3
            RemoteDeploy->>RemoteDeploy: use prebuilt bundle
        else No prebuilt bundle
            RemoteDeploy->>CodeBuild: create CodeBuild project
            RemoteDeploy->>CodeBuild: start build
            CodeBuild->>CodeBuild: run deployspec in container
            CodeBuild-->>RemoteDeploy: build status
            RemoteDeploy->>RemoteDeploy: monitor build progress
        end
        
        RemoteDeploy-->>CLI: ModuleDeploymentResponse
    end
```

## Key Decision Points

1. **Session Type Detection**: The factory checks the SessionManager type to determine deployment strategy
    - Local deployments only support a single account / region and SeedFarmer manages this without the need to change manifests
2. **Bundle Optimization**: Only remote deployments check for prebuilt bundles in S3 to support destroy processing
3. **Execution Environment**:
    - Local: Runs deployspec commands directly on the local machine
    - Remote: Creates and executes CodeBuild projects in AWS

## Strategy Selection

- **Local Strategy**: Used when `--local` flag is set or when using local AWS credentials
- **Remote Strategy**: Default strategy using SeedFarmer toolchain roles and CodeBuild for isolation
