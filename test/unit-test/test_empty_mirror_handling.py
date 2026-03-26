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

import importlib
import os
import subprocess
import sys
from unittest import mock

import pytest


@pytest.mark.mirror
class TestPypiMirrorSupport:
    """Tests for pypi_mirror_support.py empty string handling."""

    SCRIPT = os.path.join(os.path.dirname(__file__), "..", "..", "seedfarmer", "resources", "pypi_mirror_support.py")

    def test_empty_secret_name_skips_secrets_manager(self):
        """Empty string SEEDFARMER_PYPI_MIRROR_SECRET should not call Secrets Manager."""
        env = os.environ.copy()
        env["SEEDFARMER_PYPI_MIRROR_SECRET"] = ""
        env["AWS_DEFAULT_REGION"] = "us-west-2"
        result = subprocess.run(
            [sys.executable, self.SCRIPT, "https://example.com/simple/"],
            env=env,
            capture_output=True,
            text=True,
            timeout=10,
        )
        assert result.returncode == 0
        assert "pip config being set for" in result.stdout

    def test_no_secret_default_skips_secrets_manager(self):
        """NO_SECRET value should not call Secrets Manager."""
        env = os.environ.copy()
        env["SEEDFARMER_PYPI_MIRROR_SECRET"] = "NO_SECRET"
        env["AWS_DEFAULT_REGION"] = "us-west-2"
        result = subprocess.run(
            [sys.executable, self.SCRIPT, "https://example.com/simple/"],
            env=env,
            capture_output=True,
            text=True,
            timeout=10,
        )
        assert result.returncode == 0


@pytest.mark.mirror
class TestNpmMirrorSupport:
    """Tests for npm_mirror_support.py empty string handling."""

    SCRIPT = os.path.join(os.path.dirname(__file__), "..", "..", "seedfarmer", "resources", "npm_mirror_support.py")

    def test_empty_secret_name_skips_secrets_manager(self):
        """Empty string SEEDFARMER_NPM_MIRROR_SECRET should not call Secrets Manager."""
        env = os.environ.copy()
        env["SEEDFARMER_NPM_MIRROR_SECRET"] = ""
        env["AWS_DEFAULT_REGION"] = "us-west-2"
        result = subprocess.run(
            [sys.executable, self.SCRIPT, "https://example.com/npm/"],
            env=env,
            capture_output=True,
            text=True,
            timeout=10,
        )
        assert result.returncode == 0
        assert "npm config" in result.stdout.lower() or "Setting npm" in result.stdout


@pytest.mark.mirror
class TestInstallCommandsMirrorHandling:
    """Tests that empty string mirrors are treated as unset in install commands.

    Uses importlib to load modules directly, avoiding circular import issues.
    """

    def _load_deploy_module(self, module_name):
        """Load deploy module avoiding circular imports."""
        spec = importlib.util.spec_from_file_location(
            module_name,
            os.path.join(os.path.dirname(__file__), "..", "..", "seedfarmer", "deployment", f"{module_name}.py"),
        )
        # Mock the problematic imports
        with mock.patch.dict(
            "sys.modules",
            {
                "seedfarmer.commands._runtimes": mock.MagicMock(),
                "seedfarmer.commands": mock.MagicMock(),
                "seedfarmer.deployment.deploy_factory": mock.MagicMock(),
            },
        ):
            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)
        return mod

    def test_remote_empty_pypi_mirror_skipped(self):
        """Empty string pypi_mirror should not generate mirror install commands (remote)."""
        mod = self._load_deploy_module("deploy_remote")

        module_manifest = mock.MagicMock()
        module_manifest.npm_mirror = None
        module_manifest.pypi_mirror = None

        deployer = mock.MagicMock()
        deployer.mdo = mock.MagicMock()
        deployer.mdo.npm_mirror = ""
        deployer.mdo.pypi_mirror = ""

        commands = mod.DeployRemoteModule._codebuild_install_commands(
            deployer, module_manifest, stack_outputs=None, runtimes=None
        )
        mirror_commands = [c for c in commands if "mirror_support" in c]
        assert len(mirror_commands) == 0, f"Expected no mirror commands, got: {mirror_commands}"

    def test_remote_set_pypi_mirror_included(self):
        """Non-empty pypi_mirror should generate mirror install commands (remote)."""
        mod = self._load_deploy_module("deploy_remote")

        module_manifest = mock.MagicMock()
        module_manifest.npm_mirror = None
        module_manifest.pypi_mirror = None

        deployer = mock.MagicMock()
        deployer.mdo = mock.MagicMock()
        deployer.mdo.npm_mirror = ""
        deployer.mdo.pypi_mirror = "https://example.com/simple/"

        commands = mod.DeployRemoteModule._codebuild_install_commands(
            deployer, module_manifest, stack_outputs=None, runtimes=None
        )
        pypi_commands = [c for c in commands if "pypi_mirror_support" in c]
        assert len(pypi_commands) > 0, "Expected pypi mirror commands"
        assert any("https://example.com/simple/" in c for c in pypi_commands)

    def test_local_empty_pypi_mirror_skipped(self):
        """Empty string pypi_mirror should not generate mirror install commands (local)."""
        mod = self._load_deploy_module("deploy_local")

        module_manifest = mock.MagicMock()
        module_manifest.npm_mirror = None
        module_manifest.pypi_mirror = None

        deployer = mock.MagicMock()
        deployer.mdo = mock.MagicMock()
        deployer.mdo.npm_mirror = ""
        deployer.mdo.pypi_mirror = ""

        commands = mod.DeployLocalModule._codebuild_install_commands(
            deployer, module_manifest, stack_outputs=None, runtimes=None
        )
        mirror_commands = [c for c in commands if "mirror_support" in c]
        assert len(mirror_commands) == 0, f"Expected no mirror commands, got: {mirror_commands}"
