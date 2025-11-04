# AIOps Modules

The **Artificial Intelligence Operations (AIOps)** modules provide specialized infrastructure components for building AI/ML workloads and data science platforms on AWS. These modules are designed to accelerate the deployment of machine learning infrastructure, model training, and AI operations.

## Repository

**Source**: [AWS AIOps Modules](https://github.com/awslabs/aiops-modules)

## Available Modules

**_Coming Soon_** - _Feel free to directly access the Git Repository listed above in the meantime._

We will provide a comprehensive list of:

- current modules available
- description of each module
- input and output definitions
- example manifest configurations

## Key Features

- **ML-Focused**: Purpose-built for machine learning and AI workloads
- **Scalable**: Designed for enterprise-scale ML operations
- **Integrated**: Works seamlessly with AWS AI/ML services
- **Best Practices**: Implements MLOps and AIOps best practices
- **Production Ready**: Battle-tested components for production ML systems

## Usage Example

```yaml
# Deploy a SageMaker Studio environment
name: ml-studio
path: git::https://github.com/awslabs/aiops-modules.git//modules/sagemaker/sagemaker-studio?ref=main&depth=1
targetAccount: primary
parameters:
  - name: studio-domain-name
    value: my-ml-platform
  - name: enable-projects
    value: true
```

## Common Use Cases

- **ML Platform Setup**: Deploy complete SageMaker environments with notebooks, studios, and endpoints
- **Model Training**: Set up distributed training with Ray clusters on EKS
- **MLOps Pipelines**: Implement CI/CD for machine learning models
- **Experiment Tracking**: Deploy MLflow for experiment management and model registry
- **Foundation Models**: Deploy and fine-tune foundation models with Bedrock and SageMaker
- **AI Agents**: Build intelligent automation and autonomous systems

## Getting Started

1. **Identify your ML use case** from the categories above
2. **Review module documentation** for specific AI/ML components
3. **Configure parameters** for your ML workload requirements
4. **Deploy using Seed-Farmer** for consistent, repeatable ML infrastructure

For more information about building ML platforms with Seed-Farmer, see the [Module Development Guide](../../guides/module-development.md).
