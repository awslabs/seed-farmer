import os

import aws_cdk
from aws_cdk import App, CfnOutput

from stack import NetworkingStack

project_name = os.getenv("AWS_CODESEEDER_NAME")

def _proj(name:str)-> str:
    return f"{project_name.upper()}_{name}"

def _param(name: str) -> str:
    return f"{project_name.upper()}_PARAMETER_{name}"


# get the env parameters with proper prefixes
deployment_name = os.getenv(_proj("DEPLOYMENT_NAME"), "")
module_name = os.getenv(_proj("MODULE_NAME"), "")
hash = os.getenv(_proj("HASH"), "")
internet_accessible = os.getenv(_param("INTERNET_ACCESSIBLE"), True)

app = App()

stack = NetworkingStack(
    scope=app,
    id=f"{project_name}-{deployment_name}-{module_name}",
    project_name=project_name,
    deployment_name=deployment_name,
    module_name=module_name,
    internet_accessible=internet_accessible,
    env=aws_cdk.Environment(
        account=os.environ["CDK_DEFAULT_ACCOUNT"],
        region=os.environ["CDK_DEFAULT_REGION"],
    ),
)

CfnOutput(
    scope=stack,
    id="vpcId",
    value=stack.vpc.vpc_id,
)

CfnOutput(
    scope=stack,
    id="publicSubnetIds",
    value=",".join(stack.public_subnets.subnet_ids),
)

CfnOutput(
    scope=stack,
    id="privateSubnetIds",
    value=",".join(stack.private_subnets.subnet_ids),
)

if not stack.internet_accessible:
    CfnOutput(
        scope=stack,
        id="isolatedSubnetIds",
        value=",".join(stack.isolated_subnets.subnet_ids),
    )

CfnOutput(
    scope=stack,
    id="nodeSubnetIds",
    value=",".join(stack.nodes_subnets.subnet_ids),
)

CfnOutput(
    scope=stack,
    id="metadata",
    value=stack.to_json_string(
        {
            "VpcId": stack.vpc.vpc_id,
            "PublicSubnetIds": stack.public_subnets.subnet_ids,
            "PrivateSubnetIds": stack.private_subnets.subnet_ids,
            "IsolatedSubnetIds": stack.isolated_subnets.subnet_ids if not stack.internet_accessible else [],
        }
    ),
)

app.synth(force=True)
