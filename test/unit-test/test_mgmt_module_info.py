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

    # Ensure module stack/role names preserve project case for SCP/prefix-sensitive environments.
    mocker.patch.object(type(mi.config), "PROJECT", new_callable=mocker.PropertyMock, return_value="Falcon")

    stack_name, role_name = mi.get_module_stack_names(
        deployment_name="myapp", group_name="test", module_name="mymodule", session=session
    )

    assert stack_name.startswith("Falcon-myapp-test-mymodule")
    assert role_name.startswith("Falcon-myapp-test-mymodule")


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
