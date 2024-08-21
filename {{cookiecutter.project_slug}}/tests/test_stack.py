# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

import os
import sys
from unittest import mock

import aws_cdk
import cdk_nag
import pytest
from aws_cdk.assertions import Annotations, Match, Template


@pytest.fixture(scope="function")
def stack_defaults():
    with mock.patch.dict(os.environ, {}, clear=True):
        os.environ["CDK_DEFAULT_ACCOUNT"] = "111111111111"
        os.environ["CDK_DEFAULT_REGION"] = "us-east-1"

        # Unload the app import so that subsequent tests don't reuse
        if "stack" in sys.modules:
            del sys.modules["stack"]

        yield


@pytest.fixture(scope="function")
def stack(stack_defaults) -> aws_cdk.Stack:
    import stack

    app = aws_cdk.App()

    project_name = "test-project"
    dep_name = "test-deployment"
    mod_name = "test-module"
    app_prefix = f"{project_name}-{dep_name}-{mod_name}"

    return stack.TemplateStack(
        app,
        app_prefix,
        stack_description="Stack Description",
    )


def test_synthesize_stack(stack: aws_cdk.Stack) -> None:
    Template.from_stack(stack)


def test_no_cdk_nag_errors(stack: aws_cdk.Stack, use_rds: bool) -> None:
    aws_cdk.Aspects.of(stack).add(cdk_nag.AwsSolutionsChecks())

    nag_errors = Annotations.from_stack(stack).find_error(
        "*",
        Match.string_like_regexp(r"AwsSolutions-.*"),
    )
    assert not nag_errors, f"Found {len(nag_errors)} CDK nag errors"
