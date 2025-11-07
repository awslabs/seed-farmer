import os

import pytest
import yaml

from seedfarmer import config
from seedfarmer.commands import _cfn_seedkit as cfn_seedkit


@pytest.mark.commands
@pytest.mark.commands_seedkit
def test_synth_creates_file(mocker):
    """Test that synth creates a file with the expected content."""
    # Mock the template file
    template_content = {"Resources": {"TestResource": {"Type": "AWS::S3::Bucket"}}}

    # Mock open to return the template content
    mock_open = mocker.patch("builtins.open", mocker.mock_open(read_data=yaml.dump(template_content)))

    # Mock yaml.safe_load to return the template content
    mocker.patch("yaml.safe_load", return_value=template_content)

    # Mock create_output_dir to return our expected path
    output_dir = os.path.join(os.getcwd(), ".seedfarmer.out/seedkit-test123")
    mocker.patch("seedfarmer.utils.create_output_dir", return_value=output_dir)

    # Call the function
    result = cfn_seedkit.synth(deploy_id="test123")

    # Verify the result is the expected filename
    expected_filename = os.path.join(output_dir, config.SEEDKIT_YAML_FILENAME)
    assert expected_filename == result

    # Verify open was called with the correct paths
    mock_open.assert_any_call(config.SEEDKIT_TEMPLATE_PATH, encoding="utf-8")
    mock_open.assert_any_call(expected_filename, "w", encoding="utf-8")


@pytest.mark.commands
@pytest.mark.commands_seedkit
def test_synth_synthesize_only(mocker):
    """Test that synth with synthesize=True outputs to stdout and returns None."""
    # Mock the template file
    template_content = {"Resources": {"TestResource": {"Type": "AWS::S3::Bucket"}}}

    # Mock open to return the template content
    mock_open = mocker.patch("builtins.open", mocker.mock_open(read_data=yaml.dump(template_content)))

    # Mock yaml.safe_load to return the template content
    mocker.patch("yaml.safe_load", return_value=template_content)

    # Mock yaml.dump to return a string
    mocker.patch("yaml.dump", return_value="yaml content")

    # Mock sys.stdout.write
    mock_stdout = mocker.patch("sys.stdout.write")

    # Call the function
    result = cfn_seedkit.synth(deploy_id="test123", synthesize=True)

    # Verify the result is None
    assert result is None

    # Verify stdout.write was called with the template content
    mock_stdout.assert_called_once_with("yaml content")

    # Verify open was only called once (for reading the template)
    assert mock_open.call_count == 1


@pytest.mark.commands
@pytest.mark.commands_seedkit
def test_synth_with_kwargs(mocker):
    """Test that synth accepts and ignores additional kwargs."""
    # Mock the template file
    template_content = {"Resources": {"TestResource": {"Type": "AWS::S3::Bucket"}}}

    # Mock open to return the template content
    mocker.patch("builtins.open", mocker.mock_open(read_data=yaml.dump(template_content)))

    # Mock yaml.safe_load to return the template content
    mocker.patch("yaml.safe_load", return_value=template_content)

    # Mock create_output_dir to return our expected path
    output_dir = os.path.join(os.getcwd(), ".seedfarmer.out/seedkit-test123")
    mocker.patch("seedfarmer.utils.create_output_dir", return_value=output_dir)

    # Call the function with additional kwargs
    result = cfn_seedkit.synth(deploy_id="test123", extra_param="value", another_param=123)

    # Verify the result is the expected filename
    expected_filename = os.path.join(output_dir, config.SEEDKIT_YAML_FILENAME)
    assert expected_filename == result
