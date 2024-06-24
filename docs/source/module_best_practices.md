# Best Practices


## Ordering of Module Deployment
The `seedfarmer` CLI uses the [deployment manifest](manifests.md) group ordering to sequentially deploy groups (modules in a group are deployed in parallel), and this ordering is preserved.  On the destroy of the deployment, the reverse ordering of the groups is followed (still, each module in the group is destroy in parallel).  It is important to identify your module inter-dependancies and allocate them to the proper group in the proer order.  For example, if a compute resource (ex. an ec2 instance) needs to be deployed in a VPC, then the module that creates the VPC should be in a group that is deployed BEFORE the group that contains the EC2 module.  

The `seedfarmer` CLI does not currently support inter-module dependency management, so the best-pracice guideline is to group modules that are independent of one-another and order the groups based on module-dependancy.


***
## Preferred Build Tooling
The [deployspec](deployspec.md) supports using any executable library.  The preferred library is the [AWS CDKv2](https://docs.aws.amazon.com/cdk/v2/guide/home.html).  This version of the CDK allows for isolation of access to AWS Services for [AWS CodeBuld](https://docs.aws.amazon.com/codebuild/latest/userguide/welcome.html) via [AWS CodeSeeder](https://aws-codeseeder.readthedocs.io/en/latest/) to only the CodeBuild service in the context of deploying your code.  But, the deployspec also has the ability to execute commands that are outside of the CDK constructs.  This provides the least-privelege access to AWS resources without needing to give additional permissions 

***
## When to use a `modulestack.yaml` policy
Whenever the [deployspec](deployspec.md) is executing commands directly (ex. `aws s3 cp`), the role AWS CodeSeeder uses to exeucte the build needs to have access to those resources. This is done via the [modulestack.yaml](modulestack.md) policy.  Follow the least-priveleges guidelines for granting access within this policy.

***
## Validation of Module Code
We have available two (2) scripts that can format and check your moduel code:
* `scripts/fix.sh` - this will correct the format of your code or tell you what the issues are
* `scripts/validate.sh` - this will perform checks of your code for consistency

These are found in the [Seed-Farmer Git Repo](https://github.com/awslabs/seed-farmer)

You should run these against your module codebase prior to making code repository commits.
Feel free to copy these scripts into your own project for application to your modules

### fix.sh
The `fix.sh` script will apply standardization libraries to your code based on the language.
* `python` code uses [ruff](https://docs.astral.sh/ruff/)
* `typescript` code uses [prettier](https://www.npmjs.com/package/prettier)

To run, from commandline pass in the language and relative path to yur module:
```bash
./scripts/fix.sh --language python --path <relative path to code>
-- OR --
./scripts/fix.sh --language typescript --path <relative path to code>
```

### validate.sh
The `validate.sh` script will apply check libraries to your code based on the language.
* `python` code uses [ruff](https://docs.astral.sh/ruff/) and [mypy](https://mypy.readthedocs.io/en/stable/)
* `typescript` code uses [prettier](https://www.npmjs.com/package/prettier)
* `ALL CODE` - [cfn-lint](https://github.com/aws-cloudformation/cfn-lint) is applied to all `modulestack.yaml` files

To run, from commandline pass in the relative path to yur module:
```bash
./scripts/validate.sh --language python --path <relative path to code>
-- OR --
./scripts/validate.sh --language typescript --path <relative path to code>
```
***