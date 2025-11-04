# Integration Tests Module

**Category:** Testing  
**Module:** `testing/integration-tests`

## Description

This module creates infrastructure to run integration tests of various `seed-farmer` manifest(s) that are managed in a repository. Specifically, an AWS CodePipeline is provisioned that runs `seedfarmer apply` & `seedfarmer destroy` in sequence for any one or multiple manifests that are passed to the module. The pipeline is connected to a Github repository via an OAuth Token.

## Input Parameters

#### Required
- `manifest-paths`: Local paths within your github repo to desired manifest(s) to test. If specifying multiple please use comma-separated values. (e.g. `"manifests/this/deployment.yaml,manifests/that/deployment.yaml"`)
- `repo-owner`: Github Organization or Owner name of repository.
- `repo-name`: Github Repository Name.
- `oauth-token-secret-name`: Name of the SecretsManager secret that stores your github personal access token value.

## Outputs

- `IntegrationTestPipeline`: Integration testing pipeline name.
- `IntegrationTestAlertsTopic`: Name of SNS topic setup to receive Alerts from CodePipeline via CodeStar Notifiations.

## Source

[View on GitHub](https://github.com/awslabs/idf-modules/tree/main/modules/testing/integration-tests)
