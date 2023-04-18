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
import botocore
import pytest
from moto import mock_codebuild, mock_iam, mock_secretsmanager, mock_ssm, mock_sts
from seedfarmer.services._service_utils import boto3_client
from seedfarmer.services.session_manager import SessionManager
from seedfarmer.services import _service_utils

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
    session = boto3.Session()


@pytest.fixture(scope="function")
def sts_client(aws_credentials):
    with mock_sts():
        yield boto3_client(service_name="sts", session=None)


@pytest.fixture(scope="function")       
def session_manager(sts_client):
    SessionManager._instances={}
    SessionManager().get_or_create(
        project_name="test",
        region_name="us-east-1",
        toolchain_region="us-east-1",
        enable_reaper=False,
    )

@pytest.fixture(scope="function")
def secretsmanager_client(aws_credentials, session_manager):
    with mock_sts():
        yield boto3_client(service_name="secretsmanager", session=None)

@pytest.mark.parametrize("session", [None, boto3.Session()])
def test_utils_boto3_client(aws_credentials, session):
    _service_utils.boto3_client("s3", session)


@pytest.mark.parametrize("session", [None, boto3.Session()])
def test_utils_boto3_resource(aws_credentials, session):
    _service_utils.boto3_resource("s3", session)


@pytest.mark.parametrize("session", [None, boto3.Session()])
def test_utils_get_region(sts_client, session):
    assert _service_utils.get_region(session) == "us-east-1"


def test_utils_get_account_id(sts_client):
    assert _service_utils.get_account_id() == "123456789012"


# def test_utils_get_account_id_failed(sts_client, session):
#     with pytest.raises(botocore.exceptions.ClientError):
#         assert _service_utils.get_account_id(boto3.Session) == "123456789012"


@pytest.fixture(scope="function")
def iam_client(aws_credentials):
    with mock_iam():
        yield _service_utils.boto3_client(service_name="iam", session=None)


### Codebuild
@pytest.mark.service
def test_codebuild(session) -> None:
    import seedfarmer.services._codebuild as codebuild

    with mock_codebuild():
        codebuild.get_build_data(build_ids=["codebuild:12345"], session=session)
        codebuild.get_build_data(build_ids=["12345"], session=session)


### IAM
@pytest.mark.service
def test_iam(iam_client, session) -> None:
    import seedfarmer.services._iam as iam

    with mock_iam():
        iam.create_check_iam_role(
            project_name="test",
            deployment_name="test",
            group_name="test",
            module_name="test",
            trust_policy=None,
            role_name="test",
            permissions_boundary_arn="arn:aws:iam::aws:policy/AdministratorAccess",
            session=session,
        )
        r = iam.get_role(role_name="test", session=session)
        assert r["Role"]["RoleName"] == "test"
        iam.get_role(role_name="garbage", session=session)
        iam.attach_policy_to_role(
            role_name="test", policies=["arn:aws:iam::aws:policy/AdministratorAccess"], session=session
        )
        # Test tolerance if policy already attached..this is not a typo
        iam.attach_policy_to_role(
            role_name="test", policies=["arn:aws:iam::aws:policy/AdministratorAccess"], session=session
        )
        with pytest.raises(Exception):
            iam.attach_policy_to_role(role_name="test", policies=["blah"], session=session)

        iam.attach_inline_policy(
            role_name="test",
            policy_body='{"Version": "2012-10-17","Statement": [{"Effect": "Allow","Action": "*","Resource": "*"}]}',
            policy_name="testinline",
            session=session,
        )

        with pytest.raises(Exception):
            iam.attach_inline_policy(
                role_name="test", policy_body='{"blah":"Blah"}', policy_name="testinline", session=session
            )
        iam.detach_inline_policy_from_role(role_name="test", policy_name="testinline", session=session)
        with pytest.raises(Exception):
            iam.detach_inline_policy_from_role(role_name="test", policy_name="testinlinedoesnexist", session=session)
        iam.detach_policy_from_role(
            role_name="test", policy_arn="arn:aws:iam::aws:policy/AdministratorAccess", session=session
        )
        iam.detach_policy_from_role(
            role_name="test", policy_arn="arn:aws:iam::aws:policy/AdministratorAccess2", session=session
        )
        iam.delete_role(role_name="test", session=session)
        iam.delete_role(role_name="dontexist", session=session)


### SSM


@pytest.mark.service
def test_get_ssm_params(session) -> None:
    import seedfarmer.services._ssm as ssm

    with mock_ssm():
        ssm.put_parameter(name="/myapp/test/", obj={"Hey": "tsting"}, session=session)
        ssm.does_parameter_exist(name="/myapp/test/", session=session)
        ssm.does_parameter_exist(name="/garbage/", session=session)
        ssm.get_all_parameter_data_by_path(prefix="/myapp/", session=session)
        ssm.get_parameter_if_exists(name="/myapp/test/", session=session)
        ssm.get_parameter_if_exists(name="/garbage/", session=session)
        ssm.get_parameter(name="/myapp/test/", session=session)


@pytest.mark.service
def test_put_ssm_param(session) -> None:
    import seedfarmer.services._ssm as ssm

    with mock_ssm():
        ssm.put_parameter(name="/myapp/test/", obj={"Hey": "tsting"}, session=session)


@pytest.mark.service
def test_list_ssm_param(session) -> None:
    import seedfarmer.services._ssm as ssm

    with mock_ssm():
        ssm.put_parameter(name="/myapp/test/", obj={"Hey": "testing"}, session=session)
        ssm.list_parameters(prefix="/myapp/test/", session=session)
        ssm.list_parameters_with_filter(prefix="/myapp/", contains_string="test", session=session)


@pytest.mark.service
def test_delete_ssm_param(session) -> None:
    import seedfarmer.services._ssm as ssm

    with mock_ssm():
        ssm.delete_parameters(parameters=["/myapp", "/myapp/test/"], session=session)
        ssm.delete_parameters(
            parameters=[
                "/myapp",
                "/myapp/test1/",
                "/myapp/test2/",
                "/myapp/test3/",
                "/myapp/test4/",
                "/myapp/test5/",
                "/myapp/test6/",
                "/myapp/test7/",
                "/myapp/test8/",
                "/myapp/test9/",
            ],
            session=session,
        )


@pytest.mark.service
def test_get_ssm_metadata(session) -> None:
    import seedfarmer.services._ssm as ssm

    with mock_ssm():
        ssm.put_parameter(name="/myapp/test/", obj={"Hey": "testing"}, session=session)
        ssm.describe_parameter(name="/myapp/test/", session=session)


# ### SecretsManager
# @pytest.mark.service
# def test_secrets_manager(session_manager, mocker, secretsmanager_client)->None:
#     import seedfarmer.services._secrets_manager as sm
#    #mocker.patch("seedfarmer.services._secrets_manager.boto3_client", return_value=secretsmanager_client)
#     with mock_secretsmanager():
#         sm.get_secret_secrets_manager(name="test")


### Sessions Manager
##REF -- https://gist.github.com/k-bx/5861641

# @pytest.mark.service
# def test_get_params(aws_credentials)->None:
#     from seedfarmer.services.session_manager import SessionManager
#     session = SessionManager().get_or_create(
#         project_name="myapp",
#         account_id=os.environ["AWS_DEFAULT_REGION"],
#         region_name=os.environ["AWS_DEFAULT_REGION"]).get_deployment_session(
# )
