# Bootstrapping Accounts

You must have only one `toolhchain account` bootstrapped and at least one `target account` bootstrapped.  The account that is the `toolhchain account` can be bootstrapped as a `target account`.


## Bootstrap Toolchain Account
The `seedfarmer bootstrap toolchain` CLI command will take care of setting up the account.  
```bash
Usage: seedfarmer bootstrap toolchain [OPTIONS]

  Bootstrap a Toolchain account.

Options:
  -p, --project TEXT              Project identifier
  -t, --trusted-principal TEXT    ARN of Principals trusted to assume the
                                  Toolchain Role
  -b, --permissions-boundary TEXT  ARN of a Managed Policy to set as the
                                  Permission Boundary on the Toolchain Role
  --as-target / --not-as-target   Optionally also bootstrap the account as a
                                  Target account  [default: not-as-target]
  --synth / --no-synth            Synthesize a CFN template only...do not
                                  deploy  [default: no-synth]
  --profile TEXT                  The AWS profile to initiate a session
  --region TEXT                   AWS region to use
  --debug / --no-debug            Enable detail logging  [default: no-debug]
  --help                          Show this message and exit.
```

The `trusted-principal` field allows you to pass in one or multiple roles who CAN assume the `toolchain account` role.  If you do not pass in at least one, no one can assume this role (that is bad).

The `permission-boundary` filed allows you to attach a policy to the role to act as a [permissions boundary](https://docs.aws.amazon.com/IAM/latest/UserGuide/access_policies_boundaries.html)

Typically, you can have the `toolchain account` act as the `target account`.  The `as-target` field will bootstrap both in a single command. 



## Bootstrap Target Account

```bash
sage: seedfarmer bootstrap target [OPTIONS]

  Bootstrap a Target account.

Options:
  -p, --project TEXT              Project identifier
  -t, --toolchain-account TEXT    Account Id of the Toolchain account trusted
                                  to assume the Target account's Deployment
                                  Role  [required]
  -b, --permissions-boundary TEXT  ARN of a Managed Policy to set as the
                                  Permission Boundary on the Toolchain Role
  --synth / --no-synth            Synthesize a CFN template only...do not
                                  deploy  [default: no-synth]
  --profile TEXT                  The AWS profile to initiate a session
  --region TEXT                   AWS region to use
  --debug / --no-debug            Enable detail logging  [default: no-debug]
  --help                          Show this message and exit.
```

You must pass in the `toolchain-account` field so a trust-relationship can be set up between the `toolchain account` role and the `target account` role.

The `permission-boundary` filed allows you to attach a policy to the role to act as a [permissions boundary](https://docs.aws.amazon.com/IAM/latest/UserGuide/access_policies_boundaries.html)

## Prepping the Account / Region
`seedfarmer` leverages the AWS CDKv2.  This must be bootstrapped in ech account/region combination to be used of each target account.