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

from typing import Callable, List, Optional

from click.testing import CliRunner


def _test_command(
    sub_command: Callable,
    options: List[str],
    exit_code: int,
    expected_output: Optional[str] = None,
    return_result: Optional[bool] = False,
    skip_eval:Optional[bool] = False,
):
    runner = CliRunner()
    command_output = runner.invoke(sub_command, options)
    print(command_output.exit_code)
    if not skip_eval:
        assert command_output.exit_code == exit_code
    else:
        print("skipping eval")

    if return_result:
        return command_output

    if expected_output:
        assert expected_output in command_output.output
