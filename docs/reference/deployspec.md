---
title: Deployspec
---

The `deployspec.yaml` file is the **execution blueprint** for your module. It defines exactly how your infrastructure code gets deployed and destroyed within AWS CodeBuild. Think of it as the "recipe" that tells Seed-Farmer how to cook your infrastructure.

## What the Deployspec Does

The deployspec serves as the **bridge between your infrastructure code and AWS CodeBuild**. It answers these critical questions:

- **How should the build environment be prepared?** (Installing dependencies, setting up tools)
- **What commands should run to deploy your infrastructure?** (CDK deploy, CloudFormation, Terraform, etc.)
- **What commands should run to destroy your infrastructure?** (Cleanup procedures)
- **What metadata should be exported for other modules to use?** (Outputs and references)

### Key Responsibilities

1. **Environment Setup**: Installs required tools, libraries, and dependencies
2. **Deployment Execution**: Runs the actual infrastructure deployment commands
3. **Metadata Management**: Exports outputs that other modules can reference
4. **Cleanup Operations**: Handles proper resource destruction
5. **Error Handling**: Manages deployment failures and rollbacks

## Structure and Phases

The deployspec is organized into two main sections (`deploy` and `destroy`), each with four distinct phases:

```yaml
deploy:
  phases:
    install:      # Install dependencies and tools
      commands:
        - npm install -g aws-cdk@2.100.0
        - pip install -r requirements.txt
    pre_build:    # Pre-deployment setup
      commands:
        - echo "Preparing deployment environment"
    build:        # Main deployment logic
      commands:
        - cdk deploy --require-approval never --progress events --app "python app.py" --outputs-file ./cdk-exports.json
        - echo "Deployment completed successfully"
    post_build:   # Post-deployment tasks
      commands:
        - echo "Exporting module metadata"
        - seedfarmer metadata convert -f cdk-exports.json

destroy:
  phases:
    install:      # Install dependencies for destruction
      commands:
        - npm install -g aws-cdk@2.100.0
        - pip install -r requirements.txt
    pre_build:    # Pre-destruction setup
      commands:
        - echo "Preparing for resource cleanup"
    build:        # Main destruction logic
      commands:
        - cdk destroy --force --app "python app.py"
        - echo "Resources destroyed successfully"
    post_build:   # Post-destruction cleanup
      commands:
        - echo "Cleanup completed"

# Configuration options
build_type: BUILD_GENERAL1_MEDIUM
publishGenericEnvVariables: false
```

### Phase Execution Order

1. **install**: Set up the build environment with required tools and dependencies
2. **pre_build**: Perform any setup tasks before the main deployment/destruction
3. **build**: Execute the primary deployment or destruction commands
4. **post_build**: Handle post-deployment tasks like metadata export or cleanup

## Environment Variables and Parameters

### How Parameters Become Environment Variables

This is **critically important** for module development: Seed-Farmer automatically converts all parameters from your module manifest into environment variables that are available in your deployspec execution.

### Parameter Naming Convention

The naming convention depends on whether your module is **project-specific** or **generic**:

#### Generic Modules (Default Behavior)

When `publishGenericEnvVariables` is `true` (the default), parameters use the generic `SEEDFARMER_PARAMETER_` prefix:

```yaml
# In your module manifest
parameters:
  - name: vpc-id
    value: vpc-12345678
  - name: instance-type
    value: t3.medium
  - name: database-name
    value: myapp-prod-db
```

**Available in deployspec as**:

```bash
SEEDFARMER_PARAMETER_VPC_ID=vpc-12345678
SEEDFARMER_PARAMETER_INSTANCE_TYPE=t3.medium
SEEDFARMER_PARAMETER_DATABASE_NAME=myapp-prod-db
```

### Parameter Name Transformation Rules

Seed-Farmer converts parameter names to environment variables using these transformation rules:

| Parameter Name Style | Example Parameter | Environment Variable (Generic) |
|---------------------|-------------------|--------------------------------|
| kebab-case          | `vpc-id`          | `SEEDFARMER_PARAMETER_VPC_ID`  |
| camelCase           | `vpcId`           | `SEEDFARMER_PARAMETER_VPC_ID`  |
| PascalCase          | `VpcId`           | `SEEDFARMER_PARAMETER_VPC_ID`  |
| snake_case          | `vpc_id`          | `SEEDFARMER_PARAMETER_VPC_ID`  |
| Mixed styles        | `some-Complex_Name` | `SEEDFARMER_PARAMETER_SOME_COMPLEX_NAME` |

**Key Points**:

- All parameter names are converted to **UPPER_SNAKE_CASE**
- Hyphens (`-`), underscores (`_`), and camelCase boundaries become underscores
- Generic modules use the `SEEDFARMER_PARAMETER_` prefix
- This makes modules reusable across different projects

### System Environment Variables

Seed-Farmer also provides system-level information as environment variables within the deploy process:

```bash
SEEDFARMER_PROJECT_NAME=myapp
SEEDFARMER_DEPLOYMENT_NAME=production
SEEDFARMER_MODULE_NAME=vpc-network
SEEDFARMER_GROUP_NAME=networking
AWS_ACCOUNT_ID=123456789012
AWS_DEFAULT_REGION=us-east-1
```

## Using Parameters in Your Deployspec

### Basic Parameter Usage

```yaml
deploy:
  phases:
    build:
      commands:
        # Reference parameters directly
        - echo "Deploying VPC: $SEEDFARMER_PARAMETER_VPC_ID"
        - echo "Instance type: $SEEDFARMER_PARAMETER_INSTANCE_TYPE"
        
        - cdk deploy --require-approval never --progress events --app "python app.py" --outputs-file ./cdk-exports.json
        
        # Use in CloudFormation
        - aws cloudformation deploy \
            --template-file template.yaml \
            --stack-name my-stack \
            --parameter-overrides \
              VpcId=$SEEDFARMER_PARAMETER_VPC_ID \
              InstanceType=$SEEDFARMER_PARAMETER_INSTANCE_TYPE
```

### Working with JSON Parameters

When parameters contain JSON data, you can parse them using `jq`:

```yaml
deploy:
  phases:
    build:
      commands:
        # Parse JSON parameter
        - export DB_HOST=$(echo $SEEDFARMER_PARAMETER_DATABASE_CONFIG | jq -r '.host')
        - export DB_PORT=$(echo $SEEDFARMER_PARAMETER_DATABASE_CONFIG | jq -r '.port')
        
        # Use parsed values
        - echo "Connecting to database at $DB_HOST:$DB_PORT"
```

## Configuration Options

### Build Type

Control the compute resources for your CodeBuild environment:

```yaml
build_type: BUILD_GENERAL1_LARGE
```

**Available options**:

- `BUILD_GENERAL1_SMALL`: 3 GB memory, 2 vCPUs
- `BUILD_GENERAL1_MEDIUM`: 7 GB memory, 4 vCPUs  
- `BUILD_GENERAL1_LARGE`: 15 GB memory, 8 vCPUs
- `BUILD_GENERAL1_2XLARGE`: 145 GB memory, 72 vCPUs

### Generic Modules

```yaml
# For generic modules (default and recommended)
publishGenericEnvVariables: true
```

Generic modules are the recommended approach as they:

- Create reusable infrastructure components
- Work across different projects without modification
- Use the `SEEDFARMER_PARAMETER_*` naming convention
- Promote modularity and code reuse

## Metadata Management

### How Module Metadata Works

Seed-Farmer uses a metadata system that allows modules to export outputs that other modules can reference as inputs. This creates a dependency chain where modules can consume outputs from previously deployed modules.

#### The Metadata File System

When your deployspec runs, Seed-Farmer automatically creates a metadata file that your module writes to.

**For Generic Modules (Default)**:

- Environment variable: `SEEDFARMER_MODULE_METADATA`
- File location: `module/SEEDFARMER_MODULE_METADATA`

#### How to Export Module Outputs

There are several ways to export metadata from your module:

### Method 1: Using Seed-Farmer Metadata CLI Commands (Recommended)

The [seedfarmer metadata](./cli-commands.md#metadata) commands automatically handle the metadata file creation and management:

```yaml
deploy:
  phases:
    build:
      commands:
        # Use parameters in complex commands
        - cdk deploy --require-approval never --progress events --app "python app.py" --outputs-file ./cdk-exports.json
        - seedfarmer metadata convert -f cdk-exports.json 
        - seedfarmer metadata add -k VpcId -v vpc-12345678
        - seedfarmer metadata add -k DatabaseEndpoint -v data.cluster-xyz.us-east-1.rds.amazonaws.com
```

### Method 2: Direct Environment Variable Export

You can also export metadata directly by setting the metadata environment variable:

```yaml
deploy:
  phases:
    post_build:
      commands:
        # For generic modules
        - export SEEDFARMER_MODULE_METADATA='{"VpcId": "vpc-12345678", "SubnetIds": ["subnet-123", "subnet-456"]}'
 
```

!!! warning "Use with caution"
    Seed-Farmer provides commands to automate the addition of data to the output and it is recommended to use them.  

#### CDK Output Structure for Metadata

When using CDK, your stack must export a `metadata` output with a specific structure. The `seedfarmer metadata convert` command expects the CDK outputs file to contain a key matching your module's deployment name, with a nested `metadata` field.

Here's the correct pattern:

```python
# In your CDK stack
from aws_cdk import CfnOutput, Stack

class MyStack(Stack):
    def __init__(self, scope, construct_id, **kwargs):
        super().__init__(scope, construct_id, **kwargs)
        
        # ... your infrastructure code ...
        
        # Export metadata as a CDK output - this creates the required structure
        CfnOutput(
            scope=self,
            id="metadata",
            value=Stack.to_json_string(
                self,
                {
                    "VpcId": self.vpc.vpc_id,
                    "SecurityGroupId": self.security_group.security_group_id,
                    "PublicSubnetIds": self.public_subnets.subnet_ids,
                    "PrivateSubnetIds": self.private_subnets.subnet_ids,
                    "IsolatedSubnetIds": self.isolated_subnets.subnet_ids if not self.internet_accessible else [],
                    "LocalZonePrivateSubnetIds": [s.subnet_id for s in self.local_zone_private_subnets] 
                        if hasattr(self, "local_zone_private_subnets") else [],
                    "LocalZonePublicSubnetIds": [s.subnet_id for s in self.local_zone_public_subnets] 
                        if hasattr(self, "local_zone_public_subnets") else [],
                }
            ),
        )
```

**Expected CDK Output File Structure:**

The `seedfarmer metadata convert` command expects the CDK outputs file to have this structure:

```json
{
  "project-deployment-module": {
    "metadata": "{\"VpcId\": \"vpc-12345678\", \"SecurityGroupId\": \"sg-87654321\", \"PublicSubnetIds\": [\"subnet-123\", \"subnet-456\"], \"PrivateSubnetIds\": [\"subnet-789\", \"subnet-012\"]}"
  }
}
```

**Critical Requirements:**

- `project-deployment-module` is the full module deployment name (format: `{project}-{deployment}-{module}`)
- The `metadata` field must contain a **JSON string** (not a JSON object)
- The JSON string contains your actual metadata values as a serialized JSON object

### Important Metadata Guidelines

#### 1. Metadata Must Be JSON

All metadata must be valid JSON. Seed-Farmer stores and retrieves metadata as JSON objects:

```yaml
# ✅ Good - Valid JSON
- seedfarmer metadata add -j '{"VpcId": "vpc-123", "SubnetCount": 4}'

# ❌ Bad - Invalid JSON (single quotes, unquoted keys)
- seedfarmer metadata add -j "{VpcId: 'vpc-123', SubnetCount: 4}"
```

#### 2. Use Consistent Naming Conventions

Use consistent, descriptive names for your metadata keys:

```yaml
# ✅ Good - Clear, consistent naming
- seedfarmer metadata add -k VpcId -v vpc-12345678
- seedfarmer metadata add -k DatabaseEndpoint -v data.cluster-xyz.us-east-1.rds.amazonaws.com
- seedfarmer metadata add -k SubnetIds -v '["subnet-123", "subnet-456"]'

# ❌ Bad - Inconsistent, unclear naming
- seedfarmer metadata add -k vpc -v vpc-12345678
- seedfarmer metadata add -k db_endpoint -v data.cluster-xyz.us-east-1.rds.amazonaws.com
- seedfarmer metadata add -k subnets -v '["subnet-123", "subnet-456"]'
```

#### 3. Document Your Metadata Outputs

Always document what metadata your module exports in your README.md:

```markdown
### Module Metadata Outputs

- `VpcId`: The ID of the created VPC
- `DatabaseEndpoint`: The RDS cluster endpoint URL
- `SubnetIds`: Array of subnet IDs created in the VPC
- `SecurityGroupId`: The ID of the default security group

#### Output Example

```json
{
  "VpcId": "vpc-12345678",
  "DatabaseEndpoint": "data.cluster-xyz.us-east-1.rds.amazonaws.com",
  "SubnetIds": ["subnet-123", "subnet-456"],
  "SecurityGroupId": "sg-789"
}
```

### Complete Metadata Export Examples

#### CDK Module with Automatic Conversion

```yaml
deploy:
  phases:
    build:
      commands:
        - cdk deploy --require-approval never --progress events --app "python app.py" --outputs-file ./cdk-exports.json
    post_build:
      commands:
        # Automatically convert CDK outputs
        - seedfarmer metadata convert
        
        # Add additional custom metadata
        - seedfarmer metadata add -k DeploymentTimestamp -v $(date -u +"%Y-%m-%dT%H:%M:%SZ")
        - seedfarmer metadata add -k ModuleVersion -v "1.2.3"
```

#### Terraform Module with Manual Export

```yaml
deploy:
  phases:
    build:
      commands:
        - terraform apply -auto-approve
        - terraform output -json > terraform-outputs.json
    post_build:
      commands:
        # Extract Terraform outputs and add to metadata
        - VPC_ID=$(terraform output -raw vpc_id)
        - DB_ENDPOINT=$(terraform output -raw database_endpoint)
        - SUBNET_IDS=$(terraform output -json subnet_ids)
        
        - seedfarmer metadata add -k VpcId -v $VPC_ID
        - seedfarmer metadata add -k DatabaseEndpoint -v $DB_ENDPOINT
        - seedfarmer metadata add -k SubnetIds -v "$SUBNET_IDS"
```

#### CloudFormation Module with Stack Outputs

```yaml
deploy:
  phases:
    build:
      commands:
        - aws cloudformation deploy --template-file template.yaml --stack-name $STACK_NAME
    post_build:
      commands:
        # Get CloudFormation stack outputs
        - |
          aws cloudformation describe-stacks --stack-name $STACK_NAME \
            --query 'Stacks[0].Outputs' --output json > cfn-outputs.json
        
        # Convert to metadata format
        - VPC_ID=$(jq -r '.[] | select(.OutputKey=="VpcId") | .OutputValue' cfn-outputs.json)
        - DB_ENDPOINT=$(jq -r '.[] | select(.OutputKey=="DatabaseEndpoint") | .OutputValue' cfn-outputs.json)
        
        - seedfarmer metadata add -k VpcId -v $VPC_ID
        - seedfarmer metadata add -k DatabaseEndpoint -v $DB_ENDPOINT
```

### Troubleshooting Metadata Issues

#### Common Problems and Solutions

1. **Metadata not appearing in dependent modules**
    - Ensure you're exporting metadata in the `build` or `post_build` phase
    - Verify the metadata is valid JSON
    - Check that the cdk output file is correct

2. **CDK convert command not working**
    - Ensure your CDK outputs file contains the expected structure
    - Use `seedfarmer metadata depmod` to get the correct module key
    - Try using the `-jq` option to specify the exact path to your data

3. **JSON parsing errors**
    - Validate your JSON using `jq` or online JSON validators
    - Escape quotes properly in shell commands  
    - Use single quotes around JSON strings in YAML

## Complete Examples

### CDK-Based Module

```yaml
deploy:
  phases:
    install:
      commands:
        - npm install -g aws-cdk@2.100.0
        - pip install -r requirements.txt
    pre_build:
      commands:
        - echo "Starting CDK deployment"
        - echo "VPC ID: $SEEDFARMER_PARAMETER_VPC_ID"
        - echo "Environment: $SEEDFARMER_PARAMETER_ENVIRONMENT"
    build:
      commands:
        - cdk deploy --require-approval never --progress events --app "python app.py" --outputs-file ./cdk-exports.json
        - echo "CDK deployment completed"
    post_build:
      commands:
        - seedfarmer metadata convert
        - echo "Metadata exported successfully"

destroy:
  phases:
    install:
      commands:
        - npm install -g aws-cdk@2.100.0
        - pip install -r requirements.txt
    build:
      commands:
        - cdk destroy --all --force

build_type: BUILD_GENERAL1_MEDIUM
publishGenericEnvVariables: true
```

### Terraform Module

```yaml
publishGenericEnvVariables: true
deploy:
  phases:
    install:
      commands:
        - TERRAFORM_VERSION=1.13.3
        - wget -q https://releases.hashicorp.com/terraform/"$TERRAFORM_VERSION"/terraform_"$TERRAFORM_VERSION"_linux_amd64.zip
        - unzip terraform_"$TERRAFORM_VERSION"_linux_amd64.zip
        - mv terraform /usr/local/bin/
    build:
      commands:
        - > 
          terraform init -backend-config="bucket=${SEEDFARMER_PARAMETER_TFSTATE_BUCKET_NAME}" 
          -backend-config="key=opensearch-serverless-module/terraform.tfstate" 
          -backend-config="region=${AWS_DEFAULT_REGION}"
        - >
          terraform plan -input=false -out tf.plan
          -var="collection_name=$SEEDFARMER_PARAMETER_COLLECTION_NAME"
          -var="s3_bucket_prefix=$SEEDFARMER_PARAMETER_S3_BUCKET_PREFIX"
        - >
          terraform apply -auto-approve
          -var="collection_name=$SEEDFARMER_PARAMETER_COLLECTION_NAME"
          -var="s3_bucket_prefix=$SEEDFARMER_PARAMETER_S3_BUCKET_PREFIX"
        - terraform output -json > tf-exports.json
        - seedfarmer metadata add -k collection_arn -v $(terraform output -raw collection_arn)
        - seedfarmer metadata add -k collection_name -v $(terraform output -raw collection_name)
        - seedfarmer metadata add -k s3_bucket_arn -v $(terraform output -raw s3_bucket_arn)
    post_build:
      commands:
        - echo "OpenSearch Serverless module deployment successful"
destroy:
  phases:
    install:
      commands:
        - TERRAFORM_VERSION=1.13.3
        - wget -q https://releases.hashicorp.com/terraform/"$TERRAFORM_VERSION"/terraform_"$TERRAFORM_VERSION"_linux_amd64.zip
        - unzip terraform_"$TERRAFORM_VERSION"_linux_amd64.zip
        - mv terraform /usr/local/bin/
    build:
      commands:
        - > 
          terraform init -backend-config="bucket=${SEEDFARMER_PARAMETER_TFSTATE_BUCKET_NAME}" 
          -backend-config="key=opensearch-serverless-module/terraform.tfstate" 
          -backend-config="region=${AWS_DEFAULT_REGION}"
        - terraform destroy -auto-approve
    post_build:
      commands:
        - echo "OpenSearch Serverless module destruction successful"
build_type: BUILD_GENERAL1_MEDIUM

```

### CloudFormation Module

```yaml
deploy:
  phases:
    pre_build:
      commands:
        - echo "Deploying CloudFormation stack"
        - echo "Stack name: $SEEDFARMER_PARAMETER_STACK_NAME"
    build:
      commands:
        - |
          aws cloudformation deploy \
            --template-file template.yaml \
            --stack-name $SEEDFARMER_PARAMETER_STACK_NAME \
            --parameter-overrides \
              VpcId=$SEEDFARMER_PARAMETER_VPC_ID \
              InstanceType=$SEEDFARMER_PARAMETER_INSTANCE_TYPE \
            --capabilities CAPABILITY_IAM
        
        # Export stack outputs
        - |
          aws cloudformation describe-stacks \
            --stack-name $SEEDFARMER_PARAMETER_STACK_NAME \
            --query 'Stacks[0].Outputs' > cfn-outputs.json
    post_build:
      commands:
        - |
          # Convert CloudFormation outputs to metadata
          OUTPUTS=$(jq -r 'map({(.OutputKey): .OutputValue}) | add' cfn-outputs.json)
          seedfarmer metadata add -j "$OUTPUTS"

destroy:
  phases:
    build:
      commands:
        - aws cloudformation delete-stack --stack-name $SEEDFARMER_PARAMETER_STACK_NAME
        - |
          aws cloudformation wait stack-delete-complete \
            --stack-name $SEEDFARMER_PARAMETER_STACK_NAME

build_type: BUILD_GENERAL1_SMALL
publishGenericEnvVariables: true
```

## Best Practices

### Parameter Handling

1. **Always validate required parameters** in the `pre_build` phase
2. **Use descriptive parameter names** that clearly indicate their purpose
3. **Handle JSON parameters carefully** using `jq` for parsing
4. **Set default values** when appropriate to make modules more flexible
5. **Document parameter requirements** in your module's README

### Metadata Export

1. **Use consistent naming conventions** for exported metadata
2. **Include both simple values and complex objects** as needed
3. **Document exported metadata** in your module's README

### Security Considerations

1. **Never log sensitive parameters** like passwords or API keys
2. **Use AWS Secrets Manager** for sensitive configuration
3. **Validate input parameters** to prevent injection attacks
4. **Use least-privilege IAM roles** in your modulestack.yaml
5. **Sanitize user inputs** before using them in commands
