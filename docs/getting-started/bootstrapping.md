---
title: Bootstrapping
---

Before you can use Seed-Farmer to deploy resources, you need to bootstrap your AWS accounts. This guide explains how to bootstrap your toolchain and target accounts.

## Account Types

Seed-Farmer uses two types of accounts:

- **Toolchain Account**: The primary account that stores deployment metadata and coordinates deployments
- **Target Account(s)**: The account(s) where modules are actually deployed ( *target account and deployment account are referred to  synonymously in this document* )

You must have only one toolchain account bootstrapped and at least one target account bootstrapped. The account that is the toolchain account can also be bootstrapped as a target account.

## Bootstrap Toolchain Account

*You must have completed the [Installation](installation.md)*

Please see [Bootstrapping Commands](../reference/cli-commands.md/#bootstrap or run the `--help` flag for all options.

The `seedfarmer bootstrap toolchain` command sets up the toolchain account with the necessary IAM roles and permissions.  

```bash
seedfarmer bootstrap toolchain \
  --project PROJECT_NAME \
  --trusted-principal PRINCIPAL_ARN \
```

### Example

For this guide, we will let the project name be `myproject` and use an arbitrary ARN:

```bash
seedfarmer bootstrap toolchain \
  --project myproject \
  --trusted-principal arn:aws:iam::123456789012:role/DevOps \
  --as-target
```

This command:

1. Sets up the toolchain account with the necessary IAM roles
2. Also bootstraps the account as a target account (`--as-target`)
3. Uses the project name `myproject`
4. Trusts the `DevOps` role to assume the toolchain role

## Bootstrap Target Account

The `seedfarmer bootstrap target` command sets up a target account with the necessary IAM roles and permissions.

```bash
seedfarmer bootstrap target \
  --project PROJECT_NAME \
  --toolchain-account ACCOUNT_ID
```

### Example

Continue to use the project name as `myproject`.

```bash
seedfarmer bootstrap target \
  --project myproject \
  --toolchain-account 123456789012
```

This command:

1. Sets up the target account with the necessary IAM roles
2. Uses the project name `myproject`
3. Trusts the toolchain account `123456789012` to assume the target account's deployment role

## Qualifiers for Roles

You can use qualifiers to segregate target deployments when using a multi-account structure. A qualifier appends a 6-character alpha-numeric string to the deployment role and toolchain role.

!!! important
    The qualifier **must be the same** on the toolchain role and each target role.

## IAM Path Prefixes

You can use IAM path prefixes for the toolchain role, target account deployment roles, and policies. This allows you to create logical separation to simplify permissions management.

IAM paths must begin and end with a `/`. For example:

```bash
seedfarmer bootstrap toolchain \
  --project myproject \
  --trusted-principal arn:aws:iam::123456789012:role/DevOps \
  --role-prefix /myproject/ \
  --policy-prefix /myproject/
```

## Deployment Role Security Controls

The deployment role includes explicit deny policies for certain high-risk IAM actions to improve security posture. These include:

- `iam:CreateAccessKey`
- `iam:CreateLoginProfile`
- `iam:UpdateLoginProfile`
- `iam:AddUserToGroup`
- `iam:AttachGroupPolicy`
- `iam:AttachUserPolicy`
- `iam:CreatePolicyVersion`

These restrictions help maintain security by preventing potential privilege escalation paths while still allowing the deployment role to perform its intended functions.

## Seedkit Infrastructure

In addition to the IAM roles created during bootstrapping, Seed-Farmer automatically deploys [Seedkit Infrastructure](../concepts/architecture.md#seedkit-infrastructure) in each target account and region during your first deployment. The seedkit provides the core infrastructure components needed for module deployments:

- **AWS CodeBuild Project**: Executes module deployments
- **S3 Bucket**: Stores deployment bundles and artifacts  
- **CloudWatch Log Groups**: Captures deployment execution logs
- **IAM Service Roles**: Enables CodeBuild execution

The seedkit is deployed automatically when you run `seedfarmer apply` and is essential for deployments. You can also manually manage the seedkit using CLI commands.

For detailed information about the seedkit architecture, components, and configuration options, see the [Seedkit Infrastructure](../concepts/architecture.md#seedkit-infrastructure) section in the Architecture documentation.

## Minimum Permissions Required for Bootstrap

The following policy outlines the minimum required IAM permissions to execute `seedfarmer bootstrap` commands:

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "CFNPolicySID",
            "Effect": "Allow",
            "Action": [
                "cloudformation:CreateChangeSet",
                "cloudformation:DescribeChangeSet",
                "cloudformation:ExecuteChangeSet",
                "cloudformation:DescribeStacks"
            ],
            "Resource": [
                "arn:aws:iam:::role/seedfarmer-*-toolchain-role",
                "arn:aws:cloudformation:*:*:stack/seedfarmer-exampleproj-toolchain-role/*",
                "arn:aws:cloudformation:*:*:stack/seedfarmer-exampleproj-deployment-role/*"
            ]
        },
        {
            "Sid": "IAMPolicySID",
            "Effect": "Allow",
            "Action": [
                "iam:GetRole",
                "iam:DeleteRolePolicy",
                "iam:TagRole",
                "iam:CreateRole",
                "iam:DeleteRole",
                "iam:PutRolePolicy"
            ],
            "Resource": "arn:aws:iam:::role/seedfarmer-*"
        }
    ]
}
```

!!! note
    Replace `exampleproj` with your project name.

## Next Steps

After bootstrapping your accounts, you can:

- Follow the [Quick Start](quick-start.md) guide to deploy your first project
- Learn about [Manifests](../reference/manifests.md) to define your deployments
- Explore [Module Development](../guides/module-development.md) to create your own modules
