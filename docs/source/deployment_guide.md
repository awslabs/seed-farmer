# Deployment Guide

Seedfarmer follows the Industry standard `GitOps` model. The project is entirely driven by `Descriptive` prinicples in the form of asking inputs from a module developer via manifest file(s).

## Steps to deployment

#### Create a Virtual environment using:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

####  Install the requirements

```bash
pip install seed-farmer.
```

#### Create a mew project
The following command will create the skeleton of your project
```bash
seedfarmer init project -n myapp
```

Note that a file called `seedfarmer.yaml` has been created. That contains basic configuration that seedfarmer will use. For example, the file contains a key `project` that will prefex resource names upon creation


#### Setting the region
Seedfarmer submits build information to AWS CodeBuild via AWS CodeSeeder.  The initial submittal is done via AWS CLI, leveraging the configured active AWS profile.  If you would like to deploy your project to a region other than the region configured for the profile, you can explicitly set the region via:

```bash
export AWS_DEFAULT_REGION=<region-name>   (ex. us-east-1, eu-central-1)
```
Please see [HERE for details](https://docs.aws.amazon.com/cli/latest/userguide/cli-configure-envvars.html)

#### Bootstrap the CDK
We use AWS CDK V2 as the standard CDK as it is compatible with V1.  But, you need to bootstrap it (one time per region) with V2 - see [HERE](https://docs.aws.amazon.com/cdk/v2/guide/bootstrapping.html).
```bash
cdk bootstrap aws://<account>/<region>
```


#### Prep the AWS SecretsManager
As part of this example deployment (`example-dev`), there are modules that leverage credentials for access.  We store these credentials in AWS SecretsManager.  We have provided a bash script to populate AWS SecretsManager with default values for those modules that need them located in at `scripts/setup-secrets-example.sh`.  
Run the bash script from commandline with the following:
```bash
source scripts/setup-secrets-example.sh
```
> NOTE the above script uses `jq`.  Please install it via [these instructions](https://stedolan.github.io/jq/download/).
#### Verify the Manifests for Deployment
Move to the `manifests` directory using the below command, where you will locate sample manifests in the name of `example-dev` and `example-prod`. You should create a directory with your desired deployment names like `uat`, `demo` etc.

```bash
cd manifests/
```

### Deployment WalkThrough

For the below walkthrough, let us move into the `example-dev` directory using the below command, where the deploymemt name is set to `example-dev`:

```bash
cd example-dev/
```

File `deployment.yaml` is the top level manifest, which should include the modules you wanted to deploy, grouped under logical containers called `group`.  Please see [manifests](manifests.md) for more details.

> Note:
> All paths inside the manifest files should be relative to the root of the project. For ex: if you want to include a module manifest `example-modules.yaml` in your deplopyment.yaml, you should declare the path as `manifests/example-dev/example-modules.yaml`

#### Dockerhub Support

To avoid throttling from `DockerHub` when building images, you should create a parameter/re-use an existing parameter in `AWS Secrets Manager` to store your DockerHub username and password. 

To create/update the default secret (aws-myapp-docker-credentials) run:

```bash
./scripts/setup-secrets-dockerhub.sh
```

> Note:
> For additional info on setting up the secret manually see [manifests](manifests.md) guide for details.
> The `examples-dev` modules DO leverage DockerHub, so you should populate the SecretsManager as indicated in [manifests](manifests.md).

For the walkthrough, we have few manifests declared within `example-dev` directory which installs the following modules in sequence. If you do not wish to know what modules the demo deployment is doing, you can skip reading this section:
  * `Group` name is set to `optionals` to install the following, sourcing from the manifest `manifests/example-dev/optional-modules.yaml`:
    * Creates a `networking` module (creates vpc, 2 Public/Private subnets, IGW, NAT, Gateway endpoints etc)
    * Creates a `datalake-buckets` module (creates shared buckets for datalake, logging and artifacts etc)
  * `Group` name is set to `core` to install the following, sourcing from the manifest `manifests/example-dev/core-modules.yaml`:
    * Creates `eks` module (creates AWS EKS Compute environment with standard plugins installed)
    * Creates `mwaa` module(creates AWS Managed Airflow cluster for orchestration of dags)
    * Creates `metadata-storgae` module(creates shared AWS DynamoDB and AWS Glue databases)
    * Creates `opensearch` module (creates AWS Managed Opensearch for ingesting app/infra logs)
  * `Group` name is set to `examples` to install the following, sourcing from the manifest `manifests/example-dev/example-modules.yaml`:
    * Creates `example-dags` module (Demos an example on how to deploy dags from target modules using the shared mwaa module)
  * `Group` name is set to `blogs` to install the following, sourcing from the manifest `manifests/example-dev/blogs.yaml`:
    * Creates `rosbag-scene-detection` module
    > Note: This was previously named as `module1`
    * Creates `rosbag-visualization` module
    > Note: This was previously named as `module5`
  * `Group` name is set to `integration` to install the following, sourcing from the manifest `manifests/example-dev/integration-modules.yaml`:
    * Creates `rosbag-scene-detection` module

#### Deploy
Use the [CLI](cli_commands.md) to deploy.
Below is the command to deploy the modules using the main manifest `deployment.yaml`:

```bash
seedfarmer apply manifests/example-dev/deployment.yaml
```



#### Destroy
Below is the command to destroy all the modules related to a deployment:

```bash
seedfarmer destroy <<DEPLOYMENT_NAME>>
```

> Note:
> Replace the `DEPLOYMENT_NAME` with the desired deployment name of your environment. For ex: `example-dev`
> You can pass an optional `--debug` flag to the above command for getting debug level output

### FAQS

