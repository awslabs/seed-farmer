# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

from typing import Any

import aws_cdk
import cdk_nag
from constructs import Construct


class TemplateStack(aws_cdk.Stack):
    def __init__(
        self,
        scope: Construct,
        id: str,
        **kwargs: Any,
    ) -> None:
        super().__init__(scope, id, **kwargs)

        # TODO define your stack here
        # ...

        # TODO define your nag suppressions if necessary here
        # cdk_nag.NagSuppressions.add_resource_suppressions(
        # )
