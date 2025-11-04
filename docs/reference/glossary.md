# Glossary

This glossary provides definitions for technical terms and concepts used throughout the SeedFarmer documentation. Terms are organized alphabetically for easy reference.

### A 

### B 

**Bundle**: A collection of module code and dependencies that gets packaged and deployed together. The bundle includes the module's infrastructure code, deployspec, and any additional data files needed for deployment.

### C 

**Configuration File**: A structured file that defines settings, parameters, and behavior for SeedFarmer components. Common configuration files include `seedfarmer.yaml` (project configuration), `deployspec.yaml` (deployment instructions), and `modulestack.yaml` (IAM permissions).

### D 

**Deployspec.yaml**: The YAML configuration file that serves as the execution blueprint for a module. It defines the phases and commands for both deployment and destruction operations, including dependency installation, pre/post-build steps, and the main build commands that deploy infrastructure resources.

**Deployment**: A specific instance of a project that defines the overall deployment strategy, including target accounts, regions, and groups of modules to be deployed. Defined by a deployment manifest that serves as the master configuration.

**Deployment Role**: An IAM role created in each target account that is assumed by the Toolchain Role to orchestrate module deployments. This role is also referred to as a Target Role.  The Deployment Role has account-specific permissions with minimal required access and includes explicit deny policies for high-risk IAM actions to maintain security posture. It creates Module roles that are assigned to AWS Codebuild jobs by SeedFarmer.

### E 

### F 

### G 

**GitOps**: A deployment methodology that uses Git repositories as the single source of truth for infrastructure configuration. SeedFarmer follows GitOps principles by using declarative manifests stored in version control to define and manage infrastructure deployments.

**Group**: A logical collection of related modules within a deployment that are processed together. Groups are deployed sequentially, with modules within each group deployed in parallel. Groups help organize modules by function (e.g., networking, compute, applications) and manage deployment dependencies.

### H 

### I 

**IAM (Identity and Access Management)**: AWS service that enables secure control of access to AWS resources. SeedFarmer uses IAM extensively for its multi-account security model, creating roles with least-privilege permissions for toolchain operations, deployment orchestration, and module-specific resource management.

**Infrastructure as Code (IaC)**: The practice of managing and provisioning infrastructure through machine-readable definition files rather than manual processes. SeedFarmer supports various IaC tools including AWS CDK, CloudFormation, and Terraform.

### J 

### K 

### L 

**Least Privilege**: A security principle that grants users and roles only the minimum permissions necessary to perform their required tasks. SeedFarmer implements least privilege through its role hierarchy, where Toolchain Roles have orchestration permissions, Deployment Roles have account-specific permissions, and Module Roles have only the permissions needed for their specific resources.

### M 

**Manifest**: Configuration files that define what gets deployed, where it gets deployed, and how it gets configured. SeedFarmer uses two types of manifests: deployment manifests (top-level configuration) and module manifests (individual component configurations).

**Metadata**: Information about deployed modules that can be exported and consumed by other modules. Metadata includes outputs, resource identifiers, and configuration values that enable module interconnection and dependency management. Managed through the deployspec and accessible via AWS Systems Manager Parameter Store.

**Module**: The fundamental deployable unit in SeedFarmer. A self-contained Infrastructure as Code component that deploys specific AWS resources. Modules are reusable, composable building blocks that can be combined to create complex infrastructure deployments.

**Module Role**: An IAM role created per module in the target account with least-privilege permissions specific to that module's resource requirements. The Module Role is assumed by the Deployment Role and uses permissions defined in the optional `modulestack.yaml` file to deploy and manage the module's AWS resources. This granular approach ensures each module has only the permissions it needs.

**Modulestack.yaml**: An optional AWS CloudFormation template file that defines the specific IAM permissions required by a module's role. It follows CloudFormation syntax and includes parameters that correspond to the module's manifest parameters, enabling least-privilege permission policies tailored to each module's resource requirements.  This is used to allow the Module role to execute AWS-specific commands directly from the deployspec.yaml (ex. create and pull from an S3 bucket).

**Multi-Account Security Model**: SeedFarmer's security architecture that uses IAM role assumption chains across multiple AWS accounts to provide isolation and least-privilege access. The model includes Toolchain Roles in the central account, Deployment Roles in target accounts, and Module Roles for individual components, with optional permissions boundaries and qualifiers for enhanced security controls.

### N 

### O 

### P 

**Parameter**: A configurable value that can be passed to modules during deployment to customize their behavior. Parameters are defined in manifest files and can include strings, numbers, booleans, or complex data structures. They enable module reusability by allowing the same module to be deployed with different configurations.

**Permissions Boundary**: An optional IAM feature that sets the maximum permissions an IAM role can have, providing an additional layer of security control. SeedFarmer supports applying permissions boundaries to Toolchain Roles and Deployment Roles to further restrict their permissions and enhance security posture in multi-account deployments.

**Project**: The top-level orginaztional structure of SeedFarmer managed deployments.  This is defined in the `seedfarmer.yaml` and applies to all Deployments with that project name definition.

### Q 

**Qualifier**: A 6-character alphanumeric string that can be appended to Toolchain Roles and Deployment Roles to segregate target deployments in multi-account structures. Qualifiers must be the same on both the toolchain role and each target role, providing a way to create multiple isolated deployment environments within the same account structure.

### R 

**Role Assumption**: The AWS IAM mechanism that allows one role to temporarily assume the permissions of another role. SeedFarmer uses role assumption chains where the Toolchain Role assumes Deployment Roles in target accounts, which then assume Module Roles to deploy specific resources. This creates a secure, auditable chain of permissions across accounts.

### - S -

**seedfarmer.yaml**: The main project configuration file that defines project-level settings including project name, description, and global configuration options. Located at the root of a SeedFarmer project, it serves as the entry point for project identification and validation settings.

**SeedFarmer Artifacts**: SeedFarmer resources (an S3 bucket) for storing module-specific artifacts.  This supports for example, the ability to destroy modules without the need of bundling the code and as an overflow for storing metadata that is too large for AWS SSM Parameter storage.

**Seedkit**: The foundational infrastructure that SeedFarmer deploys in each target account and region to enable module deployments. It includes AWS CodeBuild projects, S3 buckets for artifacts, and IAM service roles necessary for deployment execution.

### T 

**Target Account**: An account configured to allow SeedFarmer to deploy modules.  Each target account must have a target role as defined by the SeedFarmer boostrap.

**Target Role**: See _Deployment Role_

**Toolchain Account** The primary AWS Account that stores deployment-specific data.  The toolchain account is also defined by a  region associated with the account.

**Toolchain Role**: An IAM role created in the toolchain account that serves as the central orchestration role for SeedFarmer deployments. It is assumed by users or CI/CD systems and has permissions limited to orchestration and metadata management, including access to AWS Systems Manager for module metadata and the ability to assume Deployment Roles in target accounts. The Toolchain Role follows least-privilege principles and can be configured with qualifiers and permissions boundaries for enhanced security.

### U 

### V 

### W 

### X 

### Y 

### Z 
