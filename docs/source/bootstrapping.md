# Bootstrapping Accounts

You must have only one `toolchain account` bootstrapped and at least one `target account` bootstrapped.  The account that is the `toolchain account` can be bootstrapped as a `target account`.


## Bootstrap Toolchain Account
The `seedfarmer bootstrap toolchain` CLI command will take care of setting up the account.  
```text
Usage: seedfarmer bootstrap toolchain [OPTIONS]

  Bootstrap a Toolchain account.

Options:
  -p, --project TEXT              Project identifier
  -t, --trusted-principal TEXT    ARN of Principals trusted to assume the
                                  Toolchain Role. This can be used multiple
                                  times to create a list.
  -b, --permissions-boundary TEXT
                                  ARN of a Managed Policy to set as the
                                  Permission Boundary on the Toolchain Role
  --as-target / --not-as-target   Optionally also bootstrap the account as a
                                  Target account  [default: not-as-target]
  --synth / --no-synth            Synthesize a CFN template only...do not
                                  deploy  [default: no-synth]
  --profile TEXT                  The AWS profile to initiate a session
  --region TEXT                   AWS region to use
  --qualifier TEXT                A qualifier to append to toolchain role
                                  (alpha-numeric char max length of 6)
  --role-prefix TEXT              An IAM path prefix to use with the
                                  seedfarmer roles.
  --policy-prefix TEXT            An IAM path prefix to use with the
                                  seedfarmer policies.
  -pa, --policy-arn TEXT          ARN of existing Policy to attach to Target
                                  Role (Deploymenmt Role) This can be use
                                  multiple times, but EACH policy MUST be
                                  valid in the Target Account. The `--as-
                                  target` flag must be used if passing in
                                  policy arns as they are applied to the
                                  Deployment Role only.
  --debug / --no-debug            Enable detail logging  [default: no-debug]
  --help                          Show this message and exit.
```

The `trusted-principal` field allows you to pass in one or multiple roles who CAN assume the `toolchain account` role.  If you do not pass in at least one, no one can assume this role (that is bad).

The `permission-boundary` filed allows you to attach a policy to the role to act as a [permissions boundary](https://docs.aws.amazon.com/IAM/latest/UserGuide/access_policies_boundaries.html)

Typically, you can have the `toolchain account` act as the `target account`.  The `as-target` field will bootstrap both in a single command. 


## Bootstrap Target Account

```text
Usage: seedfarmer bootstrap target [OPTIONS]

  Bootstrap a Target account.

Options:
  -p, --project TEXT              Project identifier
  -t, --toolchain-account TEXT    Account Id of the Toolchain account trusted
                                  to assume the Target account's Deployment
                                  Role  [required]
  -b, --permissions-boundary TEXT
                                  ARN of a Managed Policy to set as the
                                  Permission Boundary on the Toolchain Role
  --synth / --no-synth            Synthesize a CFN template only...do not
                                  deploy  [default: no-synth]
  --profile TEXT                  The AWS profile to initiate a session
  --region TEXT                   AWS region to use
  --qualifier TEXT                A qualifier to append to target role (alpha-
                                  numeric char max length of 6)
  --role-prefix TEXT              An IAM path prefix to use with the seedfarmer
                                  roles.
  -pa, --policy-arn TEXT          ARN of existing Policy to attach to Target
                                  Role (Deploymenmt Role) This can be use
                                  multiple times to create a list, but EACH
                                  policy MUST be valid in the Target Account
  --debug / --no-debug            Enable detail logging  [default: no-debug]
  --help                          Show this message and exit.
```

You must pass in the `toolchain-account` field so a trust-relationship can be set up between the `toolchain account` role and the `target account` role.

The `permission-boundary` field allows you to attach a policy to the role to act as a [permissions boundary](https://docs.aws.amazon.com/IAM/latest/UserGuide/access_policies_boundaries.html)


## Qualifiers for Toolchain Role and Target Roles
We have added support for the use of a qualifier for the toolchain role and the target account deployment role(s).  This is to help segregate target deployment when using a multi-account structure which has a central shared services (CICD account) as the toolchain account performing deployments across relevant environments (ex. DEV, INT, PROD). A `qualifier` can be used if you want to restrict the level of access/action a dev/tester/support team can perform on any target given environment.

The qualifier post-pends a 6 chars alpha-numeric string to the deployment role and toolchain role.  The qualifier **MUST BE THE SAME ON THE TOOLCHAIN ROLE AND EACH TARGET ROLE.**


## IAM Paths Prefixes for Toolchain, Target Roles, and Policies
We have added support for the use of a IAM Paths for the toolchain role, target account deployment role(s), and policie(s). Using IAM Paths you can create groupings and design a logical separation to simplify permissions management. A common example in organizations is using Service Control Policies enforcing logical separation by team e.g. `/legal/` or `/sales/`, or project name.

## Deployment Role Security Controls
The deployment role includes explicit deny policies for certain high-risk IAM actions to improve security posture. The following IAM actions are explicitly denied regardless of any allow statements that might exist elsewhere in the policy:

- `iam:CreateAccessKey` - Prevents creation of permanent access keys
- `iam:CreateLoginProfile` - Prevents creation of console passwords
- `iam:UpdateLoginProfile` - Prevents modification of console passwords
- `iam:AddUserToGroup` - Prevents adding users to groups which could escalate privileges
- `iam:AttachGroupPolicy` - Prevents attaching policies to groups
- `iam:AttachUserPolicy` - Prevents attaching policies directly to users
- `iam:CreatePolicyVersion` - Prevents creating new versions of IAM policies
- `iam:DeleteGroupPolicy` - Prevents deletion of inline policies from groups
- `iam:DeleteUserPolicy` - Prevents deletion of inline policies from users
- `iam:DetachGroupPolicy` - Prevents detachment of policies from groups
- `iam:DetachUserPolicy` - Prevents detachment of policies from users
- `iam:PutGroupPolicy` - Prevents adding inline policies to groups
- `iam:PutUserPolicy` - Prevents adding inline policies to users
- `iam:RemoveUserFromGroup` - Prevents removing users from groups
- `iam:SetDefaultPolicyVersion` - Prevents changing which version of a policy is active

These restrictions help maintain security by preventing potential privilege escalation paths while still allowing the deployment role to perform its intended functions.

A `--role-prefix` and `--policy-prefix` CLI parameters can be used if you want to provide IAM Paths to the toolchain, target roles, and project policy created by `seed-farmer`. If bootstrapped with prefixes, the same prefixes must be provided with `apply` and `destroy` CLI commands so that seedfarmer is able to locate the correct toolchain and target deployment roles. IAM Paths must begin and end with a `/`. More information in [IAM identifiers](https://docs.aws.amazon.com/IAM/latest/UserGuide/reference_identifiers.html).

Additionally, seed-farmer creates module deployment roles at `apply`. It is possible to provide prefixes for the module deployment roles using the deployment manifest. See [manifests](manifests.md).

## Prepping the Account / Region
`seedfarmer` leverages the AWS CDKv2.  This must be bootstrapped in each account/region combination to be used of each target account.

## Minimum Permissions Required for Bootstrap
The following policy outlines the minimum required IAM permissions in order to execute `seedfarmer bootstrap ..` against a toolchain/target account. **Note**: The project name `exampleproj` is used in this policy as an example. This would need to be changed to the project name in `seedfarmer.yaml`.

```
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "VisualEditor0",
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
            "Sid": "VisualEditor1",
            "Effect": "Allow",
            "Action": [
                "iam:GetRole",
                "iam:DeleteRolePolicy",
                "iam:TagRole",
                "iam:CreateRole",
                "iam:DeleteRole",
                "iam:PutRolePolicy"
            ],
            "Resource": "*"
        }
    ]
}
```
