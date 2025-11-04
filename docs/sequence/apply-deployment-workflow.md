# Apply Deployment Workflow

This sequence diagram shows the end-to-end process when running `seedfarmer apply manifest.yaml`.

```mermaid
sequenceDiagram
    participant User as User
    participant CLI as CLI Main
    participant ApplyCmd as Apply Command
    participant DeployCmd as Deployment Commands
    participant ManifestProc as Manifest Processing
    participant DepResolver as Dependency Resolver
    participant ModuleDeploy as Module Deployment
    participant AWS as AWS Services

    User->>CLI: seedfarmer apply manifest.yaml --profile prod
    CLI->>CLI: load_dotenv_files()
    CLI->>ApplyCmd: apply(spec, profile, region, ...)
    
    ApplyCmd->>DeployCmd: apply()
    DeployCmd->>ManifestProc: load_deployment_manifest()
    ManifestProc->>ManifestProc: parse YAML manifest
    ManifestProc->>ManifestProc: validate manifest schema
    ManifestProc-->>DeployCmd: DeploymentManifest object
    
    DeployCmd->>DeployCmd: process_git_module_paths()
    loop For each git module
        DeployCmd->>DeployCmd: clone_module_repo()
        DeployCmd->>DeployCmd: set_local_path()
    end
    
    DeployCmd->>DeployCmd: process_archive_paths()
    DeployCmd->>DeployCmd: process_data_files()
    
    DeployCmd->>DepResolver: resolve_dependencies()
    DepResolver->>DepResolver: build dependency graph
    DepResolver->>DepResolver: topological sort
    DepResolver-->>DeployCmd: ordered module list
    
    DeployCmd->>DeployCmd: load_parameter_values()
    DeployCmd->>AWS: resolve parameter references
    AWS-->>DeployCmd: parameter values
    
    loop For each module group (parallel)
        DeployCmd->>ModuleDeploy: deploy_modules_in_group()
        
        loop For each module in group
            ModuleDeploy->>ModuleDeploy: create ModuleDeployObject
            ModuleDeploy->>ModuleDeploy: DeployModuleFactory.create()
            ModuleDeploy->>ModuleDeploy: deploy_module()
            ModuleDeploy->>AWS: deploy infrastructure
            AWS-->>ModuleDeploy: deployment result
        end
        
        ModuleDeploy-->>DeployCmd: group deployment status
    end
    
    DeployCmd->>DeployCmd: write_deployment_manifest()
    DeployCmd-->>ApplyCmd: deployment complete
    ApplyCmd-->>CLI: success/failure
    CLI-->>User: deployment status
```

## Key Phases

1. **Initialization**: Load environment, parse CLI arguments
2. **Manifest Processing**: Parse and validate deployment manifest
3. **Source Preparation**: Clone git repos, fetch archives, process data files
4. **Dependency Resolution**: Build and sort dependency graph
5. **Parameter Resolution**: Resolve all parameter references
6. **Module Deployment**: Deploy modules in dependency order
7. **Completion**: Write final manifest and report status
