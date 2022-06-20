## ModuleStack

The modulestack (`modulestack.yaml`) is an optional AWS Cloudformation file that contains the granular permissions that AWS Codeseeder will need to deploy your module.  It is recommended to use a least-privelege policy to promote security best practices.

By default, the CLI uses AWS CDKv2, which assumes a role that has the permissions to deploy via CloudFormation and is the recommended practice.  You have the ability to use the `modulestack.yaml` to give additial permissions to `AWS CodeSeeder` on your behalf.  

Typical cases when you would use a  `modulestack.yaml`:
- any time you are invoking AWS CLI in the deployspec (not in the scope of the CDK) - for example: copying files to S3
- you perfer to use the AWSCLI v1 - in which a least-privilege policy is necessary for ALL AWS Services.


#### Initial Template

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