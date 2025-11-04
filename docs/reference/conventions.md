# Standard Formats and Configurations

## Global Replace in Manifests

Seed-Farmer traditionally uses the [Environment Parameter](manifests.md)  as a means to get environment parameter at runtime to be declarative about the field requested:

A more recent feature was the use of Global Value Replace for manifests.  Any value in a manifest, when surrounded by `${}` can be replaced with the value of the referred to environment parameter if it exists.

```yaml
name: example
toolchainRegion: ${PREFERRED}
forceDependencyRedeploy: false
targetAccountMappings:
  - alias: production
    accountId: ${MYACCOUNTID}
```

In the above example, the `MYACCOUNTID` and `PREFERRED` will be replaced with the value of the environment parameter if it exist.

!!! warning "Not for Keys"
    This only works for values in the manifests, not keys.  If the environment parameter is not defined, the processing will error and stop.

## Module Sourcing

SeedFarmer supports sourcing modules from the following:
  
- Local Filesystem
- Git Repositories
- Archives (zip and tar via HTTPS)

A particular naming convention is defined via examples.

### Local Filesystem

For development purposes, modules can be sourced from local filesystems.  

The path element MUST ALWAYS be relative to the directory where `seedfarmer.yaml` is located.

```yaml
path: module-name
path: module/mygroup/module-name

```

### Git-compliant Repositories

Seed-Farmer supports fetching modules from Git-compliant repositories, including AWS CodeArtifact, based on branches, commit tags, and commit hashes.

```yaml
path: git::https://github.com/awslabs/idf-modules.git//modules/dummy/blank?ref=release/1.2.0
path: git::https://github.com/awslabs/idf-modules.git//modules/dummy/blank?ref=v1.1.0
path: git::https://github.com/awslabs/idf-modules.git//modules/dummy/blank/?ref=2d0aee3880bbf195129c441529f91ad074983037


path: git::codecommit::us-west-2://idf-modules.git//modules/dummy/blank?ref=release/1.2.0
path: git::codecommit::us-east-1://idf-modules.git//modules/dummy/blank/?ref=v1.0.0
path: git::codecommit::us-east-1://idf-modules.git//modules/dummy/blank/?ref=2d0aee3880bbf195129c441529f91ad074983037


```

!!! warning "Recommended Practices"
    Referring to a branch, tag, or commit hash provides a level of certainty that the code is consistent.

!!! info "Git Module Sourcing"
    The path can be sourced from Git using the [semantic defined by HashiCorp for Terraform](https://developer.hashicorp.com/terraform/language/modules/configuration#module-sourcing)

### Hosted Archives

Archives hosted from a URL are also supported.  The archive should have a scheme in which a path is defined from the root of the archive, rather than placing the files right at the root.  This is to identify and isolate the exact code referenced

```yaml

path: archive::https://github.com/awslabs/idf-modules/archive/refs/tags/v1.6.0.tar.gz?module=modules/dummy/blank
path: archive::https://github.com/awslabs/idf-modules/archive/refs/tags/v1.6.0.zip?module=modules/dummy/blank

```
