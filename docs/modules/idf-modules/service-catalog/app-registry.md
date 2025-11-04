# AWS Service Catalog - App Regitsry resources

**Category:** Service-Catalog  
**Module:** `service-catalog/app-registry`

## Description

You can consider deploying this module, if you are working on creating an AWS Solution. One of the requirements for creating an AWS solution is being able to track the CloudFormation stacks using AWS Service catalog - AppRegistry resource.

This module:

- Creates an AppRegistry application resource
- It also joins the CloudFormation stacks created externally into the AppRegistry application using boto3

## Input Parameters

#### Required

- `solution-id`: The solution ID for the AWS Solution
- `solution-name`: The solution Name for the AWS Solution
- `solution-version`: The solution Version for the AWS Solution

The parameters `(solution-*)` will resolve a custom text that is used as a description of the stack.

## Outputs

- `AppRegistryName`: Service Catalog - AppRegistry name
- `AttributeGroupName`: Service Catalog - Attribute group name

## Source

[View on GitHub](https://github.com/awslabs/idf-modules/tree/main/modules/service-catalog/app-registry)
