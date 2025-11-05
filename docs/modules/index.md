---
title: Public Modules
---

Seed-Farmer provides access to a comprehensive library of pre-built, reusable infrastructure modules that you can use in your deployments. These modules are designed to accelerate your infrastructure development by providing tested, production-ready components.

## How to Use Public Modules

### Git Path References

You can reference modules directly in your deployment manifests using Git paths. Seed-Farmer will automatically fetch the code during deployment:

```yaml
name: networking
path: git::https://github.com/awslabs/idf-modules.git//modules/network/basic-cdk?ref=release/1.0.0&depth=1
targetAccount: primary
```

### Local References

You can also clone the repository and reference modules from your local filesystem:

```yaml
name: networking
path: modules/network/basic-cdk/
targetAccount: primary
```

## Available Module Collections

### [IDF Modules](idf-modules/index.md)

The **Industry Data Framework (IDF)** modules provide foundational infrastructure components for data processing and analytics solutions. These modules cover networking, compute, storage, databases, and orchestration services.

**Key Categories**: Compute, Database, Network, Storage, Orchestration, Integration

### [AIOps Modules](aiops-modules/index.md)

The **Artificial Intelligence Operations (AIOps)** modules provide specialized components for AI/ML workloads, including SageMaker services, MLflow, Ray clusters, and example implementations.

**Key Categories**: SageMaker, MLflow, EKS, Agents, Examples, FMOps

## Module Benefits

- **Production Ready**: All modules are tested and designed for production use
- **Consistent Patterns**: Follow AWS best practices and consistent architectural patterns
- **Parameterized**: Configurable through deployment manifest parameters
- **Documented**: Each module includes comprehensive documentation and examples
- **Versioned**: Use specific versions or branches for stability and reproducibility

## Getting Started

1. **Browse the module collections** to find components that match your needs
2. **Review module documentation** to understand parameters and outputs
3. **Reference modules in your deployment manifest** using Git paths or local paths
4. **Deploy using Seed-Farmer** with `seedfarmer apply`

For more information about using modules in deployments, see the [Module Development Guide](../guides/module-development.md).
