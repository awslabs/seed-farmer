# Codebuild Local Agents for Testing Deployments

SeedFarmer now supports using [AWS CodeBuild Agent](https://docs.aws.amazon.com/codebuild/latest/userguide/use-codebuild-agent.html) to allow deployments of SeedFarmer-compliant manifests / modules without any changes.  

It leverages your user credentials via AWS Profile or via AWS Session Credentials.

It is limited to a single account / region as determined by your credentials and (optionally) a region you may pass in.  This does not change your manifests in any way, but does disregard the account / region definitions to go to only a single account / region.  All other configurations are used as if running on AWS CodeBuild.




## More to come here with in-depth detail regarding usage.

