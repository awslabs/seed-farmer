# Eks Modules

This section contains all eks modules available in the IDF framework.


??? info "Ray Cluster"
    
    **Module:** `eks/ray-cluster`
    
    This module creates a Ray cluster in AWS EKS Kubernetes cluster. It deploys a RayClsuter via [kuberay-helm](https://github.com/ray-project/kuberay-helm) and a ClusterIP service. Requires a RayOperator...
    
    [View Details](./ray-cluster.md){ .md-button }
    [GitHub Source](https://github.com/awslabs/aiops-modules/tree/main/modules/eks/ray-cluster){ .md-button .md-button--primary }


??? info "Introduction"
    
    **Module:** `eks/ray-image`
    
    This module demonstrates an example on how to build a custom Ray Docker image. The image is pushed to AWS ECR with enabled scan on push.
    
    [View Details](./ray-image.md){ .md-button }
    [GitHub Source](https://github.com/awslabs/aiops-modules/tree/main/modules/eks/ray-image){ .md-button .md-button--primary }


??? info "Ray Operator"
    
    **Module:** `eks/ray-operator`
    
    This module runs Ray Operator in AWS EKS Kubernetes cluster. It deploys a KubeRay Operator via [kuberay-helm](https://github.com/ray-project/kuberay-helm).
    
    [View Details](./ray-operator.md){ .md-button }
    [GitHub Source](https://github.com/awslabs/aiops-modules/tree/main/modules/eks/ray-operator){ .md-button .md-button--primary }


??? info "Ray Orchestrator"
    
    **Module:** `eks/ray-orchestrator`
    
    This module orchestrates submission of a Ray training job to the Ray Cluster and an inference job using AWS Step Functions.
    
    [View Details](./ray-orchestrator.md){ .md-button }
    [GitHub Source](https://github.com/awslabs/aiops-modules/tree/main/modules/eks/ray-orchestrator){ .md-button .md-button--primary }

