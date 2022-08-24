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
#
import json
import logging
import os
from typing import Any, Dict, List, Optional

import yaml
from jinja2 import Template

from seedfarmer import CLI_ROOT
from seedfarmer.utils import CfnSafeYamlLoader

_logger: logging.Logger = logging.getLogger(__name__)


def get_toolchain_template(
    project_name: str,
    principalARN: List[str],
    permissionsBoundaryARN: Optional[str] = None,
) -> Dict[Any, Any]:
    with open((os.path.join(CLI_ROOT, "resources/toolchain_role.template")), "r") as f:
        role = yaml.load(f, CfnSafeYamlLoader)
    if principalARN:
        role["Resources"]["ToolchainRole"]["Properties"]["AssumeRolePolicyDocument"]["Statement"][0]["Principal"][
            "AWS"
        ] = principalARN
    if permissionsBoundaryARN:
        role["Resources"]["ToolchainRole"]["Properties"]["PermissionsBoundary"] = permissionsBoundaryARN
    template = Template(json.dumps(role))
    t = template.render({"project_name": project_name})
    return dict(json.loads(t))


def get_deployment_template(
    toolchain_account_id: str, project_name: str, permissionsBoundaryARN: Optional[str] = None
) -> Dict[Any, Any]:
    with open((os.path.join(CLI_ROOT, "resources/deployment_role.template")), "r") as f:
        role = yaml.load(f, CfnSafeYamlLoader)
    if permissionsBoundaryARN:
        role["Resources"]["DeploymentRole"]["Properties"]["PermissionsBoundary"] = permissionsBoundaryARN
    template = Template(json.dumps(role))
    t = template.render({"toolchain_account_id": toolchain_account_id, "project_name": project_name})
    return dict(json.loads(t))


def write_template(template: Dict[Any, Any], name: str) -> None:
    loc = os.path.join(os.getcwd(), "templates")
    output = os.path.join(loc, name)
    _logger.info(f"Writing template to {output}")
    os.makedirs(loc, exist_ok=True)
    with open(output, "w") as outfile:
        yaml.dump(template, outfile)


def bootstrap_toolchain_account(
    project_name: str,
    principalARN: List[str],
    permissionsBoundaryARN: Optional[str] = None,
    synthesize: bool = False,
) -> Optional[Dict[Any, Any]]:
    template = get_toolchain_template(project_name, principalARN, permissionsBoundaryARN)
    _logger.debug((json.dumps(template, indent=4)))
    if not synthesize:
        # call the services to deploy
        pass
    else:
        write_template(template=template, name="toolchain_bootstrap.yaml")
    return template


def bootstrap_target_account(
    toolchain_account_id: str,
    project_name: str,
    permissionsBoundaryARN: Optional[str] = None,
    synthesize: bool = False,
) -> Optional[Dict[Any, Any]]:
    template = get_deployment_template(toolchain_account_id, project_name, permissionsBoundaryARN)
    _logger.debug((json.dumps(template, indent=4)))
    if not synthesize:
        # call the services to deploy
        pass
    else:
        write_template(template=template, name="target_bootstrap.yaml")
    return template
