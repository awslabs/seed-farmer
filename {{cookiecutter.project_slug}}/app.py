# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

import aws_cdk
import cdk_nag

from settings import ApplicationSettings
from stack import TemplateStack

app_settings = ApplicationSettings()
app = aws_cdk.App()

template_stack = TemplateStack(
    scope=app,
    id=app_settings.settings.app_prefix,
    stack_description=app_settings.parameters.module_description,
    env=aws_cdk.Environment(
        account=app_settings.default.account,
        region=app_settings.default.region,
    ),
)

aws_cdk.CfnOutput(
    scope=template_stack,
    id="metadata",
    value=template_stack.to_json_string(
        {
            "TemplateOutput1": "Add something from template_stack",
        }
    ),
)

aws_cdk.Aspects.of(app).add(cdk_nag.AwsSolutionsChecks(log_ignores=True))

aws_cdk.Tags.of(app).add("Deployment", app_settings.settings.app_prefix)

app.synth()
