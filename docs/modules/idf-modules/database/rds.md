# RDS Instance Module

**Category:** Database  
**Module:** `database/rds`

## Description

This module will create a RDS database instance tied to the provided VPC.
The password for the database admin will be automatically generated and stored in SecretsManager.
The module can also set up SecretsManager to automatically rotate the credentials.

## Outputs

- `CredentialsSecretArn`: ARN of the secret
- `DatabaseHostname`: Database hostname
- `DatabasePort`: Database port
- `SecurityGroupId`: ID of the database security group

## Source

[View on GitHub](https://github.com/awslabs/idf-modules/tree/main/modules/database/rds)
