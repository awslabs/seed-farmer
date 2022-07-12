import os

from aws_cdk import App, CfnOutput
from stack import Cognito

deployment_name = os.getenv("MYAPP_DEPLOYMENT_NAME")
module_name = os.getenv("MYAPP_MODULE_NAME")
domain_name_prefix = os.getenv("MYAPP_PARAMETER_DOMAIN_NAME_PREFIX", "")

app = App()

stack = Cognito(
    scope=app,
    id=f"myapp-{deployment_name}-{module_name}",
    domain_name_prefix=domain_name_prefix,
)

CfnOutput(
    scope=stack,
    id="metadata",
    value=stack.to_json_string(
        {
            "CognitoDomainName": stack.cognito_domain.domain_name,
            "CognitoUserPoolArn": stack.cognito_user_pool.user_pool_arn,
            "CognitoPoolClientId": stack.cognito_user_pool_client.user_pool_client_id,
        }
    ),
)

app.synth()
