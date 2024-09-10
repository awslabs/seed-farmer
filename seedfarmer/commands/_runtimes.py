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

from enum import Enum
from typing import Dict, Optional


class CuratedBuildImages:
    class ImageEnums(Enum):
        UBUNTU_STANDARD_6 = "aws/codebuild/standard:6.0"
        UBUNTU_STANDARD_7 = "aws/codebuild/standard:7.0"
        AL2_STANDARD_4 = "aws/codebuild/amazonlinux2-x86_64-standard:4.0"
        AL2_STANDARD_5 = "aws/codebuild/amazonlinux2-x86_64-standard:5.0"

    class ImageRuntimes(Enum):
        UBUNTU_STANDARD_6 = {"nodejs": "16", "python": "3.10", "java": "corretto17"}
        UBUNTU_STANDARD_7 = {"nodejs": "18", "python": "3.11", "java": "corretto21"}
        AL2_STANDARD_4 = {"nodejs": "16", "python": "3.9", "java": "corretto17"}
        AL2_STANDARD_5 = {"nodejs": "18", "python": "3.11", "java": "corretto21"}


def get_runtimes(codebuild_image: Optional[str]) -> Optional[Dict[str, str]]:
    image_vals = [cbi.value for cbi in CuratedBuildImages.ImageEnums]
    if codebuild_image in image_vals:
        cir_d = {cir.name: cir.value for cir in CuratedBuildImages.ImageRuntimes}
        k = CuratedBuildImages.ImageEnums(codebuild_image).name
        return cir_d[k]
    else:
        return None
