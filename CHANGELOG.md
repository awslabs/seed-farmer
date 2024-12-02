# CHANGELOG

All notable changes to this project will be documented in this file.
This project adheres to [Semantic Versioning](http://semver.org/) and [Keep a Changelog](http://keepachangelog.com/).

## Unreleased

### New 

### Changes

### Fixes


## v5.0.1 (2024-12-02)

### New 

### Changes

- Adds `seedfarmer --version` to validate package without running explicit command
- Added ability to disable env replacement in module parameters
- Updating bootstrap docs with minimum permissions
- Update manifest example module versions
- Update session manager to pass toolchain role region to sts

### Fixes
- allow nested modules in archives pulled over HTTPS (ref issue/749)

## v5.0.0 (2024-08-16)

### New

- Added `-b/--template-branch` parameter to `seedfarmer init project` and `seedfarmer init module` so it permits to use multiple branches from a single repository.
- Added support for downloading modules from archives using HTTPS
- Added generic module deployment roles for modules without modulestack

### Changes

### Fixes
- Adds validation for trusted principal arns in `seedfarmer bootstrap toolchain`

## v4.0.4 (2024-07-19)

### New

### Changes
- adds support for npm mirrors to be set 

### Fixes

- value replacement from environment variables was only working for the first value


## v4.0.3 (2024-07-11)

### New

### Changes

### Fixes
- when a bundle is available on destroy, ignore the path entirely

## v4.0.2 (2024-07-08)

### New

### Changes
- adding support for module manifest schema generation
- updates to dependency libraries (from dependabot):
  - certifi~=2024.7.4
  - boto3~=1.34.140
  - botocore~=1.34.140
  - pydantic~=2.8.2
  - pydantic-core~=2.20.1

### Fixes


## v4.0.1 (2024-06-10)

### New

### Changes

### Fixes
- correcting how SeedFarmer stores deployed manifests of previously deployed modules in SSM


## v4.0.0 (2024-06-03)

### New
- adding support for S3 to store bundles
  - see [UPGRADE to 4.0.0](https://seed-farmer.readthedocs.io/en/latest/upgrades.html#upgrading-to-4-0-0)
- adding seedfarmer version tag to toolchain and deployment roles
- removing python 3.7 support
- adding python 3.12 support 

### Changes
- adding local path of manifests that fail to load to the actual final string printed
  - this is already being done, but moving closer to last line of output
- updating idna>=3.7 everywhere
### Fixes

## v3.5.2 (2024-06-10)

### New

### Changes

### Fixes
- correcting how SeedFarmer stores deployed manifests of previously deployed modules in SSM
  - this is corrected in later releases, but need to support in case not everyone has upgraded


## v3.5.1 (2024-05-21)

### New

### Changes

### Fixes
- updating requests library  `requests==2.32.0`


## v3.5.1 (2024-05-21)

### New

### Changes

### Fixes
- updating requests library  `requests==2.32.0`

## v3.5.0 (2024-05-09)

### New
- adding universal environment replace in manifests (ref: `${SOMEKEY}`)
- adding list recursion of manifests for environment variable replace
- adding support for AWS SecretsManager integration for pypi mirrors

### Changes
- enforce strict validation for unknown values in manifests

### Fixes
- resolving parameter values via regional / global mappings needs to use account id, not alias

## v3.4.0 (2024-04-19)

### New
- added support for pypi mirror at module, region and account levels
- added support for npm mirror at module, region and account levels
### Changes
- refactored code to use ModelDeployObject for ease of implementation
### Fixes


## v3.3.1 (2024-04-08)

### New

### Changes

### Fixes
- metadata sourced from file to the os env cannot be parsed if not compliant json, adding code to check for this

## v3.3.0 (2024-04-01)

### New
- support to generate schema for manifests from CLI (`seedfarmer list schema`)
- added commithash persistence support for modules sourced from git
  - recorded in module manifest (`commit_hash`)
  - recorded in module metadata as `SeedFarmerModuleCommitHash` and can be fetched

### Changes
- renaming the threads spawned for deploy / destroy to indicate the module being worked on
- adding detailed docs for CLI parameters
- complete support to delete the seedkit on `seedfarmer destroy` command
- adding verbose messaging to session manager and hints to reconcile session issues
- adding info for destroy and list deployments when no deployments found
- refactored git support logic to separate python file
- added verbose messaging related to git issues
- updated `black~=24.3.0` in requirements-dev as per dependabot
- updated `werkzeug~=2.3.8` in requirements-dev as per dependabot
- removed explicit support for python 3.7
  - this was only due to support for black in requirements-dev, but was also removed from setup.py
- loosened restrictions on `typing-requirements` library 


### Fixes
- Add schema validation step checking that either `value` or `value_from` is present for each parameter

## v3.2.2 (2024-02-27)

### New

### Changes
- handle errors in metadata support when cannot read from file of codebuild

### Fixes


## v3.2.1 (2024-02-27)


## Unreleased

### New

### Changes

### Fixes
- ordering of metadata when using helper commands was backwards in `metadata_support.py`

## v3.2.0 (2024-02-26)

### New
- support list of env files using `--env-file`

### Changes
- adding `AwsCodeSeederDeployed` and `SeedFarmerDeployed` to all module metadata output for reference (versions used to deploy successfully)
- adding `AWS_CODESEEDER_VERSION` and `SEEDFARMER_VERSION` to all module environment parameters for reference (versions currently in use)
- added `--update-seedkit` support to `apply` 
  - SeedFarmer will no longer try to update the seedkit on every request
  - Users can override this with the `--update-seedkit` flag in case AWS CodeSeeder has updated the SeedKit
- added `--update-project-policy` support to `apply` 
  - SeedFarmer will apply a changeset to the project policy when this flag is set

### Fixes
- adding in workaround for manifests whose char length is greater than SSM limit of 8192 k


## v3.1.2 (2024-01-24)

### New

### Changes

### Fixes
- packaging library missing from setup

## v3.1.1 (2024-01-22)

### New

### Changes
  - updating readthedocs configs as site has changed their requirements

### Fixes


## v3.1.0 (2024-01-22)

### New
- adding AWS curated codebuild iamge override with opinionated runtimes

### Changes
- updating pydantic support from 1.X.X to 2.5.3
- adding seedfarmer verions check support with `seedfarmer.yaml`
- updating `aws-codeseeder` dependency top 0.11.0

### Fixes
- update `manifests/examples/` to point to an updated release branch
- Docs - manifest name description (seed-farmer/docs/source/manifests.md) needed correction
- Docs - added definition of `nameGenerator` for deployment manifest (seed-farmer/docs/source/manifests.md)

## v3.0.1 (2023-11-10)

### New

### Changes
- force attach the managed policy to the module role during `destroy`

### Fixes

## v3.0.0 (2023-11-02)

### New
- BREAKING CHANGE*** - the checksum calculation used to trigger module redeploy has changed
- Existing deployed modules may incur a redeployment when going from a previous version
  - resolve global/regional parameters when calculating checksum for individual module redeploy
  - resolve env parameters when calculating checksum for individual module redeploy

### Changes

### Fixes

## v2.10.5 (2023-10-20)

### New

### Changes
- adding support for module-type spec on init of new module `seedfarmer init module -mt cdkv2`

### Fixes
- skip destroy of managed-project-policy if it has roles attached
- if managed-project-policy is in an `*_IN_PROCESS` state, wait 60 seconds and check again
  - bumps `aws-codeseeder~=0.10.2`

## v2.10.4 (2023-10-23)

### New

### Changes
- updating `urllib~=1.26.17` for http-cookie vulnerability
- update `aws-codeseeder~=0.10.1`

### Fixes
- corecting urllib hard dependency version
- global and regional param resolution should usse account_alias instead of account_id

## v2.10.3 (2023-09-22)

### New

### Changes
- forcing `certifi~=2023.7.22` in all references due to e-Tugra security notification [HERE](https://groups.google.com/a/mozilla.org/g/dev-security-policy/c/C-HrP1SEq1A?pli=1)
- adding `concurrency` definition to the docs
- updating `urllib==1.26.5` in docs/requirements-docs.in
- adding in seedkit redeploy information in the `Architecture` section of the docs
- allow non-json compliant ssm parameters to be parsed when using module-specifics paths (`/<project>/<dep>/<mod>/databaseinfo`)
### Fixes

## v2.10.2 (2023-07-28)

### New

### Changes
- removing pyjq library dependency (installation issues with library)

### Fixes
- raising error if an env variable specified by parameter is not found

## v2.10.1 (2023-07-25)

### New

### Changes

### Fixes
- correct the arn generation of inline policy for docker secrets policy

## v2.10.0 (2023-07-21)

### New
- added support for other partitions (`aws-cn` and `aws-us-gov`)
- added CLI commands to be used as boilerplate code in deployspec for managing metadata
  - ref: https://seed-farmer.readthedocs.io/en/latest/manifests.html#deployment-manifest
### Changes
- updated aws-codeseeder depenedency to 0.10.0

### Fixes

## v2.9.4 (2023-06-29)

### New

### Changes

### Fixes
- updated how remote repos are created and pulled to support code-commit

## v2.9.3 (2023-06-28)

### New

### Changes
- adding support for gitpath sourced modules based on commit hash

### Fixes

## v2.9.2 (2023-06-28)

### New

### Changes
- applying local path eval consistently, updating patch release 2.9.1 chnage for modulestack.yaml eval

### Fixes

## v2.9.1 (2023-06-27)

### New

### Changes

### Fixes
- handle exceptions when cloned repo based off tags is in a detached HEAD state
- proper parsing of modulestack.yaml path if sourced from git

## v2.9.0 (2023-06-16)

### New
- adding qualifier support for bootstrap roles
- adding support to attach policies to target role when bootstrapping

### Changes
- raise error if a metadata parameter or value_from parameter is not available
### Fixes

## v2.8.0 (2023-05-23)

### New
- added `forceDependencyRedeploy` feature to codebase
### Changes
- updated `requests~=2.31.0` in requirements-dev.* to align to dependabot

### Fixes

## v2.7.2 (2023-05-22)

### New

### Changes
- implement custom error classes, remove all `exit()` commands
- added debug component to print all codebuild urls, regardless of status

### Fixes


## v2.7.1 (2023-05-17)

## Unreleased

### New

### Changes

### Fixes
- allow for SSM parameter to be either string or json-compliant when a single value

## v2.7.0 (2023-05-16)

### New
- adding HTTP-Proxy (this is a backward-compatible change)
- adding `seedfarmer list allmoduledata` to fetch all the metadata in a deployment in a single call
- adding Network configuration support from SSM and EnvVariables


### Changes
- refactored deployment_commands
- added python upper limit versioning (to `<3.12`)

### Fixes
- typo in messaging about errored manifest

## v2.6.5 (2023-05-03)

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

