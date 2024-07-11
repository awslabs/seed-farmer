# Overview
`seedfarmer` is a python-based CICD library that leverages the GitOps paradigm to manage deployed code.  It is tooling-agnostic (can support AWS CDK, CloudFormation, bash scripting, Terraform, etc).  It leverages declarative manifests to define deployable code (`modules`), and manages the state of the deployed code - detecting and applying changes as needed.  

(multiaccount_support)=
## Multi Account Support
`seedfarmer` uses the concept of a`toolchain account` and `target account`(s).  These accounts have roles associated with them that have the minimal permissions necessary to perform deployments.  The `toolchain account` role assumes the `target account` role.  `seedfarmer` is configured that ONLY this role assumption can occur.

- `toolchain account` -- the primary account that:
  - stores the deployment-specific information
  - has the `toolchain-role` necessary to manage and coordinate `seedfarmer` deployments
  - is region-centric due to metadata storage
- `target account` -- the account(s) where:
  - modules are deployed
  - has the `deployment-role` necessary to deploy modules
  - is region-centric due to metadata storage

There can be at any time only ONE (1) `toolchain account` with MANY `target account`s.  And, a `toolchain account` can be also `target account`. Each account only needs to be boostrapped once - regardless of the region that modules are deployed.  The `roles` created are global to the account. 


## Concepts
All `seedfarmer` deployments leverage a logical separation of artifacts.  A single `Project` can have multiple `Deployments` of `Groups` of `Modules`.

`Project` - a project as a direct one-to-one relationship with the [AWS Codeseeder](https://aws-codeseeder.readthedocs.io/en/latest/) managed CodeBuild project.  You can have multiple projects in an account(s) and they are isolated from one another (no one project can use artifact from another project).

`Deployment` - a deployment represents all the modules leveraging AWS resources in one or many accounts.  It is metadata that gives isolation from other deployments in the same project.

`Group` - a group represents all modules that can be deployed concurrently. No module in a group can have a dependency on another module in the same group.  `seedfarmer` keeps track of the ordering of groups for deployment and reverses the ordering of the groups for destruction.

`Module` - a module is what gets deployed.  It is represented by code.  A module can be deployed multiple times in the same `Deployment` as long as it has a unique logical name
