# Quick Start Guide

This is a quick start guide to get you ready to deploy with `seed-farmer`.  This should not be used INSTEAD of reading the documentation.

NOTE: this is an abberviated version of the [Deployment Guide](deployment_guide.md)

This assumes the following:
- the account you are using has an account id of `123456789012`
- the role you will be using to invoke `seedfarmer` is `arn:aws:iam::123456789012:role/Admin`
- your toolchain account and target account / deployment account are one in the same
- the name of your project is `exampleproj`  (as an example)
- the aws cdk libraries are already installed

### Prep your Environment

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install seed-farmer
cdk bootstrap aws://123456789012/us-east-1
```

### Bootstrap Your Account
```bash
seedfarmer bootstrap toolchain \
--project exampleproj \
-t arn:aws:iam::123456789012:role/Admin \
--as-target
```

### Deploy a Deployment in the Project
Now you can deploy any `seed-farmer` compliant project / module(s).  We have included a sample in the [Seed-Farmer git repo](https://github.com/awslabs/seed-farmer) that has a project named `exampleproj` and a deployment named `examples`.

```bash
mkdir mycodebase && cd mycodebase
git clone https://github.com/awslabs/seed-farmer.git
cd seed-farmer/examples/exampleproject
echo PRIMARY_ACCOUNT=123456789012 >>.env
seedfarmer apply manifests/examples/deployment.yaml --env-file .env
```


Congratulations...you are now deploying.

### Destroy a Deployment
```bash
seedfarmer destroy examples --env-file .env
```

Now you have destroyed.



