# Architecture

**Seed-Farmer** does not create its own deployments, rather it helps to deploy YOUR modules by acting as the broker between your 
module code and the AWS Cloud via AWS CodeSeeder.


## Multi-Account Architecture
<TODO: PUT MULTI-ACCOUNT DIAGRAM HERE!!>
<TODO: Explain the multi-account stuff with toolchain roles and target/deployment roles>

## Method of processing
Below is a flow of `seed-farmer` deployment of a single module in a single account/region.  Once `seed-farmer` resolves the proer target/deployment role, the following depicts the steps taken to deploy a module.
![Seed-Farmer Invocation](_static/SeedFarmer.png)

1. Invoke **seedfarmer** CLI
2. **seedfarmer** reads/writes deployment metadata with AWS Systems Manager
3. **seedfarmer** invokes AWS IAM to create module-specific roles, attaching the proper least-privilege policies
4. **seedfarmer** leverages **AWS CodeSeeder** for remote deployment on AWS CodeBuild
5. **AWS CodeSeeder** prepares AWS CodeBuild 
6. AWS CodeBuild via **AWS CodeSeeder** inspects and fetches data from AWS SecretsManager (if necessary)
7. AWS CodeBuild via **AWS CodeSeeder** executes the custom **deployspec** for the module
9. AWS CodeBuild via **AWS CodeSeeder** updates AWS Systems Manager with completed module metadata
9. **seedfarmer** updates deployment metadata in AWS Systems Manager

