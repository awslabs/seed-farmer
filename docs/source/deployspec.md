## Deployspec

Each Module must contain a deployspec.yaml file. This file defines deployment instructions read by seedfarmer. These instructions include the external module metadata required, libraries/utilities to be installed, and deployment commands. The deployspec.yaml is very similar to the AWS CodeBuild [buildspec.yaml](https://docs.aws.amazon.com/codebuild/latest/userguide/build-spec-ref.html) implementing the phases structure and adding a module_dependencies section for declaring other modules whose metadata should be made to the module on deployment.

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


### Example
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