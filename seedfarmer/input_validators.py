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
    def validate_qualifier(qualifier: str) -> tuple[bool, Optional[str]]:
        """
        Validate qualifier parameter.

        Args:
            qualifier: Qualifier string to validate

        Returns:
            Tuple of (is_valid, error_message)
        """
        if not qualifier:
            return True, None

        if len(qualifier) > InputValidator.QUALIFIER_MAX_LENGTH:
            return False, f"Qualifier must be {InputValidator.QUALIFIER_MAX_LENGTH} characters or less"

        if not InputValidator.ALPHANUMERIC_PATTERN.match(qualifier):
            return False, "Qualifier must be alphanumeric"

        return True, None

    @staticmethod
    def validate_role_prefix(role_prefix: str) -> tuple[bool, Optional[str]]:
        """
        Validate IAM role path prefix.

        Args:
            role_prefix: IAM path prefix to validate

        Returns:
            Tuple of (is_valid, error_message)
        """
        if not role_prefix:
            return True, None

        if len(role_prefix) > InputValidator.IAM_PATH_MAX_LENGTH:
            return False, f"Role prefix must be {InputValidator.IAM_PATH_MAX_LENGTH} characters or less"

        if not role_prefix.startswith("/"):
            return False, "Role prefix must start with '/'"

        if not role_prefix.endswith("/"):
            return False, "Role prefix must end with '/'"

        if not InputValidator.IAM_PATH_PATTERN.match(role_prefix):
            return False, "Role prefix contains invalid characters. Allowed: a-z, A-Z, 0-9, +=,.@-_/"

        return True, None

    @staticmethod
    def validate_policy_prefix(policy_prefix: str) -> tuple[bool, Optional[str]]:
        """
        Validate IAM policy path prefix.

        Args:
            policy_prefix: IAM path prefix to validate

        Returns:
            Tuple of (is_valid, error_message)
        """
        # Policy prefix has same rules as role prefix
        return InputValidator.validate_role_prefix(policy_prefix)

    @staticmethod
    def validate_project_name(project_name: str) -> tuple[bool, Optional[str]]:
        """
        Validate project name.

        Args:
            project_name: Project name to validate

        Returns:
            Tuple of (is_valid, error_message)
        """
        if not project_name:
            return False, "Project name cannot be empty"

        if len(project_name) > InputValidator.PROJECT_NAME_MAX_LENGTH:
            return False, f"Project name must be {InputValidator.PROJECT_NAME_MAX_LENGTH} characters or less"

        if not InputValidator.AWS_RESOURCE_NAME_PATTERN.match(project_name):
            return False, "Project name contains invalid characters"

        if project_name.startswith("-") or project_name.endswith("-"):
            return False, "Project name cannot start or end with a hyphen"

        return True, None

    @staticmethod
    def validate_deployment_name(deployment_name: str) -> tuple[bool, Optional[str]]:
        """
        Validate deployment name.

        Args:
            deployment_name: Deployment name to validate

        Returns:
            Tuple of (is_valid, error_message)
        """
        if not deployment_name:
            return False, "Deployment name cannot be empty"

        if len(deployment_name) > InputValidator.DEPLOYMENT_NAME_MAX_LENGTH:
            return False, f"Deployment name must be {InputValidator.DEPLOYMENT_NAME_MAX_LENGTH} characters or less"

        if not InputValidator.AWS_RESOURCE_NAME_PATTERN.match(deployment_name):
            return False, "Deployment name contains invalid characters"

        if deployment_name.startswith("-") or deployment_name.endswith("-"):
            return False, "Deployment name cannot start or end with a hyphen"

        return True, None

    @staticmethod
    def validate_group_name(group_name: str) -> tuple[bool, Optional[str]]:
        """
        Validate group name.

        Args:
            group_name: Group name to validate

        Returns:
            Tuple of (is_valid, error_message)
        """
        if not group_name:
            return False, "Group name cannot be empty"

        if len(group_name) > InputValidator.GROUP_NAME_MAX_LENGTH:
            return False, f"Group name must be {InputValidator.GROUP_NAME_MAX_LENGTH} characters or less"

        if not InputValidator.AWS_RESOURCE_NAME_PATTERN.match(group_name):
            return False, "Group name contains invalid characters"

        if group_name.startswith("-") or group_name.endswith("-"):
            return False, "Group name cannot start or end with a hyphen"

        return True, None

    @staticmethod
    def validate_module_name(module_name: str) -> tuple[bool, Optional[str]]:
        """
        Validate module name.

        Args:
            module_name: Module name to validate

        Returns:
            Tuple of (is_valid, error_message)
        """
        if not module_name:
            return False, "Module name cannot be empty"

        if len(module_name) > InputValidator.MODULE_NAME_MAX_LENGTH:
            return False, f"Module name must be {InputValidator.MODULE_NAME_MAX_LENGTH} characters or less"

        if not InputValidator.AWS_RESOURCE_NAME_PATTERN.match(module_name):
            return False, "Module name contains invalid characters"

        if module_name.startswith("-") or module_name.endswith("-"):
            return False, "Module name cannot start or end with a hyphen"

        return True, None

    @staticmethod
    def validate_arn(arn: str) -> tuple[bool, Optional[str]]:
        """
        Validate AWS ARN format.

        Args:
            arn: ARN string to validate

        Returns:
            Tuple of (is_valid, error_message)
        """
        if not arn:
            return False, "ARN cannot be empty"

        if not InputValidator.ARN_PATTERN_WITH_AWS.match(arn):
            return False, "Invalid ARN format. Expected: arn:aws:service::account-id:resource"

        return True, None

    @staticmethod
    def validate_session_timeout(timeout: int) -> tuple[bool, Optional[str]]:
        """
        Validate session timeout interval.

        Args:
            timeout: Timeout in seconds

        Returns:
            Tuple of (is_valid, error_message)
        """
        if timeout <= 0:
            return False, "Session timeout must be a positive integer"

        if timeout < 60:
            return False, "Session timeout must be at least 60 seconds"

        if timeout > 43200:  # 12 hours
            return False, "Session timeout must be 43200 seconds (12 hours) or less"

        return True, None

    @staticmethod
    def validate_role_name_length(project_name: str, qualifier: Optional[str] = None) -> tuple[bool, Optional[str]]:
        """
        Validate that the generated role name will not exceed IAM limits.

        Args:
            project_name: Project name
            qualifier: Optional qualifier

        Returns:
            Tuple of (is_valid, error_message)
        """
        # Format: seedfarmer-{project_name}-toolchain-role[-{qualifier}]
        base_length = len("seedfarmer--toolchain-role")
        role_name_length = base_length + len(project_name)

        if qualifier:
            role_name_length += len(qualifier) + 1  # +1 for the hyphen

        if role_name_length > InputValidator.IAM_ROLE_NAME_MAX_LENGTH:
            return False, (
                f"Generated role name would be {role_name_length} characters, "
                f"exceeding IAM limit of {InputValidator.IAM_ROLE_NAME_MAX_LENGTH}. "
                f"Use a shorter project name or qualifier."
            )

        return True, None
