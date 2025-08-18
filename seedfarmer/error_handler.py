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
import sys
from functools import wraps
from typing import Any, Callable, NoReturn, Optional, TypeVar

import botocore.exceptions
import click

from seedfarmer.errors.seedfarmer_errors import (
    InvalidConfigurationError,
    InvalidManifestError,
    InvalidPathError,
    InvalidSessionError,
    ModuleDeploymentError,
    RemoteDeploymentRuntimeError,
    SeedFarmerException,
)

_logger: logging.Logger = logging.getLogger(__name__)

F = TypeVar("F", bound=Callable[..., Any])


def print_error_message(message: str, color: str = "red") -> None:
    """
    Simple error message printer to avoid circular imports.
    """
    if color == "red":
        click.echo(click.style(message, fg="red", bold=True))
    elif color == "yellow":
        click.echo(click.style(message, fg="yellow", bold=True))
    else:
        click.echo(click.style(message, bold=True))


def handle_seedfarmer_error(error: Exception, context: Optional[str] = None) -> NoReturn:
    """
    Handle SeedFarmer specific errors with user-friendly messages.

    Args:
        error: The exception that occurred
        context: Optional context about when the error occurred
    """
    error_prefix = f"[{context}] " if context else ""

    if isinstance(error, InvalidPathError):
        print_error_message(f"{error_prefix}Path Error: {error}", "red")
        _logger.debug("Full error details: %s", error, exc_info=True)

    elif isinstance(error, InvalidManifestError):
        print_error_message(f"{error_prefix}Manifest Error: {error}", "red")
        print_error_message("Please check your deployment manifest syntax and structure.", "yellow")
        _logger.debug("Full error details: %s", error, exc_info=True)

    elif isinstance(error, InvalidConfigurationError):
        print_error_message(f"{error_prefix}Configuration Error: {error}", "red")
        print_error_message("Please verify your configuration settings.", "yellow")
        _logger.debug("Full error details: %s", error, exc_info=True)

    elif isinstance(error, ModuleDeploymentError):
        print_error_message(f"{error_prefix}Deployment Error: {error}", "red")
        print_error_message("Check the deployment logs for more details.", "yellow")
        _logger.debug("Full error details: %s", error, exc_info=True)

    elif isinstance(error, InvalidSessionError):
        print_error_message(f"{error_prefix}Session Error: {error}", "red")
        print_error_message("Please check your AWS credentials and permissions.", "yellow")
        _logger.debug("Full error details: %s", error, exc_info=True)

    elif isinstance(error, RemoteDeploymentRuntimeError):
        print_error_message(f"{error_prefix}Remote Deployment Error: {error}", "red")
        _logger.debug("Full error details: %s", error, exc_info=True)

    else:
        # Handle the error as a generic exception
        handle_generic_error(error, context)
        return  # handle_generic_error already calls sys.exit

    sys.exit(1)


def handle_generic_error(error: Exception, context: Optional[str] = None) -> NoReturn:
    """
    Handle generic errors with user-friendly messages.

    Args:
        error: The exception that occurred
        context: Optional context about when the error occurred
    """
    error_prefix = f"[{context}] " if context else ""

    if isinstance(error, botocore.exceptions.NoCredentialsError):
        print_error_message(f"{error_prefix}AWS Credentials Error: No AWS credentials found", "red")
        print_error_message(
            "Please configure your AWS credentials using 'aws configure' or environment variables.", "yellow"
        )
        _logger.debug("Full error details: %s", error, exc_info=True)

    elif isinstance(error, botocore.exceptions.ClientError):
        error_code = error.response.get("Error", {}).get("Code", "Unknown")
        error_message = error.response.get("Error", {}).get("Message", str(error))
        print_error_message(f"{error_prefix}AWS Error ({error_code}): {error_message}", "red")

        # Provide specific guidance for common AWS errors
        if error_code == "AccessDenied":
            print_error_message("Please check your AWS permissions and IAM roles.", "yellow")
        elif error_code == "UnauthorizedOperation":
            print_error_message("Please check your AWS permissions for this operation.", "yellow")
        elif error_code in ["NoSuchBucket", "BucketNotFound"]:
            print_error_message("The specified S3 bucket was not found.", "yellow")
        elif error_code == "InvalidParameterValue":
            print_error_message("Please check the parameter values in your configuration.", "yellow")

        _logger.debug("Full error details: %s", error, exc_info=True)

    elif isinstance(error, FileNotFoundError):
        print_error_message(f"{error_prefix}File Not Found: {error.filename or 'Unknown file'}", "red")
        print_error_message("Please check that all required files exist and paths are correct.", "yellow")
        _logger.debug("Full error details: %s", error, exc_info=True)

    elif isinstance(error, PermissionError):
        print_error_message(f"{error_prefix}Permission Error: {error}", "red")
        print_error_message("Please check file and directory permissions.", "yellow")
        _logger.debug("Full error details: %s", error, exc_info=True)

    elif isinstance(error, KeyboardInterrupt):
        print_error_message("\nOperation cancelled by user.", "yellow")
        _logger.debug("Operation interrupted by user")

    else:
        # For truly unexpected errors, show a generic message but log the full details
        print_error_message(f"{error_prefix}Unexpected Error: {type(error).__name__}: {error}", "red")
        print_error_message("An unexpected error occurred. Please check the logs for more details.", "yellow")
        _logger.error("Unexpected error occurred", exc_info=True)

    sys.exit(1)


def safe_execute(context: str) -> Callable[[F], F]:
    """
    Decorator to safely execute functions with proper error handling.

    Args:
        context: Description of what operation is being performed

    Returns:
        Decorated function that handles errors gracefully
    """

    def decorator(func: F) -> F:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            try:
                return func(*args, **kwargs)
            except (
                InvalidPathError,
                InvalidManifestError,
                InvalidConfigurationError,
                ModuleDeploymentError,
                InvalidSessionError,
                RemoteDeploymentRuntimeError,
                SeedFarmerException,
            ) as e:
                handle_seedfarmer_error(e, context)
            except Exception as e:
                handle_generic_error(e, context)

        return wrapper  # type: ignore

    return decorator


def log_error_safely(logger: logging.Logger, error: Exception, message: str) -> None:
    """
    Log an error message without exposing sensitive stacktrace information to console output.

    Args:
        logger: Logger instance to use
        error: The exception that occurred
        message: User-friendly error message
    """
    # Log user-friendly message at error level (will show in console)
    logger.error(message)

    # Log full exception details only at debug level (hidden unless debug mode is on)
    logger.debug("Full error details: %s", error, exc_info=True)
