# Module Development

To create a new module, there are certain requirements needed to allow the CLI (and AWS CodeSeedeer) to deploy your code.
## Required Files
Every module must have the following:
- [deployment manifest](deployment_manifest)
- [module manifest](module_manifest)
- [deployspec.yaml](deployspec)
- [README.md of module](module_readme)

## Optional Files
- [modulestack.yaml](modulestack)


## Create a new module



The [CLI](cli_commands.md) provides an `init` method to create your skeleton module code.  We will create a new module named `mymodule` in the group `mygroup`
```
> seedfarmer init module -g mygroup -m mymodule
> cd modules/mygroup/mymodule
```
The strucuture for your module is in place.  Edit the `deploysepc.yaml` as needed.  We provde a `modulestack.template` file that can be edited for additional permissions, and that file needs to be renamed to `modulestack.yaml` in order to be used.  

For a deep-dive on the module creation command, see [HERE](indepth_module_creation).

(deployspec)=
## Deployspec

Each Module must contain a `deployspec.yaml` file. This file defines deployment instructions read by seedfarmer. These instructions include the external module metadata required, libraries/utilities to be installed, and deployment commands. The deployspec.yaml is very similar to the AWS CodeBuild [buildspec.yaml](https://docs.aws.amazon.com/codebuild/latest/userguide/build-spec-ref.html) implementing the phases structure and adding a module_dependencies section for declaring other modules whose metadata should be made to the module on deployment.

### Structure
Below is a sample manifest that just 'echo' data to the environment runtime:

```yaml
deploy:
  phases:
    install:
      commands:
      - pip install -r requirements.txt
    pre_build:
      commands:
      - echo "Prebuild stage"
    build:
      commands:
      - echo "bash deploy.sh"
    post_build:
      commands:
      - echo "Deploy successful"
destroy:
  phases:
    install:
      commands:
      - pip install -r requirements.txt
    pre_build:
      commands:
      - echo "Prebuild stage"
      - echo "testing change"
    build:
      commands:
      - echo "DESTROY!"
    post_build:
      commands:
      - echo "Destroy successful"
build_type: BUILD_GENERAL1_LARGE
```

The deployspec is broken into 2 major areas of focus: `deploy `and `destroy`.  Each of these areas have 4 distinct phases in which commands can be executed (ex. installing supporting libraries, setting environment variables, etc.)  It is in these sections that AWS CodeSeeder makes calls to deploy/destroy on the modules' behalf.  The example below will highlight.

The parameter `build_type` allows module developers to choose the size of the compute instance AWS CodeSeeder will leverage as defined [HERE](https://docs.aws.amazon.com/codebuild/latest/userguide/build-env-ref-compute-types.html).  This parameter is defaulted to `BUILD_GENERAL1_SMALL`

The currently supported values are:
```
- BUILD_GENERAL1_SMALL
- BUILD_GENERAL1_MEDIUM
- BUILD_GENERAL1_LARGE 
- BUILD_GENERAL1_2XLARGE
```


#### Example
The following is an example deployspec that issues a series of commands.  This is only an example...

```yaml
deploy:
  phases:
    install:
      commands:
        - npm install -g aws-cdk@2.20.0
        - apt-get install jq
        - pip install -r requirements.txt
    build:
      commands:
        - aws iam create-service-linked-role --aws-service-name elasticmapreduce.amazonaws.com || true
        - export ECR_REPO_NAME=$(echo $MYAPP_PARAMETER_FARGATE | jq -r '."ecr-repository-name"')
        - aws ecr describe-repositories --repository-names ${ECR_REPO_NAME} || aws ecr create-repository --repository-name ${ECR_REPO_NAME}
        - export IMAGE_NAME=$(echo $MYAPP_PARAMETER_FARGATE | jq -r '."image-name"')
        - export COMMIT_HASH=$(echo $CODEBUILD_RESOLVED_SOURCE_VERSION | cut -c 1-7)
        - export IMAGE_TAG=${COMMIT_HASH:=latest}
        - export REPOSITORY_URI=$AWS_ACCOUNT_ID.dkr.ecr.$AWS_DEFAULT_REGION.amazonaws.com/$ECR_REPO_NAME
        - aws ecr get-login-password --region $AWS_DEFAULT_REGION | docker login --username AWS --password-stdin $AWS_ACCOUNT_ID.dkr.ecr.$AWS_DEFAULT_REGION.amazonaws.com
        - >
          echo "MYAPP_PARAMETER_SHARED_BUCKET_NAME: ${MYAPP_PARAMETER_SHARED_BUCKET_NAME}"
        - echo Building the Docker image...          
        - cd service/ && docker build -t $REPOSITORY_URI:latest .
        - docker tag $REPOSITORY_URI:latest $REPOSITORY_URI:$IMAGE_TAG
        - docker push $REPOSITORY_URI:latest && docker push $REPOSITORY_URI:$IMAGE_TAG
        - cd .. && cdk deploy --all --require-approval never --progress events --app "python app.py" --outputs-file ./cdk-exports.json
        - export MYAPP_MODULE_METADATA=$(python -c "import json; file=open('cdk-exports.json'); print(json.load(file)['myapp-${MYAPP_DEPLOYMENT_NAME}-${MYAPP_MODULE_NAME}']['metadata'])")
destroy:
  phases:
    install:
      commands:
      - npm install -g aws-cdk@2.20.0
      - pip install -r requirements.txt
    build:
      commands:
      - cdk destroy --all --force --app "python app.py"
build_type: BUILD_GENERAL1_LARGE
```

In the above example, a different CDKv2 version is being installed as an example, AWS CLI commands are issued, and the actual deployment script (AWS CDK) is executed with the output of the CDK being written to SSM as a JSON document so other modules can leverage it.

(module_readme)=
## Module ReadMe

As part of the process to promote reusability and sharabiltiy of the modules, each module is required to have a README.md that talks directly to end users and describes:

- the description of the module
- the inputs - parameter names
  - required
  - optional
- the outputs - the parameter names in JSON format
  - having a sample output is highly recommneded so other users cancan quickly reference in their modules


### Example 

Below is a sample of the sections in a README.md for the modules:

```
# OpenSearch Module


## Description

This module creates an OpenSearch cluster


## Inputs/Outputs

### Input Paramenters

#### Required

- `vpc-id`: The VPC-ID that the cluster will be created in

#### Optional
- `opensearch_data_nodes`: The number of data nodes, defaults to `1`
- `opensearch_data_nodes_instance_type`: The data node type, defaults to `r6g.large.search`
- `opensearch_master_nodes`: The number of master nodes, defaults to `0`
- `opensearch_master_nodes_instance_type`: The master node type, defaults to `r6g.large.search`
- `opensearch_ebs_volume_size`: The EBS volume size (in GB), defaults to `10`

### Module Metadata Outputs

- `OpenSearchDomainEndpoint`: the endpoint name of the OpenSearch Domain
  `OpenSearchDomainName`: the name of the OpenSearch Domain
- `OpenSeearchDashboardUrl`: URL of the OpenSearch cluster dashboard
- `OpenSearchSecurityGroupId`: name of the DDB table created for Rosbag Scene Data

#### Output Example

```json
{
  "OpenSearchDashboardUrl": "https://vpc-myapp-test-core-opensearch-aaa.us-east-1.es.amazonaws.com/_dashboards/",
  "OpenSearchDomainName": "vpc-myapp-test-core-opensearch-aaa",
  "OpenSearchDomainEndpoint": "vpc-myapp-test-core-opensearch-aaa.us-east-1.es.amazonaws.com",
  "OpenSearchSecurityGroupId": "sg-0475c9e7efba05c0d"
}

```

(modulestack)=
## ModuleStack

The modulestack (`modulestack.yaml`) is an optional AWS Cloudformation file that contains the granular permissions that AWS Codeseeder will need to deploy your module.  It is recommended to use a least-privelege policy to promote security best practices.

By default, the CLI uses AWS CDKv2, which assumes a role that has the permissions to deploy via CloudFormation and is the recommended practice.  You have the ability to use the `modulestack.yaml` to give additial permissions to `AWS CodeSeeder` on your behalf.  

Typical cases when you would use a  `modulestack.yaml`:
- any time you are invoking AWS CLI in the deployspec (not in the scope of the CDK) - for example: copying files to S3
- you perfer to use the AWSCLI v1 - in which a least-privilege policy is necessary for ALL AWS Services.


### Initial Template

Below is a sample template that is provoded by the [CLI](cli_commands.md).  The `Parameters` section is populated with the input provided from the CLI when deploying.  

*** It DOES have a policy definiton that is wide open - you SHOULD CHANGE THIS - it is only a template!

```yaml
AWSTemplateFormatVersion: 2010-09-09
Description: This template deploys a Module specific IAM permissions

Parameters:
  DeploymentName:
    Type: String
    Description: The name of the deployment
  ModuleName:
    Type: String
    Description: The name of the Module
  RoleName:
    Type: String
    Description: The name of the IAM Role

Resources:
  Policy:
    Type: 'AWS::IAM::Policy'
    Properties:
      PolicyDocument:
        Statement:
          - Effect: Allow
            Action: '*'
            Resource: '*'
        Version: 2012-10-17
      PolicyName: "myapp-modulespecific-policy"
      Roles: [!Ref RoleName]
```
### Parameters
As mentioned above, we strongly recommend a least-priviledge policy to promote security best practices. The `modulestack.yaml` automatically has access to the parameters that were defined in your manifest file. Those passed parameters can help make your policy more explicit by using parameter names to limit permissions to a resource.

Below is an example of how to make use of this functionality.

Lets say we want to deploy the Cloud9 module. This module, on top of deploying a Cloud9 instance, also executes a few boto3 calls after the CDK deploys the Cloud9 environment. This example will focus on the boto3 call that modifies the volume of the instance. So we need to give permission to execute that boto3 call and we also want to restrict which instance to modify

Suppose this is our manifest. We want our modulestack.yaml to limit modification to our instance named `cloud9-ml-project-dev`
```
name: workbench
path: modules/workbench/cloud9/
parameters:
  ...
  - name: instance_type
    value: t3.micro
  - name: instance_name
    value: cloud9-ml-project-dev
  ...
```

The parameter names in your module manifest are resolved in `CamelCase` in the modulestack.yaml file. The `instance_name` parameter will resolve to `InstanceName`. Back in our modulestack.yaml, under `Parameters`, the manifest parameter `instance_name` is added as `InstanceName`. Now we can add a policy that will allow modification of volume of our specific instance by referencing the parameter we specified

```
...
Parameters:
  InstanceName:
    Type: String
    Description: The name of the Cloud9 instance

Resources:
  Policy:
    Type: "AWS::IAM::Policy"
    Properties:
      PolicyDocument:
        Statement:
          - Effect: Allow
            Action:
              - "ec2:ModifyVolume"
            Resource: "*"
            Condition:
              StringLike:
                ec2:ResourceTag/Name: !Sub 'aws-cloud9-${InstanceName}-*'
          ...
```
Side note, the `aws-cloud9-` prefix is added by the Cloud9 deployment automatically

## Add the Manifests
Create a new module manifest (see [manifests](module_manifest)) and place it in the `manifests/` directory, under a logical directory.  If the `deployment.yaml` manifest does not exist, create it also.  Add your `module manifest` to the `deployment manifest`.
