# CHANGELOG

All notable changes to this project will be documented in this file.
This project adheres to [Semantic Versioning](http://semver.org/) and [Keep a Changelog](http://keepachangelog.com/).


## Unreleased

### New
- Added intra-group validation of parameter references (prevent any intra-group dependencies)
- Added validation of module deletion to prevent deleting modules that have dependencies
- Added CLI lookup `seedfarmer list dependencies` to provide dependencies of a module
- Added CLI lookup `seedfarmer list buildparams` to provide the build env params of an existing build (based on build-id) of a module

### Changes
- catch exceptions when deleting a deployment but the project policy (stack) is still in use elewhere
- respect group ordering when destroying modules in an existing deployment
- in `module_info` changed alias of import from `store` to `ssm`

### Fixes
- updated pip library to `certifi~=2022.12.7` in requirements-dev (ref dependabot #4)

## v2.3.1 (2022-11-22)

### New

### Changes

### Fixes
- removed the serialized deployspec from the module manifest ssm to prevent bloat (Issue #186)
- corrected logic for mutating SSM for each module deployment (Issue #188)

## v2.3.0 (2022-11-09)

### New
- new `generateName` attribute on DeploymentManifest for dynamic creation of the deployment `name`
- added documentation for git sourcing of modules
- new --enable-session-timeout and --session-timeout-interval CLI options on apply and destroy

### Changes

### Fixes
- unable to destroy when module sourced from remote git repository


## v2.2.1 (2022-10-25)

### New
### Changes

### Fixes
- seedfarmer apply was not picking up .env at same level as `seedfarmer.yaml`
- all `list` functions did not respect the .env path relative to `seedfarmer.yaml`

## v2.2.0 (2022-10-24)

### New
- new --env-file CLI parameter on apply and destroy enabling specific declaration of the dotenv file to use

### Changes
- modified output messaging to use logger instead of bolded print when loading project configs

### Fixes
- exit code on on failed modules changed from 0 1o 1
- changed typo `Deployemnt` to `Deployment` everywhere
- improved validation and error handling when AccountId is not resolvable from EnvVariable
- truncate and generate unique role and stack names when identifier is too long


## v2.1.0 (2022-10-03)


### New
- added updated multi-account diagram source for docs
- added support for git repositories as source for module code

### Changes
- updated architecture diagram and verbiage in docs

### Fixes

## v2.0.0 (2022-09-22)

### New
- new CLI bootstrap commands for Toolchain and Target accounts
- create SessionManager class for supporting multi-account, multi-region
- bootstrap command support to generate CFN templates for Toolchain and Target accounts
- added deployment for toolchain and target accounts via CFN
- support for cross-account and cross-region deployments
- support for envVariable as valueFrom via .env and python-dotenv
- threaded the priming of accounts on create and destroy
- added destroy of managed polices when destroying deployments
- threaded module info fetching
- added account and region to module list output
- added region and profile support for CLI commands
- added multi-region support for list moduledata
- support ParameterStore and SecretsManager as sources for module parameters (new valueFrom types)
- added region adn profile support for all cli commands where needed


### Changes
- update DeploymentManifest to support targetAccountMappings and regionMappings
- update ModuleManifest to support targetAccount and targetRegion with defaults
- move deployment level Parameters (dockerCredentialsSecret, permissionsBoundaryName) to mappings
- refactor cli commands/groups to reduce line count in `__main__.py`
- moved projectpolicy.yaml into resources/.
- added profile and region support for session in `_session_utils.py`
- convertd `session_manager.py` to only use `_session_utils.py`
- refactored deployment_command objects and signatures for threadding

### Fixes
- fix import failure of seedfarmer top-level module if seedfarmer.yaml doesn't exist
- enable basic CLI functions by lazy loading seedfarmer.yaml and boto3.Session
- ensure get_account_id() and get_regin() always use correct boto3.Session
- ensure bootstrap functions look for roles and cfn templates when updating/deploying roles
- honed back deployment role permissions
- modified session manager to support threadding with the toolchain session
- rename manifest parameter permissionBoundaryArn -> permissionsBoundaryName to align on AWS naming and hide account ids in ARNs
- ensure we find a deploymed manifest when listing/printing module metadata

## v0.1.4 (2022-08-16)

### Changes
- updated user-friendly messages for invalid credentials / sessions
- added version support for CLI `seedfarmer version`
- updated dependency aws_codeseeder==0.4.0
- corrected import of CodeSeederRuntimeError

### Fixes
- allow CLI to return when exporting moduledata that is None
- remove table and short url for errored codebuild urls
- removed architecture diagram from Git README - it is in `readthedocs`

## v0.1.3 (2022-07-19)

### New
- support logging output and url gereration from codebuild output / codeseeder
- added use of CodeSeederRuntimeError
- added ModuleDeploymentResponse object
- added export of moduledata (metadata) in UNIX format from CLI (--export-local-env)

### Changes
- moved Parameter support to its own script
- removed arch diagram from README on git repo (the image does not translate on pypi).  It is in the readthedocs site

### Fixes
- eventual consistency of IAM policy to module-spcific role (issue 43)


---

## v0.1.2 (2022-07-12)

### New
- added example modules for buckets and networking

### Changes

### Fixes
- use HTTPS instead off SSH for git cloning


---
## v0.1.1 (2022-07-07)

### New
 - feature - added CLI ability to list deployspec of deployed module
 - feature - added CLI ability to store new deployspec of deployed module

### Changes
- change - enforce runtime versions of CodeSeeder
- lock versions in requirements-dev.in
- updating CLI output to discern changes to manifest, intended deployment
- lazy-load seedkit (version 0.3.2 of codeseeder)
- improve logging messages from codeseeder
- align message output / tables listing modules requested, modified, deleted for deployment

### Fixes
- update repo for project initialization
- update repo for module initalizaton
- optimize intialization (remove interactive input, require seedfarmer.yaml)

---
## v0.1.0  (2022-06-20)


### New
* initial commit and release of public SeedFarmer

### Changes

### Fixes

