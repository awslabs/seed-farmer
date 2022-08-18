#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License").
#    You may not use this file except in compliance with the License.
#    You may obtain a copy of the License at
#
#        http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS,
#    WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#    See the License for the specific language governing permissions and
#    limitations under the License.

import hashlib
import logging
from typing import Any, cast

import aws_cdk
import aws_cdk.aws_iam as aws_iam
import aws_cdk.aws_s3 as aws_s3
import cdk_nag
from aws_cdk import Aspects, Stack, Tags
from cdk_nag import NagSuppressions
from constructs import Construct, IConstruct

_logger: logging.Logger = logging.getLogger(__name__)


class BucketsStack(Stack):  # type: ignore
    def __init__(
        self,
        scope: Construct,
        id: str,
        project_name: str,
        deployment_name: str,
        module_name: str,
        hash: str,
        buckets_encryption_type: str,
        buckets_retention: str,
        **kwargs: Any,
    ) -> None:

        # CDK Env Vars
        account: str = aws_cdk.Aws.ACCOUNT_ID
        region: str = aws_cdk.Aws.REGION

        super().__init__(scope, id, **kwargs)
        Tags.of(scope=cast(IConstruct, self)).add(key="Deployment", value=f"{project_name}-{deployment_name}")

        artifact_bucket_name = f"{project_name}-{deployment_name}-artifacts-bucket-{hash}"
        unique_ab = (hashlib.sha1(module_name.encode("UTF-8")).hexdigest())[: (60 - len(artifact_bucket_name))]

        artifacts_bucket = aws_s3.Bucket(
            self,
            id="artifacts-bucket",
            bucket_name=f"{artifact_bucket_name}-{unique_ab}",
            removal_policy=aws_cdk.RemovalPolicy.RETAIN
            if buckets_retention.upper() == "RETAIN"
            else aws_cdk.RemovalPolicy.DESTROY,
            auto_delete_objects=None if buckets_retention.upper() == "RETAIN" else True,
            encryption=aws_s3.BucketEncryption.KMS_MANAGED
            if buckets_encryption_type.upper() == "KMS"
            else aws_s3.BucketEncryption.S3_MANAGED,
            versioned=True,
            block_public_access=aws_s3.BlockPublicAccess.BLOCK_ALL,
            enforce_ssl=True,
        )

        log_bucket_name = f"{project_name}-{deployment_name}-logs-bucket-{hash}"
        unique_log = (hashlib.sha1(module_name.encode("UTF-8")).hexdigest())[: (60 - len(log_bucket_name))]

        logs_bucket = aws_s3.Bucket(
            self,
            id="logs-bucket",
            bucket_name=f"{log_bucket_name}-{unique_log}",
            removal_policy=aws_cdk.RemovalPolicy.RETAIN
            if buckets_retention.upper() == "RETAIN"
            else aws_cdk.RemovalPolicy.DESTROY,
            auto_delete_objects=None if buckets_retention.upper() == "RETAIN" else True,
            encryption=aws_s3.BucketEncryption.KMS_MANAGED
            if buckets_encryption_type.upper() == "KMS"
            else aws_s3.BucketEncryption.S3_MANAGED,
            block_public_access=aws_s3.BlockPublicAccess.BLOCK_ALL,
            enforce_ssl=True,
        )

        # ReadOnly IAM Policy
        readonly_policy = aws_iam.ManagedPolicy(
            self,
            id="readonly_policy",
            managed_policy_name=f"{project_name}-{deployment_name}-{module_name}-{region}-{account}-readonly-access",
            statements=[
                aws_iam.PolicyStatement(
                    effect=aws_iam.Effect.ALLOW,
                    actions=[
                        "kms:Decrypt",
                        "kms:Encrypt",
                        "kms:ReEncrypt*",
                        "kms:DescribeKey",
                        "kms:GenerateDataKey",
                    ],
                    resources=[f"arn:aws:kms::{account}:*"],
                ),
                aws_iam.PolicyStatement(
                    effect=aws_iam.Effect.ALLOW,
                    actions=[
                        "s3:GetObject",
                        "s3:GetObjectAcl",
                        "s3:ListBucket",
                    ],
                    resources=[
                        f"{artifacts_bucket.bucket_arn}/*",
                        f"{artifacts_bucket.bucket_arn}",
                    ],
                ),
            ],
        )

        # FullAccess IAM Policy
        fullaccess_policy = aws_iam.ManagedPolicy(
            self,
            id="fullaccess_policy",
            managed_policy_name=f"{project_name}-{deployment_name}-{module_name}-{region}-{account}-full-access",
            statements=[
                aws_iam.PolicyStatement(
                    effect=aws_iam.Effect.ALLOW,
                    actions=[
                        "kms:Decrypt",
                        "kms:Encrypt",
                        "kms:ReEncrypt*",
                        "kms:DescribeKey",
                        "kms:GenerateDataKey",
                    ],
                    resources=[f"arn:aws:kms::{account}:*"],
                ),
                aws_iam.PolicyStatement(
                    effect=aws_iam.Effect.ALLOW,
                    actions=[
                        "s3:GetObject",
                        "s3:GetObjectAcl",
                        "s3:ListBucket",
                    ],
                    resources=[
                        f"{artifacts_bucket.bucket_arn}/*",
                        f"{artifacts_bucket.bucket_arn}",
                    ],
                ),
                aws_iam.PolicyStatement(
                    actions=["s3:PutObject", "s3:PutObjectAcl"],
                    resources=[
                        f"{artifacts_bucket.bucket_arn}/*",
                        f"{artifacts_bucket.bucket_arn}",
                    ],
                ),
            ],
        )

        self.artifacts_bucket = artifacts_bucket
        self.logs_bucket = logs_bucket
        self.readonly_policy = readonly_policy
        self.fullaccess_policy = fullaccess_policy

        Aspects.of(self).add(cdk_nag.AwsSolutionsChecks())

        suppressions = [
            {
                "id": "AwsSolutions-S1",
                "reason": "Logging has been disabled for demo purposes",
                "applies_to": "*",
            },
            {
                "id": "AwsSolutions-IAM5",
                "reason": "Resource access restriced to resources",
                "applies_to": "*",
            },
        ]

        NagSuppressions.add_stack_suppressions(self, suppressions)
