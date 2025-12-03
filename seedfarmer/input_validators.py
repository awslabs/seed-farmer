#    Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
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

import re
from typing import Optional


class InputValidator:
    """Validates CLI input parameters to ensure they meet AWS and Seed-Farmer requirements."""

    # AWS IAM limits
    IAM_ROLE_NAME_MAX_LENGTH = 64
    IAM_PATH_MAX_LENGTH = 512

    # Seed-Farmer specific limits
    QUALIFIER_MAX_LENGTH = 6
    PROJECT_NAME_MAX_LENGTH = 35  # Must fit in IAM role name: seedfarmer-{project}-toolchain-role
    DEPLOYMENT_NAME_MAX_LENGTH = 64
    GROUP_NAME_MAX_LENGTH = 64
    MODULE_NAME_MAX_LENGTH = 64

    # Regex patterns
    IAM_PATH_PATTERN = re.compile(r"^/([a-zA-Z0-9+=,.@\-_]+/)*$")
    ARN_PATTERN = re.compile(r"^arn:aws[a-z\-]*:[a-z0-9\-]+::[0-9]{12}:.*$")
    ARN_PATTERN_WITH_AWS = re.compile(r"^arn:aws[a-z\-]*:[a-z0-9\-]+::(aws|[0-9]{12}|\*):.*$")
    AWS_RESOURCE_NAME_PATTERN = re.compile(r"^[a-zA-Z0-9+=,.@_.\-]+$")
    ALPHANUMERIC_PATTERN = re.compile(r"^[a-zA-Z0-9]+$")

    @staticmethod
    def validate_qualifier(qualifier: str, exception_type: type[Exception] = ValueError) -> None:
        """Validate qualifier parameter and raise if invalid."""
        if not qualifier:
            return
        if len(qualifier) > InputValidator.QUALIFIER_MAX_LENGTH:
            raise exception_type(f"Qualifier must be {InputValidator.QUALIFIER_MAX_LENGTH} characters or less")
        if not InputValidator.ALPHANUMERIC_PATTERN.match(qualifier):
            raise exception_type("Qualifier must be alphanumeric")

    @staticmethod
    def validate_role_prefix(role_prefix: str, exception_type: type[Exception] = ValueError) -> None:
        """Validate IAM role path prefix and raise if invalid."""
        if not role_prefix:
            return
        if len(role_prefix) > InputValidator.IAM_PATH_MAX_LENGTH:
            raise exception_type(f"Role prefix must be {InputValidator.IAM_PATH_MAX_LENGTH} characters or less")
        if not role_prefix.startswith("/"):
            raise exception_type("Role prefix must start with '/'")
        if not role_prefix.endswith("/"):
            raise exception_type("Role prefix must end with '/'")
        if not InputValidator.IAM_PATH_PATTERN.match(role_prefix):
            raise exception_type(
                "Role prefix contains invalid characters. Allowed: a-zA-Z0-9+=,.@-_ and forward slashes"
            )

    @staticmethod
    def validate_policy_prefix(policy_prefix: str, exception_type: type[Exception] = ValueError) -> None:
        """Validate IAM policy path prefix and raise if invalid."""
        InputValidator.validate_role_prefix(policy_prefix, exception_type)

    @staticmethod
    def validate_project_name(project_name: str, exception_type: type[Exception] = ValueError) -> None:
        """Validate project name and raise if invalid."""
        if not project_name:
            raise exception_type("Project name cannot be empty")
        if len(project_name) > InputValidator.PROJECT_NAME_MAX_LENGTH:
            raise exception_type(f"Project name must be {InputValidator.PROJECT_NAME_MAX_LENGTH} characters or less")
        if not InputValidator.AWS_RESOURCE_NAME_PATTERN.match(project_name):
            raise exception_type("Project name contains invalid characters")
        if project_name.startswith("-") or project_name.endswith("-"):
            raise exception_type("Project name cannot start or end with a hyphen")

    @staticmethod
    def validate_deployment_name(deployment_name: str, exception_type: type[Exception] = ValueError) -> None:
        """Validate deployment name and raise if invalid."""
        if not deployment_name:
            raise exception_type("Deployment name cannot be empty")
        if len(deployment_name) > InputValidator.DEPLOYMENT_NAME_MAX_LENGTH:
            raise exception_type(
                f"Deployment name must be {InputValidator.DEPLOYMENT_NAME_MAX_LENGTH} characters or less"
            )
        if not InputValidator.AWS_RESOURCE_NAME_PATTERN.match(deployment_name):
            raise exception_type("Deployment name contains invalid characters")
        if deployment_name.startswith("-") or deployment_name.endswith("-"):
            raise exception_type("Deployment name cannot start or end with a hyphen")

    @staticmethod
    def validate_group_name(group_name: str, exception_type: type[Exception] = ValueError) -> None:
        """Validate group name and raise if invalid."""
        if not group_name:
            raise exception_type("Group name cannot be empty")
        if len(group_name) > InputValidator.GROUP_NAME_MAX_LENGTH:
            raise exception_type(f"Group name must be {InputValidator.GROUP_NAME_MAX_LENGTH} characters or less")
        if not InputValidator.AWS_RESOURCE_NAME_PATTERN.match(group_name):
            raise exception_type("Group name contains invalid characters")
        if group_name.startswith("-") or group_name.endswith("-"):
            raise exception_type("Group name cannot start or end with a hyphen")

    @staticmethod
    def validate_module_name(module_name: str, exception_type: type[Exception] = ValueError) -> None:
        """Validate module name and raise if invalid."""
        if not module_name:
            raise exception_type("Module name cannot be empty")
        if len(module_name) > InputValidator.MODULE_NAME_MAX_LENGTH:
            raise exception_type(f"Module name must be {InputValidator.MODULE_NAME_MAX_LENGTH} characters or less")
        if not InputValidator.AWS_RESOURCE_NAME_PATTERN.match(module_name):
            raise exception_type("Module name contains invalid characters")
        if module_name.startswith("-") or module_name.endswith("-"):
            raise exception_type("Module name cannot start or end with a hyphen")

    @staticmethod
    def validate_arn(arn: str, exception_type: type[Exception] = ValueError) -> None:
        """Validate ARN format and raise if invalid."""
        if not arn:
            raise exception_type("ARN cannot be empty")
        if not (InputValidator.ARN_PATTERN.match(arn) or InputValidator.ARN_PATTERN_WITH_AWS.match(arn)):
            raise exception_type("Invalid ARN format")

    @staticmethod
    def validate_session_timeout(timeout: int, exception_type: type[Exception] = ValueError) -> None:
        """Validate session timeout and raise if invalid."""
        if timeout < 60:
            raise exception_type("Session timeout must be at least 60 seconds (1 minute)")
        if timeout > 43200:
            raise exception_type("Session timeout must be 43200 seconds (12 hours) or less")

    @staticmethod
    def validate_role_name_length(
        project_name: str, qualifier: Optional[str] = None, exception_type: type[Exception] = ValueError
    ) -> None:
        """Validate that the generated role name will not exceed IAM limits."""
        base_length = len("seedfarmer--toolchain-role")
        role_name_length = base_length + len(project_name)
        if qualifier:
            role_name_length += len(qualifier) + 1
        if role_name_length > InputValidator.IAM_ROLE_NAME_MAX_LENGTH:
            raise exception_type(
                f"Generated role name would be {role_name_length} characters, "
                f"exceeding IAM limit of {InputValidator.IAM_ROLE_NAME_MAX_LENGTH}. "
                f"Use a shorter project name or qualifier."
            )
