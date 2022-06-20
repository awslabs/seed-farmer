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

import logging
import os
from typing import Any

from aws_cdk import Duration, Stack
from aws_cdk import aws_cognito as cognito
from constructs import Construct

_logger: logging.Logger = logging.getLogger(__name__)

project_dir = os.path.dirname(os.path.abspath(__file__))


class Cognito(Stack):
    def __init__(
        self,
        scope: Construct,
        id: str,
        domain_name_prefix: str,
        **kwargs: Any,
    ) -> None:
        super().__init__(scope, id, **kwargs)

        self.cognito_user_pool = cognito.UserPool(
            self,
            id="CognitoUserPool",
            account_recovery=cognito.AccountRecovery.EMAIL_ONLY,
            auto_verify=cognito.AutoVerifiedAttrs(email=True, phone=False),
            password_policy=cognito.PasswordPolicy(
                min_length=8,
                require_digits=True,
                require_lowercase=True,
                require_symbols=True,
                require_uppercase=True,
                temp_password_validity=Duration.days(5),
            ),
            self_sign_up_enabled=False,
            user_invitation=cognito.UserInvitationConfig(
                email_subject="Invite to join!",
                email_body="Hello, you have been invited!<br/><br/>"
                "Username: {username}<br/>"
                "Temporary password: {####}<br/><br/>"
                "Regards",
            ),
            user_verification=cognito.UserVerificationConfig(
                email_subject="Verify your email",
                email_body="Thanks for signing up! Your verification code is {####}",
                email_style=cognito.VerificationEmailStyle.CODE,
            ),
        )

        self.cognito_user_pool_client = cognito.UserPoolClient(
            self,
            id="UserPoolClient",
            user_pool=self.cognito_user_pool,
        )

        self.cognito_domain = cognito.UserPoolDomain(
            self,
            "CognitoDomain",
            user_pool=self.cognito_user_pool,
            cognito_domain=cognito.CognitoDomainOptions(domain_prefix=domain_name_prefix),
        )
