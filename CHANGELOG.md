# CHANGELOG

All notable changes to this project will be documented in this file.
This project adheres to [Semantic Versioning](http://semver.org/) and [Keep a Changelog](http://keepachangelog.com/).





## v0.2.0 (2022-07-19)

### New
- support logging output and url gereration from codebuild output / codeseeder
- added use of CodeSeederRuntimeError
- added ModuleDeploymentResponse object 
- added export of moduledata (metadata) in UNIX format from CLI (--export-local-env)

### Changes
- moved Parameter support to its own script

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

