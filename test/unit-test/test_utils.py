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
import mock_data.mock_deployment_manifest_huge as mock
import os 
import pytest
import seedfarmer.errors
import seedfarmer.utils as utils

_logger: logging.Logger = logging.getLogger(__name__)


@pytest.fixture(scope="function")
def env_params():
    os.environ["DEP_NAME"] = "testing"
    os.environ["REGION"] = "us-east-1"
    os.environ["ACCOUNT_ID"] = "123456789012"


@pytest.mark.utils_test
def test_utils():
    import seedfarmer.utils as utils

    hash = utils.generate_hash(string="test", length=8)
    assert hash == "a94a8fe5"

    utils.generate_codebuild_url(account_id="123456789012", region="us-east-1", codebuild_id="XXXXXX")
    utils.generate_codebuild_url(account_id=None, region=None, codebuild_id=None)

    c_case = utils.upper_snake_case("camelCase")
    assert c_case == "CAMEL_CASE"
    cap_case = utils.upper_snake_case("CapitalCase")
    assert cap_case == "CAPITAL_CASE"
    pascal_case = utils.upper_snake_case("Pascal_Case")
    assert pascal_case == "PASCAL_CASE"
    # session_hash = utils.generate_session_hash()


@pytest.mark.utils_test
def test_validate_module_dependencies(env_params):
    replaced = utils.batch_replace_env(mock.deployment_manifest_batch_replace)
    assert replaced["name"] == "testing"
    assert replaced["toolchain_region"] == "us-east-1"
    assert replaced["target_account_mappings"][0]["account_id"] == '123456789012'
    

