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
import tempfile
import zipfile
from pathlib import Path
from unittest.mock import patch

import pytest

import seedfarmer.mgmt.bundle as bundle

_logger: logging.Logger = logging.getLogger(__name__)


@pytest.fixture
def temp_dir():
    """Create a temporary directory for testing."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        yield tmp_dir


@pytest.fixture
def sample_files_structure(temp_dir):
    """Create a sample file structure for testing."""
    # Create regular files
    regular_file = Path(temp_dir) / "regular.txt"
    regular_file.write_text("regular content")

    # Create hidden file (allowed)
    python_version = Path(temp_dir) / ".python-version"
    python_version.write_text("3.11.0")

    # Create hidden file (not allowed)
    hidden_file = Path(temp_dir) / ".hidden"
    hidden_file.write_text("hidden content")

    # Create ignored directory structure
    ignored_dir = Path(temp_dir) / "build"
    ignored_dir.mkdir()
    ignored_file = ignored_dir / "ignored.txt"
    ignored_file.write_text("ignored content")

    # Create subdirectory with files
    sub_dir = Path(temp_dir) / "subdir"
    sub_dir.mkdir()
    sub_file = sub_dir / "sub.txt"
    sub_file.write_text("sub content")

    # Create nested hidden file
    nested_hidden = sub_dir / ".python-version"
    nested_hidden.write_text("3.10.0")

    return {
        "temp_dir": temp_dir,
        "regular_file": str(regular_file),
        "python_version": str(python_version),
        "hidden_file": str(hidden_file),
        "ignored_file": str(ignored_file),
        "sub_file": str(sub_file),
        "nested_hidden": str(nested_hidden),
    }


@pytest.mark.mgmt
@pytest.mark.mgmt_bundle
def test_is_valid_image_file_regular_file():
    """Test _is_valid_image_file with regular files."""
    assert bundle._is_valid_image_file("/path/to/regular.txt") is True
    assert bundle._is_valid_image_file("/path/to/script.py") is True


@pytest.mark.mgmt
@pytest.mark.mgmt_bundle
def test_is_valid_image_file_ignored_paths():
    """Test _is_valid_image_file with ignored paths."""
    assert bundle._is_valid_image_file("/path/build/file.txt") is False
    assert bundle._is_valid_image_file("/path/.mypy_cache/file.txt") is False
    assert bundle._is_valid_image_file("/path/__pycache__/file.pyc") is False
    assert bundle._is_valid_image_file("/path/node_modules/package.json") is False


@pytest.mark.mgmt
@pytest.mark.mgmt_bundle
def test_is_valid_image_file_allowed_hidden_files():
    """Test _is_valid_image_file with allowed hidden files."""
    assert bundle._is_valid_image_file("/path/.python-version") is True
    assert bundle._is_valid_image_file("/path/subdir/.python-version") is True


@pytest.mark.mgmt
@pytest.mark.mgmt_bundle
def test_is_valid_image_file_disallowed_hidden_files():
    """Test _is_valid_image_file with disallowed hidden files."""
    assert bundle._is_valid_image_file("/path/.hidden") is False
    assert bundle._is_valid_image_file("/path/.gitignore") is False
    assert bundle._is_valid_image_file("/path/.env") is False


@pytest.mark.mgmt
@pytest.mark.mgmt_bundle
def test_list_files(sample_files_structure):
    """Test _list_files function."""
    files = bundle._list_files(sample_files_structure["temp_dir"])

    # Convert to relative paths for easier testing
    relative_files = [os.path.relpath(f, sample_files_structure["temp_dir"]) for f in files]

    # Should include regular files
    assert "regular.txt" in relative_files
    assert os.path.join("subdir", "sub.txt") in relative_files

    # Should include allowed hidden files
    assert ".python-version" in relative_files
    assert os.path.join("subdir", ".python-version") in relative_files

    # Should not include disallowed hidden files
    assert ".hidden" not in relative_files

    # Should not include ignored files
    assert os.path.join("build", "ignored.txt") not in relative_files


@pytest.mark.mgmt
@pytest.mark.mgmt_bundle
def test_make_zipfile(temp_dir):
    """Test _make_zipfile function."""
    # Create test structure
    bundle_dir = Path(temp_dir) / "bundle"
    bundle_dir.mkdir()
    test_file = bundle_dir / "test.txt"
    test_file.write_text("test content")

    # Create zip
    zip_path = bundle._make_zipfile(base_name=os.path.join(temp_dir, "test"), root_dir=temp_dir, base_dir="bundle")

    # Verify zip was created
    assert os.path.exists(zip_path)
    assert zip_path.endswith(".zip")

    # Verify zip contents
    with zipfile.ZipFile(zip_path, "r") as zf:
        files = zf.namelist()
        assert "bundle/" in files
        assert "bundle/test.txt" in files


@pytest.mark.mgmt
@pytest.mark.mgmt_bundle
def test_make_zipfile_dry_run(temp_dir):
    """Test _make_zipfile with dry_run=True."""
    bundle_dir = Path(temp_dir) / "bundle"
    bundle_dir.mkdir()

    zip_path = bundle._make_zipfile(
        base_name=os.path.join(temp_dir, "test"), root_dir=temp_dir, base_dir="bundle", dry_run=True
    )

    # Should return path but not create file
    assert zip_path.endswith(".zip")
    assert not os.path.exists(zip_path)


@pytest.mark.mgmt
@pytest.mark.mgmt_bundle
def test_generate_dir(sample_files_structure, temp_dir):
    """Test generate_dir function."""
    out_dir = os.path.join(temp_dir, "output")

    result_dir = bundle.generate_dir(out_dir=out_dir, dir=sample_files_structure["temp_dir"], name="test_bundle")

    # Verify directory was created
    assert os.path.exists(result_dir)
    assert result_dir.endswith("test_bundle")

    # Verify files were copied
    assert os.path.exists(os.path.join(result_dir, "regular.txt"))
    assert os.path.exists(os.path.join(result_dir, ".python-version"))
    assert os.path.exists(os.path.join(result_dir, "subdir", "sub.txt"))

    # Verify ignored files were not copied
    assert not os.path.exists(os.path.join(result_dir, ".hidden"))
    assert not os.path.exists(os.path.join(result_dir, "build", "ignored.txt"))


@pytest.mark.mgmt
@pytest.mark.mgmt_bundle
def test_generate_dir_empty_directory(temp_dir):
    """Test generate_dir with empty directory."""
    empty_dir = os.path.join(temp_dir, "empty")
    os.makedirs(empty_dir)

    out_dir = os.path.join(temp_dir, "output")

    with pytest.raises(ValueError, match="is empty"):
        bundle.generate_dir(out_dir=out_dir, dir=empty_dir, name="empty_bundle")


@pytest.mark.mgmt
@pytest.mark.mgmt_bundle
@patch("seedfarmer.mgmt.bundle.create_output_dir")
@patch("seedfarmer.mgmt.bundle.shutil.copy")
@patch("seedfarmer.mgmt.bundle.CLI_ROOT", "/mock/cli/root")
def test_generate_bundle_basic(mock_copy, mock_create_output_dir, temp_dir):
    """Test generate_bundle function basic functionality."""
    # Setup mocks
    bundle_dir = os.path.join(temp_dir, "bundle")
    mock_create_output_dir.return_value = bundle_dir

    # Create bundle directory
    os.makedirs(bundle_dir, exist_ok=True)

    with patch("seedfarmer.mgmt.bundle._make_zipfile") as mock_make_zip:
        mock_make_zip.return_value = "test.zip"

        _ = bundle.generate_bundle()

        # Verify create_output_dir was called
        mock_create_output_dir.assert_called_once_with("bundle", None)

        # Verify resource files were copied (3 calls for the resource files)
        assert mock_copy.call_count == 3

        # Verify the specific resource files were copied
        expected_sources = [
            "/mock/cli/root/resources/retrieve_docker_creds.py",
            "/mock/cli/root/resources/pypi_mirror_support.py",
            "/mock/cli/root/resources/npm_mirror_support.py",
        ]

        actual_sources = [call.kwargs["src"] for call in mock_copy.call_args_list]
        for expected_source in expected_sources:
            assert expected_source in actual_sources

        # Verify zip was created
        mock_make_zip.assert_called_once()


@pytest.mark.mgmt
@pytest.mark.mgmt_bundle
@patch("seedfarmer.mgmt.bundle.create_output_dir")
@patch("seedfarmer.mgmt.bundle.generate_dir")
@patch("seedfarmer.mgmt.bundle.CLI_ROOT", "/mock/cli/root")
def test_generate_bundle_with_dirs(mock_generate_dir, mock_create_output_dir, temp_dir):
    """Test generate_bundle with directories."""
    bundle_dir = os.path.join(temp_dir, "bundle")
    mock_create_output_dir.return_value = bundle_dir
    mock_generate_dir.return_value = "generated_dir"

    os.makedirs(bundle_dir, exist_ok=True)

    dirs = [("/source/dir1", "dest1"), ("/source/dir2", "dest2")]

    with patch("seedfarmer.mgmt.bundle._make_zipfile") as mock_make_zip:
        with patch("seedfarmer.mgmt.bundle.shutil.copy"):
            mock_make_zip.return_value = "test.zip"

            bundle.generate_bundle(dirs=dirs)

            # Verify generate_dir was called for each directory
            assert mock_generate_dir.call_count == 2
            mock_generate_dir.assert_any_call(out_dir=bundle_dir, dir="/source/dir1", name="dest1")
            mock_generate_dir.assert_any_call(out_dir=bundle_dir, dir="/source/dir2", name="dest2")


@pytest.mark.mgmt
@pytest.mark.mgmt_bundle
@patch("seedfarmer.mgmt.bundle.create_output_dir")
@patch("seedfarmer.mgmt.bundle.CLI_ROOT", "/mock/cli/root")
def test_generate_bundle_with_files(mock_create_output_dir, temp_dir):
    """Test generate_bundle with individual files."""
    bundle_dir = os.path.join(temp_dir, "bundle")
    mock_create_output_dir.return_value = bundle_dir

    os.makedirs(bundle_dir, exist_ok=True)

    # Create source files
    src_file1 = os.path.join(temp_dir, "source1.txt")
    src_file2 = os.path.join(temp_dir, "source2.txt")
    Path(src_file1).write_text("content1")
    Path(src_file2).write_text("content2")

    files = [(src_file1, "dest1.txt"), (src_file2, "subdir/dest2.txt")]

    with patch("seedfarmer.mgmt.bundle._make_zipfile") as mock_make_zip:
        with patch("seedfarmer.mgmt.bundle.shutil.copy") as mock_copy:
            with patch("os.makedirs"):  # Mock makedirs to avoid directory creation issues
                mock_make_zip.return_value = "test.zip"

                bundle.generate_bundle(files=files)

                # Verify files were copied (3 resource files + 2 custom files)
                assert mock_copy.call_count == 5

                # Verify custom files were copied
                custom_calls = [
                    call
                    for call in mock_copy.call_args_list
                    if not any(
                        resource in str(call)
                        for resource in ["retrieve_docker_creds.py", "pypi_mirror_support.py", "npm_mirror_support.py"]
                    )
                ]
                assert len(custom_calls) == 2


@pytest.mark.mgmt
@pytest.mark.mgmt_bundle
def test_extract_zip(temp_dir):
    """Test extract_zip function."""
    # Create a test zip file
    zip_path = os.path.join(temp_dir, "test.zip")
    extract_to = os.path.join(temp_dir, "extracted")

    with zipfile.ZipFile(zip_path, "w") as zf:
        zf.writestr("test.txt", "test content")
        zf.writestr("subdir/nested.txt", "nested content")

    # Extract the zip
    bundle.extract_zip(zip_path, extract_to)

    # Verify extraction
    assert os.path.exists(os.path.join(extract_to, "test.txt"))
    assert os.path.exists(os.path.join(extract_to, "subdir", "nested.txt"))

    # Verify content
    with open(os.path.join(extract_to, "test.txt"), "r") as f:
        assert f.read() == "test content"


@pytest.mark.mgmt
@pytest.mark.mgmt_bundle
def test_extract_zip_file_not_found():
    """Test extract_zip with non-existent file."""
    with pytest.raises(FileNotFoundError, match="Zip file not found"):
        bundle.extract_zip("/nonexistent/file.zip", "/some/path")
