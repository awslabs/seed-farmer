import os

import aws_cdk
from aws_cdk import App, CfnOutput
from stack import BucketsStack

project_name = os.getenv("SEEDFARMER_PROJECT_NAME", "")
deployment_name = os.getenv("SEEDFARMER_DEPLOYMENT_NAME", "")
module_name = os.getenv("SEEDFARMER_MODULE_NAME", "")
hash = os.getenv("SEEDFARMER_HASH", "")


buckets_encryption_type = os.getenv("SEEDFARMER_PARAMETER_ENCRYPTION_TYPE", "SSE")
buckets_retention = os.getenv("SEEDFARMER_PARAMETER_RETENTION_TYPE", "DESTROY")


app = App()


stack = BucketsStack(
    scope=app,
    id=f"{project_name}-{deployment_name}-{module_name}",
    project_name=project_name,
    deployment_name=deployment_name,
    module_name=module_name,
    buckets_encryption_type=buckets_encryption_type,
    buckets_retention=buckets_retention,
    hash=hash,
    env=aws_cdk.Environment(
        account=os.environ["CDK_DEFAULT_ACCOUNT"],
        region=os.environ["CDK_DEFAULT_REGION"],
    ),
)

CfnOutput(
    scope=stack,
    id="metadata",
    value=stack.to_json_string(
        {
            "ArtifactsBucketName": stack.artifacts_bucket.bucket_name,
            "LogsBucketName": stack.logs_bucket.bucket_name,
            "ReadOnlyPolicyArn": stack.readonly_policy.managed_policy_arn,
            "FullAccessPolicyArn": stack.fullaccess_policy.managed_policy_arn,
        }
    ),
)


app.synth(force=True)
