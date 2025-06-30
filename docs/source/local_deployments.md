# Codebuild Local Agents for Testing Deployments

SeedFarmer now supports using [AWS CodeBuild Agent](https://docs.aws.amazon.com/codebuild/latest/userguide/use-codebuild-agent.html) to allow deployments of SeedFarmer-compliant manifests / modules without any changes on a local machine using Docker.

It leverages your user credentials via AWS Profile or via AWS Session Credentials.

It is limited to a single account / region as determined by your credentials and (optionally) a region you may pass in.  This does not change your manifests in any way, but does disregard the account / region definitions to go to only a single account / region.  All other configurations are used as if running on AWS CodeBuild.

## Prerequisites

1. Docker running and listening on `/var/run/docker.sock`
2. Active AWS credentials via AWS Profile or via AWS Session Credentials

## Usage

### Local Apply

To apply a deployment manifest locally, use the `--local` flag with the `apply` command:

```bash
seedfarmer apply <manifest-path> --local [options]
```

This will execute the deployment process using your local AWS credentials instead of assuming SeedFarmer roles. The deployment will target the account and region associated with your active  credentials.

#### Example

```bash
# Apply using default profile
seedfarmer apply manifests/dev-deployment.yaml --local

# Apply using a specific profile and region
seedfarmer apply manifests/dev-deployment.yaml --local --profile dev-profile --region us-west-2

# Apply with debug logging
seedfarmer apply manifests/dev-deployment.yaml --local --debug
```

### Local Destroy

To destroy a deployment locally, use the `--local` flag with the `destroy` command:

```bash
seedfarmer destroy <deployment-name> --local [options]
```

This will execute the destroy process using your local AWS credentials instead of assuming SeedFarmer roles.

#### Example

```bash
# Destroy a deployment using default profile
seedfarmer destroy my-deployment --local

# Destroy using a specific profile and region
seedfarmer destroy my-deployment --local --profile dev-profile --region us-west-2

# Destroy with debug logging
seedfarmer destroy my-deployment --local --debug
```

### Additional Options

When using the `--local` flag, you can still use most of the standard SeedFarmer options:

- `--profile`: Specify an AWS profile to use for credentials
- `--region`: Specify the AWS region to deploy to
- `--debug`: Enable detailed logging
- `--dry-run`: Simulate the deployment without making changes
- `--show-manifest`: Display the generated deployment manifest
- `--env-file`: Specify a .env file to load environment variables from

### Limitations

1. Local deployments are limited to a single AWS account and region.
2. The account and region definitions in your manifest files will be disregarded in favor of your local credentials.
3. Docker must be running and accessible at `/var/run/docker.sock`.
4. Using PYPI/NPM mirrors