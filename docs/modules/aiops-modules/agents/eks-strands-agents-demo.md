# Introduction

**Category:** Agents  
**Module:** `agents/eks-strands-agents-demo`

## Description

This module runs a demo [Strands](https://strandsagents.com/latest/) Weather Agent on [Amazon EKS Auto Mode](https://aws.amazon.com/eks/auto-mode/).

The module will:
1. Provision an Amazon EKS Auto Mode Cluster
2. Build Weather Agent Docker image and push into Amazon ECR repository
3. Create and associate Amazon EKS service account permissions to an IAM Role with Amazon Bedrock access
4. Deploy Weather Agent to Amazon EKS using a Helm chart

## Source

[View on GitHub](https://github.com/awslabs/aiops-modules/tree/main/modules/agents/eks-strands-agents-demo)
