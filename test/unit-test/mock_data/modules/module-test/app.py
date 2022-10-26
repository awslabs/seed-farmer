import os

from aws_cdk import App, CfnOutput
from stack import S3

deployment_name = os.getenv("MYAPP_DEPLOYMENT_NAME")
module_name = os.getenv("MYAPP_MODULE_NAME")
event_bridge_enabled = os.getenv("MYAPP_PARAMETER_EVENT_BRIDGE_ENABLED", False)

app = App()

stack = S3(
    scope=app,
    id=f"myapp-{deployment_name}-{module_name}",
)

CfnOutput(
    scope=stack,
    id="metadata",
    value=stack.to_json_string(
        {
            "BucketName": stack.bucket.bucket_name,
        }
    ),
)

app.synth()
