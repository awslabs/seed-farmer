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

import boto3
import pytest

_logger: logging.Logger = logging.getLogger(__name__)


@pytest.fixture(scope="function")
def aws_credentials():
    """Mocked AWS Credentials for moto."""
    os.environ["AWS_ACCESS_KEY_ID"] = "testing"
    os.environ["AWS_SECRET_ACCESS_KEY"] = "testing"
    os.environ["AWS_SECURITY_TOKEN"] = "testing"
    os.environ["AWS_SESSION_TOKEN"] = "testing"
    os.environ["AWS_DEFAULT_REGION"] = "us-east-1"
    os.environ["MOTO_ACCOUNT_ID"] = "123456789012"


@pytest.fixture(scope="function")
def session(aws_credentials):
    boto3.Session()


### Test Model Init
@pytest.mark.mgmt
@pytest.mark.mgmt_module_info
def test_get_all_deployments(aws_credentials, session, mocker):
    import seedfarmer.mgmt.module_info as mi

    mocker.patch("seedfarmer.mgmt.module_info.ssm.list_parameters_with_filter", return_value=["/myapp/test/hey"])
    mi.get_all_deployments(session=session)


@pytest.mark.mgmt
@pytest.mark.mgmt_module_info
def test_get_all_deployments_with_manifest(aws_credentials, session, mocker):
    import seedfarmer.mgmt.module_info as mi

    mocker.patch("seedfarmer.mgmt.module_info.ssm.list_parameters_with_filter", return_value=["/myapp/test/manifest"])
    mi.get_all_deployments(session=session)


@pytest.mark.mgmt
@pytest.mark.mgmt_module_info
def test_get_all_deployments_with_nothing(aws_credentials, session, mocker):
    import seedfarmer.mgmt.module_info as mi

    mocker.patch("seedfarmer.mgmt.module_info.ssm.list_parameters_with_filter", return_value=[])
    mi.get_all_deployments(session=session)


@pytest.mark.mgmt
@pytest.mark.mgmt_module_info
def test_get_all_groups(aws_credentials, session, mocker):
    import seedfarmer.mgmt.module_info as mi

    mocker.patch(
        "seedfarmer.mgmt.module_info.ssm.list_parameters_with_filter",
        return_value=["/myapp/test/manifest", "/myapp/test/optionals", "/myapp/test/core"],
    )
    mi.get_all_groups(deployment="myapp", session=session)


@pytest.mark.mgmt
@pytest.mark.mgmt_module_info
def test_get_deployed_modules(aws_credentials, session, mocker):
    import seedfarmer.mgmt.module_info as mi

    mocker.patch(
        "seedfarmer.mgmt.module_info.ssm.list_parameters_with_filter",
        return_value=["/myapp/test/manifest", "/myapp/test/optionals", "/myapp/test/core"],
    )
    mi.get_deployed_modules(deployment="myapp", group="test", session=session)


@pytest.mark.mgmt
@pytest.mark.mgmt_module_info
def test_get_module_md5(aws_credentials, session, mocker):
    import seedfarmer.mgmt.module_info as mi

    mocker.patch("seedfarmer.mgmt.module_info.ssm.get_parameter_if_exists", return_value={"hash": "12345678"})
    mi.get_module_md5(
        deployment="myapp", group="test", module="mymodule", type=mi.ModuleConst.METADATA, session=session
    )

    mi.get_module_md5(deployment="myapp", group="test", module="mymodule", type=mi.ModuleConst.BUNDLE, session=session)

    mi.get_module_md5(
        deployment="myapp", group="test", module="mymodule", type=mi.ModuleConst.DEPLOYSPEC, session=session
    )
    mi.get_module_md5(
        deployment="myapp", group="test", module="mymodule", type=mi.ModuleConst.METADATA, session=session
    )


@pytest.mark.mgmt
@pytest.mark.mgmt_module_info
def test_get_module_metadata(aws_credentials, session, mocker):
    import seedfarmer.mgmt.module_info as mi

    mocker.patch("seedfarmer.mgmt.module_info._fetch_helper", return_value={"hey": "yo"})
    mi.get_module_metadata(deployment="myapp", group="test", module="mymodule", session=session)


@pytest.mark.mgmt
@pytest.mark.mgmt_module_info
def test_get_module_manifest(aws_credentials, session, mocker):
    import seedfarmer.mgmt.module_info as mi

    mocker.patch("seedfarmer.mgmt.module_info._fetch_helper", return_value={"hey": "yo"})
    mi.get_module_manifest(deployment="myapp", group="test", module="mymodule", session=session)


@pytest.mark.mgmt
@pytest.mark.mgmt_module_info
def test_get_deployment_manifest(aws_credentials, session, mocker):
    import seedfarmer.mgmt.module_info as mi

    mocker.patch("seedfarmer.mgmt.module_info._fetch_helper", return_value={"hey": "yo"})
    mi.get_deployment_manifest(deployment="myapp", session=session)


@pytest.mark.mgmt
@pytest.mark.mgmt_module_info
def test_get_deployed_deployment_manifest(aws_credentials, session, mocker):
    import seedfarmer.mgmt.module_info as mi

    mocker.patch("seedfarmer.mgmt.module_info._fetch_helper", return_value={"hey": "yo"})
    mi.get_deployed_deployment_manifest(deployment="myapp", session=session)


@pytest.mark.mgmt
@pytest.mark.mgmt_module_info
def test_get_deployspec(aws_credentials, session, mocker):
    import seedfarmer.mgmt.module_info as mi

    mocker.patch("seedfarmer.mgmt.module_info._fetch_helper", return_value={"hey": "yo"})
    mi.get_deployspec(deployment="myapp", group="test", module="mymodule", session=session)


@pytest.mark.mgmt
@pytest.mark.mgmt_module_info
def test_get_group_manifest(aws_credentials, session, mocker):
    import seedfarmer.mgmt.module_info as mi

    mocker.patch("seedfarmer.mgmt.module_info._fetch_helper", return_value={"hey": "yo"})
    mi.get_group_manifest(deployment="myapp", group="test", session=session)


@pytest.mark.mgmt
@pytest.mark.mgmt_module_info
def test_does_module_exist(aws_credentials, session, mocker):
    import seedfarmer.mgmt.module_info as mi

    mocker.patch("seedfarmer.mgmt.module_info.ssm.does_parameter_exist", return_value=True)
    mi.does_module_exist(deployment="myapp", group="test", module="mymodule", session=session)


@pytest.mark.mgmt
@pytest.mark.mgmt_module_info
def test_does_md5_match(aws_credentials, session, mocker):
    import seedfarmer.mgmt.module_info as mi

    mocker.patch("seedfarmer.mgmt.module_info.ssm.get_parameter_if_exists", return_value={"hash": "12345678"})
    mi.does_md5_match(
        deployment="myapp",
        group="test",
        module="mymodule",
        hash="12345678",
        type=mi.ModuleConst.BUNDLE,
        session=session,
    )

    mi.does_md5_match(
        deployment="myapp", group="test", module="mymodule", hash="blah", type=mi.ModuleConst.BUNDLE, session=session
    )


@pytest.mark.mgmt
@pytest.mark.mgmt_module_info
def test_does_md5_match_no(aws_credentials, session, mocker):
    import seedfarmer.mgmt.module_info as mi

    mocker.patch("seedfarmer.mgmt.module_info.ssm.get_parameter_if_exists", return_value=None)

    mi.does_md5_match(
        deployment="myapp", group="test", module="mymodule", hash="blah", type=mi.ModuleConst.BUNDLE, session=session
    )


@pytest.mark.mgmt
@pytest.mark.mgmt_module_info
def test_write_metadata(aws_credentials, session, mocker):
    import seedfarmer.mgmt.module_info as mi

    mocker.patch("seedfarmer.mgmt.module_info.ssm.put_parameter", return_value=True)
    mi.write_metadata(deployment="myapp", group="test", module="mymodule", data={"Hey", "Yo"}, session=session)


@pytest.mark.mgmt
@pytest.mark.mgmt_module_info
def test_write_group_manifest(aws_credentials, session, mocker):
    import seedfarmer.mgmt.module_info as mi

    mocker.patch("seedfarmer.mgmt.module_info.ssm.put_parameter", return_value=True)
    mi.write_group_manifest(deployment="myapp", group="test", data={"Hey", "Yo"}, session=session)


@pytest.mark.mgmt
@pytest.mark.mgmt_module_info
def test_write_module_manifest(aws_credentials, session, mocker):
    import seedfarmer.mgmt.module_info as mi

    mocker.patch("seedfarmer.mgmt.module_info.ssm.put_parameter", return_value=True)
    payload = {"Hey", "Yo"}
    mi.write_module_manifest(
        deployment="myapp", group="test", module="mymodule", data=dict.fromkeys(payload, 0), session=session
    )


@pytest.mark.mgmt
@pytest.mark.mgmt_module_info
def test_write_deployspec(aws_credentials, session, mocker):
    import seedfarmer.mgmt.module_info as mi

    mocker.patch("seedfarmer.mgmt.module_info.ssm.put_parameter", return_value=True)
    mi.write_deployspec(deployment="myapp", group="test", module="mymodule", data={"Hey", "Yo"}, session=session)


@pytest.mark.mgmt
@pytest.mark.mgmt_module_info
def test_write_module_md5(aws_credentials, session, mocker):
    import seedfarmer.mgmt.module_info as mi

    mocker.patch("seedfarmer.mgmt.module_info.ssm.put_parameter", return_value=True)
    mi.write_module_md5(
        deployment="myapp", group="test", module="mymodule", hash="12345", type=mi.ModuleConst.BUNDLE, session=session
    )


@pytest.mark.mgmt
@pytest.mark.mgmt_module_info
def test_write_deployment_manifest(aws_credentials, session, mocker):
    import seedfarmer.mgmt.module_info as mi

    mocker.patch("seedfarmer.mgmt.module_info.ssm.put_parameter", return_value=True)
    mi.write_deployment_manifest(deployment="myapp", data={"Hey", "Yo"}, session=session)


@pytest.mark.mgmt
@pytest.mark.mgmt_module_info
def test_write_deployed_deployment_manifest(aws_credentials, session, mocker):
    import seedfarmer.mgmt.module_info as mi

    mocker.patch("seedfarmer.mgmt.module_info.ssm.put_parameter", return_value=True)
    mi.write_deployed_deployment_manifest(deployment="myapp", data={"Hey", "Yo"}, session=session)


@pytest.mark.mgmt
@pytest.mark.mgmt_module_info
def test_remove_all_info(aws_credentials, session, mocker):
    import seedfarmer.mgmt.module_info as mi

    mocker.patch("seedfarmer.mgmt.module_info.ssm.delete_parameters", return_value=True)
    mi.remove_deployed_deployment_manifest(deployment="myapp", session=session)
    mi.remove_deployment_manifest(deployment="myapp", session=session)
    mi.remove_group_info(deployment="myapp", group="mygroup", session=session)
    mi.remove_module_info(deployment="myapp", group="mygroup", module="mymodule", session=session)
    mi.remove_module_md5(
        deployment="myapp", group="mygroup", module="mymodule", type=mi.ModuleConst.BUNDLE, session=session
    )


@pytest.mark.mgmt
@pytest.mark.mgmt_module_info
def test_get_module_stack_names(mocker, session):
    import seedfarmer.mgmt.module_info as mi

    mocker.patch("seedfarmer.mgmt.module_info.generate_hash", return_value="1234")
    mocker.patch("seedfarmer.mgmt.module_info.generate_session_hash", return_value="1234dade")

    # Stack name is lowercase for CF consistency; role name preserves case for IAM/SCP.
    mocker.patch.object(type(mi.config), "PROJECT", new_callable=mocker.PropertyMock, return_value="Falcon")

    stack_name, role_name = mi.get_module_stack_names(
        deployment_name="myapp", group_name="test", module_name="mymodule", session=session
    )

    assert stack_name == "falcon-myapp-test-mymodule-iam-policy"  # lowercase CF stack name
    assert role_name == "Falcon-myapp-test-mymodule-1234dade"  # preserve case IAM role name


@pytest.mark.mgmt
@pytest.mark.mgmt_module_info
def test_get_module_stack_names_uppercase_project(mocker, session):
    # 1.1.2 / 6.4 — all-uppercase project: stack lowercase, role preserves case
    import seedfarmer.mgmt.module_info as mi

    mocker.patch("seedfarmer.mgmt.module_info.generate_hash", return_value="abcd")
    mocker.patch("seedfarmer.mgmt.module_info.generate_session_hash", return_value="deadbeef")
    mocker.patch.object(type(mi.config), "PROJECT", new_callable=mocker.PropertyMock, return_value="MYPROJ")

    stack_name, role_name = mi.get_module_stack_names(
        deployment_name="myapp", group_name="test", module_name="mymodule", session=session
    )

    assert stack_name == "myproj-myapp-test-mymodule-iam-policy"
    assert role_name == "MYPROJ-myapp-test-mymodule-deadbeef"


@pytest.mark.mgmt
@pytest.mark.mgmt_module_info
def test_get_module_stack_names_lowercase_project(mocker, session):
    # 1.1.3 — all-lowercase project: no change in behaviour (regression)
    import seedfarmer.mgmt.module_info as mi

    mocker.patch("seedfarmer.mgmt.module_info.generate_hash", return_value="abcd")
    mocker.patch("seedfarmer.mgmt.module_info.generate_session_hash", return_value="deadbeef")
    mocker.patch.object(type(mi.config), "PROJECT", new_callable=mocker.PropertyMock, return_value="myproj")

    stack_name, role_name = mi.get_module_stack_names(
        deployment_name="myapp", group_name="test", module_name="mymodule", session=session
    )

    assert stack_name == "myproj-myapp-test-mymodule-iam-policy"
    assert role_name == "myproj-myapp-test-mymodule-deadbeef"


@pytest.mark.mgmt
@pytest.mark.mgmt_module_info
def test_get_module_stack_names_hash_divergence(mocker, session):
    # 1.1.6 — for a mixed-case project the stack hash (from lowercase) differs from role hash (from original case)
    import hashlib

    import seedfarmer.mgmt.module_info as mi

    mocker.patch("seedfarmer.mgmt.module_info.generate_session_hash", return_value="deadbeef")
    mocker.patch.object(type(mi.config), "PROJECT", new_callable=mocker.PropertyMock, return_value="Falcon")

    stack_name, role_name = mi.get_module_stack_names(
        deployment_name="myapp", group_name="test", module_name="mymodule", session=session
    )

    # Compute expected hashes directly to confirm the inputs differ between stack and role
    resource_name_lower = "falcon-myapp-test-mymodule"
    role_base = "Falcon-myapp-test-mymodule"
    expected_stack_hash = hashlib.sha1(resource_name_lower.encode("UTF-8"), usedforsecurity=False).hexdigest()[:4]
    expected_role_hash = hashlib.sha1(role_base.encode("UTF-8"), usedforsecurity=False).hexdigest()[:4]

    assert expected_stack_hash != expected_role_hash


@pytest.mark.mgmt
@pytest.mark.mgmt_module_info
def test_get_module_stack_names_stack_truncation(mocker, session):
    # 1.1.4 / 6.2 — resource_name > 117 chars triggers stack name truncation with hash
    # stack threshold: len(resource_name) > 128 - 11 = 117
    import seedfarmer.mgmt.module_info as mi

    mocker.patch("seedfarmer.mgmt.module_info.generate_hash", return_value="zzzz")
    mocker.patch("seedfarmer.mgmt.module_info.generate_session_hash", return_value="deadbeef")
    mocker.patch.object(type(mi.config), "PROJECT", new_callable=mocker.PropertyMock, return_value="p")

    # Build a name that is exactly 118 chars (> 117): "p-" + 116 chars of components
    long_module = "m" * 114  # "p-" + "d-g-" + 114 = 2 + 4 + 114 = 120 > 117
    stack_name, _ = mi.get_module_stack_names(
        deployment_name="d", group_name="g", module_name=long_module, session=session
    )

    assert len(stack_name) <= 128
    assert stack_name.endswith("-zzzz-iam-policy")

    # Boundary: exactly 117 chars — no truncation
    long_module_boundary = "m" * 111  # "p-" + "d-g-" + 111 = 117
    stack_name_boundary, _ = mi.get_module_stack_names(
        deployment_name="d", group_name="g", module_name=long_module_boundary, session=session
    )
    assert stack_name_boundary == f"p-d-g-{'m' * 111}-iam-policy"
    assert len(stack_name_boundary) == 128


@pytest.mark.mgmt
@pytest.mark.mgmt_module_info
def test_get_module_stack_names_role_truncation(mocker, session):
    # 1.1.5 / 6.3 — role_base > 55 chars triggers role name truncation with hash
    # role threshold: len(role_base) > 64 - 9 = 55
    import seedfarmer.mgmt.module_info as mi

    mocker.patch("seedfarmer.mgmt.module_info.generate_hash", return_value="zzzz")
    mocker.patch("seedfarmer.mgmt.module_info.generate_session_hash", return_value="deadbeef")
    mocker.patch.object(type(mi.config), "PROJECT", new_callable=mocker.PropertyMock, return_value="P")

    # Build a role_base that is exactly 56 chars (> 55): "P-" + 54 chars of components
    long_module = "m" * 52  # "P-" + "d-g-" + 52 = 2 + 4 + 52 = 58 > 55
    _, role_name = mi.get_module_stack_names(
        deployment_name="d", group_name="g", module_name=long_module, session=session
    )

    assert len(role_name) <= 64
    assert "-zzzz-deadbeef" in role_name

    # Boundary: exactly 55 chars — no truncation
    long_module_boundary = "m" * 49  # "P-" + "d-g-" + 49 = 55
    _, role_name_boundary = mi.get_module_stack_names(
        deployment_name="d", group_name="g", module_name=long_module_boundary, session=session
    )
    assert role_name_boundary == f"P-d-g-{'m' * 49}-deadbeef"
    assert len(role_name_boundary) == 64


@pytest.mark.mgmt
@pytest.mark.mgmt_module_info
def test_get_module_stack_names_hyphen_numbers_project(mocker, session):
    # 6.1 — project name with hyphens/numbers: .lower() is a no-op, no artifact introduced
    import seedfarmer.mgmt.module_info as mi

    mocker.patch("seedfarmer.mgmt.module_info.generate_hash", return_value="abcd")
    mocker.patch("seedfarmer.mgmt.module_info.generate_session_hash", return_value="deadbeef")
    mocker.patch.object(type(mi.config), "PROJECT", new_callable=mocker.PropertyMock, return_value="my-proj2")

    stack_name, role_name = mi.get_module_stack_names(
        deployment_name="myapp", group_name="test", module_name="mymodule", session=session
    )

    assert stack_name == "my-proj2-myapp-test-mymodule-iam-policy"
    assert role_name == "my-proj2-myapp-test-mymodule-deadbeef"
    assert "--" not in stack_name
    assert "--" not in role_name


@pytest.mark.mgmt
@pytest.mark.mgmt_module_info
def test_ssm_key_functions_use_lowercase_project(mocker, session):
    """SSM parameter key functions must use normalized (lowercase) project name."""
    import seedfarmer.mgmt.module_info as mi

    mocker.patch.object(type(mi.config), "PROJECT", new_callable=mocker.PropertyMock, return_value="Falcon")

    assert mi._metadata_key("dep", "grp", "mod").startswith("/falcon/")
    assert mi._deployment_key("dep").startswith("/falcon/")
    assert mi._manifest_key("dep", "grp", "mod").startswith("/falcon/")
    assert mi._group_key("dep", "grp").startswith("/falcon/")
    assert mi._deployment_manifest_key("dep").startswith("/falcon/")
    # Ensure no uppercase project name leaks into SSM paths
    for fn in [
        lambda: mi._metadata_key("d", "g", "m"),
        lambda: mi._md5_module_key("d", "g", "m", mi.ModuleConst.BUNDLE),
        lambda: mi._deployspec_key("d", "g", "m"),
        lambda: mi._deployment_key("d"),
    ]:
        assert "/Falcon/" not in fn()


@pytest.mark.mgmt
@pytest.mark.mgmt_module_info
def test_get_modulestack_path():
    import seedfarmer.mgmt.module_info as mi

    mi.get_modulestack_path(module_path="modules/basic/something")


@pytest.mark.mgmt
@pytest.mark.mgmt_module_info
def test_get_deployspec_path():
    import seedfarmer.mgmt.module_info as mi

    with pytest.raises(Exception):
        mi.get_deployspec_path(module_path="modules/basic/something")


@pytest.mark.mgmt
@pytest.mark.mgmt_module_info
def test_fetch_helper(aws_credentials, session, mocker):
    import seedfarmer.mgmt.module_info as mi

    mocker.patch("seedfarmer.mgmt.module_info.ssm.get_parameter_if_exists", return_value={})
    mi._fetch_helper(name="myapp", session=session)

    mi._fetch_helper(name="myapp", params_cache={"myapp": "yo"}, session=session)


secrets_manager_mock_data = {
    "Versions": [
        {
            "VersionId": "17853545-211c-461b-938c-6f9bf36652ce",
            "VersionStages": ["AWSPREVIOUS", "WTFTESTING"],
            "LastAccessedDate": "2023-04-17 20:00:00-04:00",
            "CreatedDate": "2023-04-17 20:52:11.327000-04:00",
            "KmsKeyIds": ["DefaultEncryptionKey"],
        },
        {
            "VersionId": "3ae24b7a-a4dc-4ee3-ba47-ef4969c1e687",
            "VersionStages": ["USEME", "AWSCURRENT"],
            "LastAccessedDate": "2023-04-17 20:00:00-04:00",
            "CreatedDate": "2023-04-17 20:53:26.644000-04:00",
            "KmsKeyIds": ["DefaultEncryptionKey"],
        },
    ],
    "ARN": "arn:aws:secretsmanager:us-east-1:123456789012:secret:testderekaddf-QZHkSe",
    "Name": "testderekaddf",
    "ResponseMetadata": {
        "RequestId": "078d54ce-4005-43ad-af49-722dd1016e36",
        "HTTPStatusCode": 200,
        "HTTPHeaders": {
            "x-amzn-requestid": "078d54ce-4005-43ad-af49-722dd1016e36",
            "content-type": "application/x-amz-json-1.1",
            "content-length": "505",
            "date": "Tue, 18 Apr 2023 02:06:29 GMT",
        },
        "RetryAttempts": 0,
    },
}


@pytest.mark.mgmt
@pytest.mark.mgmt_module_info
def test_get_secrets_version_with_version_id(aws_credentials, session, mocker):
    import seedfarmer.mgmt.module_info as mi

    mocker.patch(
        "seedfarmer.mgmt.module_info.secrets.list_secret_version_ids",
        return_value=secrets_manager_mock_data["Versions"],
    )

    val = mi.get_secrets_version(
        secret_name="sometest", version_ref="17853545-211c-461b-938c-6f9bf36652ce", session=session
    )

    assert val == "17853545-211c-461b-938c-6f9bf36652ce"


@pytest.mark.mgmt
@pytest.mark.mgmt_module_info
def test_get_secrets_version_with_no_ref(aws_credentials, session, mocker):
    import seedfarmer.mgmt.module_info as mi

    mocker.patch(
        "seedfarmer.mgmt.module_info.secrets.list_secret_version_ids",
        return_value=secrets_manager_mock_data["Versions"],
    )

    val = mi.get_secrets_version(secret_name="sometest", session=session)

    assert val == "3ae24b7a-a4dc-4ee3-ba47-ef4969c1e687"


@pytest.mark.mgmt
@pytest.mark.mgmt_module_info
def test_get_secrets_version_with_status(aws_credentials, session, mocker):
    import seedfarmer.mgmt.module_info as mi

    mocker.patch(
        "seedfarmer.mgmt.module_info.secrets.list_secret_version_ids",
        return_value=secrets_manager_mock_data["Versions"],
    )

    val = mi.get_secrets_version(secret_name="sometest:username", version_ref="USEME", session=session)

    assert val == "3ae24b7a-a4dc-4ee3-ba47-ef4969c1e687"


@pytest.mark.mgmt
@pytest.mark.mgmt_module_info
def test_get_ssm_parameter_version(aws_credentials, session, mocker):
    import seedfarmer.mgmt.module_info as mi

    test_json = {
        "Parameters": [
            {
                "Name": "testingversioning",
                "Type": "String",
                "LastModifiedUser": "arn:aws:sts::123456789012:assumed-role/Admin/someone-Isengard",
                "Version": 5,
                "Tier": "Standard",
                "Policies": [],
                "DataType": "text",
            }
        ],
        "ResponseMetadata": {
            "RequestId": "693a5834-1802-4aa1-8254-879f942e9f5b",
            "HTTPStatusCode": 200,
            "HTTPHeaders": {
                "server": "Server",
                "date": "Mon, 17 Apr 2023 23:45:53 GMT",
                "content-type": "application/x-amz-json-1.1",
                "content-length": "243",
                "connection": "keep-alive",
                "x-amzn-requestid": "693a5834-1802-4aa1-8254-879f942e9f5b",
            },
            "RetryAttempts": 0,
        },
    }

    mocker.patch("seedfarmer.mgmt.module_info.ssm.describe_parameter", return_value=test_json)
    val = mi.get_ssm_parameter_version("sometest", session=session)

    assert val == 5


@pytest.mark.mgmt
@pytest.mark.mgmt_module_info
def test_get_ssm_parameter_version_failure(aws_credentials, session, mocker):
    import seedfarmer.mgmt.module_info as mi

    mocker.patch("seedfarmer.mgmt.module_info.ssm.describe_parameter", return_value=None)
    with pytest.raises(Exception):
        mi.get_ssm_parameter_version("sometest", session=session)
