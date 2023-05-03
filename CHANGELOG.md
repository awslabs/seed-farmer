# CHANGELOG

All notable changes to this project will be documented in this file.
This project adheres to [Semantic Versioning](http://semver.org/) and [Keep a Changelog](http://keepachangelog.com/).

## Unreleased

### New

### Changes

- removed overriding build image from seedfarmer which defaults the codebuild image to ubuntu 6.0 (which comes from codeseeder as default)
- updated codeseeder to 0.9.0

### Fixes

## v2.6.4 (2023-04-28)

### New

### Changes
- adding synth for both bootstrap templates when issuing `--as-target`
- addind `dataFile` support for local files and from git
- changed default codebuild image base to 3.0.0
### Fixes


## v2.6.3 (2023-04-18)

### New

### Changes
- adding support for evaluating the version of SSM and secretsmanager when calculating md5 of code (for redeploy)

### Fixes


## v2.6.2 (2023-04-17)

### New

### Changes

### Fixes
- update gitparser version to be 3.1.30

## v2.6.1 (2023-04-12)

### New

### Changes
- removed modules as they now are in `https://github.com/awslabs/seedfarmer-modules`

### Fixes
- fix for `gitpython` assuming that codecommit repos are unsafe
- fix resolution of parameters that have a False value
- fix adding verbose error messages when a manifest cannot be loaded
- fix destroy of modules sourced from git via disparate (non-cached) cli invocations

## v2.6.0 (2023-03-10)

### New
- Adding support for customer codebuild image overrides.  This IS backward-compatible
- Enable use of generic SEEDFARMER prefixed Env Variables in CodeBuild
- Example modules demonstrate use of SEEDFARMER generic Env Variables
- Adding `SeedFarmerProject` `SeedFarmerModule` `SeedFarmerDeployment` tags to module role
- Adding CLI support to synthesize the project policy for modification
- Add `projectPolicyPath` suppprt to `seedfarmer.yaml` to allow override of default project policy

### Changes
- {ProjectName}_PROJECT_NAME and SEEDFARMER_PROJECT_NAME Env Variables added to CodeBuild
- ProjectName Parameter passed to modulestack.yaml CFN Template

### Fixes
- Adding more descriptions in the README with links to read-the-docs
- Fix codebuild role name reference
- Fix support for project names with `-` characters
- Error handling around `list` commands when a module is not found
- Force seedfarmer to ingore project policies in module projects unless configred to use it
- Safe_load all yaml files (ref: V741010817)

## v2.5.0 (2023-02-08)

### New
- added VPC support of isolated subnets for `seedkit` - flow thru to codeseeder

### Changes
- updated manifest docs for isolated subnet support
- implemented Global and Regional Parameter name/value pair lookups
- updated manifest docs for Global and Regional Parameter support

### Fixes
- added module metadata to environment parameters on destroy of module
- forced the `apply` of a deployment to respect the `toolchainRegion` parameter
- allow fetch of build info of modules not successfully deployed


## v2.4.1 (2023-01-17)

### New

### Changes

### Fixes
- exit code of failed deleted modules changed from `0` to `1`

## v2.4.0 (2023-01-13)

### New
- Added intra-group validation of parameter references (prevent any intra-group dependencies)
- Added validation of module deletion to prevent deleting modules that have dependencies
- Added CLI lookup `seedfarmer list dependencies` to provide dependencies of a module
- Added CLI lookup `seedfarmer list buildparams` to provide the build env params of an existing build (based on build-id) of a module
- Added support for gitignore when getting MD5 for module bundles

### Changes
- catch exceptions when deleting a deployment but the project policy (stack) is still in use elewhere
- respect group ordering when destroying modules in an existing deployment
- in `module_info` changed alias of import from `store` to `ssm`
- modifiled bundle md5: removed `checksumdir`, added custom alg to respect directories and gitignore
- include module reference info to `Source version` of Codebuild console
- added documentation on how to use manifest parameters in the modulestack
- updating version of `aws-codeseeder` dependency to 0.7.0

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

