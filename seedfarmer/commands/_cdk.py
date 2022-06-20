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

from typing import List, Tuple

from aws_codeseeder import create_output_dir
from aws_codeseeder.services import get_account_id, get_region
from executor import execute


def _get_cdk_toolkit_names(deployment_name: str) -> Tuple[str, str]:
    return f"{deployment_name}-cdk-toolkit", f"{deployment_name}-cdk-toolkit-{get_region()}"


def get_app_argument(app_filename: str, args: List[str]) -> str:
    args_str: str = " ".join(args)
    return f'--app "python {app_filename} {args_str}"'


def get_output_argument(module_name: str) -> str:
    path: str = create_output_dir(module_name)
    return f"--output {path}"


def deploy(deployment_name: str, module_name: str, app_filename: str, args: List[str]) -> None:
    cdk_toolkit_stack_name = _get_cdk_toolkit_names(deployment_name)
    command: str = (
        "cdk deploy --require-approval never --progress events "
        f"--toolkit-stack-name {cdk_toolkit_stack_name} "
        f"{get_app_argument(app_filename, args)} "
        f"{get_output_argument(module_name)}"
    )
    execute(command=command)


def destroy(deployment_name: str, module_name: str, app_filename: str, args: List[str]) -> None:
    cdk_toolkit_stack_name = _get_cdk_toolkit_names(deployment_name)
    command: str = (
        "cdk destroy --force "
        f"--toolkit-stack-name {cdk_toolkit_stack_name}  "
        f"{get_app_argument(app_filename, args)} "
        f"{get_output_argument(module_name)}"
    )
    execute(command=command)


def deploy_toolkit(deployment_name: str) -> None:
    cdk_toolkit_stack_name, cdk_toolkit_bucket_name = _get_cdk_toolkit_names(deployment_name)
    command: str = (
        f"cdk bootstrap --toolkit-bucket-name {cdk_toolkit_bucket_name} "
        f"--toolkit-stack-name {cdk_toolkit_stack_name} "
        f"{get_output_argument('cdk-toolkit')} "
        f"aws://{get_account_id()}/{get_region()}"
    )
    execute(command=command)
