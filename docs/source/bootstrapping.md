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


## Prepping the Account / Region
`seedfarmer` leverages the AWS CDKv2.  This must be bootstrapped in each account/region combination to be used of each target account.
