# Networking Module

**Category:** Network  
**Module:** `network/basic-cdk`

## Description

This module creates the below AWS netowrking resources. It may not be required if an end-user already has networking setup in their AWS account(s).

Networking resources are:

  - VPC
  - Public/Private/Isolated Subnets as per the use-case
  - LocalZones
  - Interface/Gateway Endpoints

## Outputs

- `VpcId`: The VPC ID created
- `SecurityGroupId`: The Security Group ID created
- `PublicSubnetIds`: An array of the public subnets
- `PrivateSubnetIds`: An array of the private subnets
- `IsolatedSubnetIds`: An array of the isolated subnets  (only if `internet-accessible` is `false`)
- `LocalZonePrivateSubnetIds`: An array of the LocalZone Private subnets
- `LocalZonePublicSubnetIds`: An array of the LocalZone Public subnets

## Source

[View on GitHub](https://github.com/awslabs/idf-modules/tree/main/modules/network/basic-cdk)
