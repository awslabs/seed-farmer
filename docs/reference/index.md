# Reference

This section provides detailed reference documentation for Seed-Farmer, including CLI commands, manifest formats, and module development guidelines.

## CLI Commands

The [CLI Commands](cli-commands.md) page provides a comprehensive reference for all Seed-Farmer CLI commands, including their options and usage examples.

## Manifests

The [Manifests](manifests.md) page explains the format and structure of Seed-Farmer manifests, including deployment manifests and module manifests.

## Module Development

The [Module Development](../guides/module-development.md) page provides detailed information on developing modules for Seed-Farmer, including required files, deployspec format, and best practices.

## FAQ

The [FAQ](faq.md) page answers common questions about Seed-Farmer and provides solutions to common problems.

## API Reference

### Environment Variables

Seed-Farmer sets the following environment variables in the CodeBuild environment for modules:

- `<PROJECT>_DEPLOYMENT_NAME`: The name of the deployment
- `<PROJECT>_MODULE_NAME`: The name of the module
- `<PROJECT>_MODULE_GROUP`: The name of the group containing the module
- `<PROJECT>_PARAMETER_<NAME>`: Parameters passed to the module

For generic modules (with `publishGenericEnvVariables: true` in the deployspec), these variables are prefixed with `SEEDFARMER_` instead of the project name.

### Metadata CLI Helper Commands

Seed-Farmer provides special commands for managing and manipulating metadata in module deployments:

- `seedfarmer metadata add`: Add output key-value pairs to the metadata
- `seedfarmer metadata convert`: Convert CDK output to Seed-Farmer metadata
- `seedfarmer metadata depmod`: Get the full name of the module
- `seedfarmer metadata paramvalue`: Get the parameter value based on the suffix

These commands can only be run from the `deployspec.yaml`.

## Best Practices

### Security

- Use least-privilege IAM roles and permissions boundaries
- Store sensitive information in AWS Secrets Manager
- Use the `modulestack.yaml` to define granular permissions for modules

### Performance

- Group modules that can be deployed concurrently
- Use the appropriate build type for your modules
- Optimize your deployspec commands for faster execution

### Maintainability

- Use consistent naming conventions for modules and parameters
- Document your modules with a comprehensive README.md
- Structure your project with clear separation of concerns
