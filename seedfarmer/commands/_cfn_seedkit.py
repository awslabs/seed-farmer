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
import sys
from typing import Any, Dict, Optional

import yaml

from seedfarmer import config
from seedfarmer.utils import create_output_dir

_logger: logging.Logger = logging.getLogger(__name__)

# FILENAME = "template.yaml"
# RESOURCES_FILENAME = os.path.join(CLI_ROOT, "resources", FILENAME)


def synth(
    *,
    deploy_id: str,
    synthesize: bool = False,
    **kwargs: Dict[str, Any],
) -> Optional[str]:
    out_dir = create_output_dir(f"seedkit-{deploy_id}")
    output_filename = os.path.join(out_dir, config.SEEDKIT_YAML_FILENAME)
    kwargs = {} if kwargs is None else kwargs

    _logger.debug("Reading %s", config.SEEDKIT_TEMPLATE_PATH)

    with open(config.SEEDKIT_TEMPLATE_PATH) as f:
        template = yaml.safe_load(f)

    if not synthesize:
        _logger.debug("Writing %s", output_filename)
        os.makedirs(os.path.dirname(output_filename), exist_ok=True)
        with open(output_filename, "w") as file:
            file.write(yaml.dump(template))
        return output_filename
    else:
        sys.stdout.write(yaml.dump(template))
        return None
