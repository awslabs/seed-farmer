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

import dataclasses
import enum


class EnvVarType(str, enum.Enum):
    PLAINTEXT = "PLAINTEXT"
    PARAMETER_STORE = "PARAMETER_STORE"
    SECRETS_MANAGER = "SECRETS_MANAGER"


@dataclasses.dataclass()
class EnvVar:
    """EnvVar dataclass

    This class is used to define environment variables made available inside of CodeBuild. Use of this
    class enables declaration of all environment variable types that CodeBuild supports.

    Parameters
    ----------
    value : string
        The value for the environment variable. The effect of this value varies depending on the type
        of environment variable created. See the AWS official documentation for usage information:
        https://docs.aws.amazon.com/codebuild/latest/userguide/build-spec-ref.html#build-spec.env.variables
        https://docs.aws.amazon.com/codebuild/latest/userguide/build-spec-ref.html#build-spec.env.parameter-store
        https://docs.aws.amazon.com/codebuild/latest/userguide/build-spec-ref.html#build-spec.env.secrets-manager
    type : EnvVarType
        The type of environment variable: PLAINTEXT, PARAMETER_STORE, or SECRETS_MANAGER. See the AWS
        official documentation for usage, by default PLAINTEXT
    """

    value: str
    type: EnvVarType = EnvVarType.PLAINTEXT
