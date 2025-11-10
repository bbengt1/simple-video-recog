"""Unit tests for core/version.py module."""

import platform
import sys
from unittest.mock import MagicMock, patch

import pytest
from pydantic import ValidationError

from core.version import VersionInfo, get_version_info, VERSION, BUILD_DATE, GIT_COMMIT


class TestVersionInfo:
    """Test VersionInfo Pydantic model."""

    def test_version_info_creation(self):
        """Test VersionInfo can be created with valid data."""
        info = VersionInfo(
            version="1.0.0",
            build_date="2025-11-08",
            git_commit="abc123f",
            python_version="3.10.12",
            platform="macOS-14.2-arm64",
            opencv_version="4.8.1",
            coreml_version="7.0.0",
            ollama_version="0.1.0"
        )
        assert info.version == "1.0.0"
        assert info.build_date == "2025-11-08"
        assert info.git_commit == "abc123f"
        assert info.python_version == "3.10.12"
        assert info.platform == "macOS-14.2-arm64"
        assert info.opencv_version == "4.8.1"
        assert info.coreml_version == "7.0.0"
        assert info.ollama_version == "0.1.0"

    def test_version_info_validation(self):
        """Test VersionInfo field validation."""
        # All fields are required strings
        with pytest.raises(ValidationError):
            VersionInfo(
                version="1.0.0",
                build_date="2025-11-08",
                git_commit="abc123f",
                python_version="3.10.12",
                platform="macOS-14.2-arm64",
                opencv_version="4.8.1",
                coreml_version="7.0.0"
                # Missing ollama_version
            )


class TestGetVersionInfo:
    """Test get_version_info function."""

    @patch('core.version.sys')
    @patch('core.version.platform')
    @patch('core.version.opencv_version', '4.8.1')
    @patch('core.version.coreml_version', '7.0.0')
    @patch('core.version.ollama_version', '0.1.0')
    def test_get_version_info_success(self, mock_platform, mock_sys):
        """Test get_version_info returns correct VersionInfo when all imports succeed."""
        mock_sys.version = "3.10.12 (main, Jun  7 2023, 00:00:00) [Clang 14.0.3]"
        mock_platform.platform.return_value = "macOS-14.2-arm64"

        info = get_version_info()

        assert isinstance(info, VersionInfo)
        assert info.version == VERSION
        assert info.build_date == BUILD_DATE
        assert info.git_commit == GIT_COMMIT
        assert info.python_version == mock_sys.version
        assert info.platform == mock_platform.platform.return_value
        assert info.opencv_version == "4.8.1"
        assert info.coreml_version == "7.0.0"
        assert info.ollama_version == "0.1.0"

    @patch('core.version.opencv_version', 'Not available')
    @patch('core.version.coreml_version', 'Not available')
    @patch('core.version.ollama_version', 'Not available')
    def test_get_version_info_import_failures(self):
        """Test get_version_info handles import failures gracefully."""
        info = get_version_info()

        assert info.opencv_version == "Not available"
        assert info.coreml_version == "Not available"
        assert info.ollama_version == "Not available"

    def test_constants(self):
        """Test version constants are set correctly."""
        assert VERSION == "1.0.0"
        assert BUILD_DATE == "2025-11-08"
        assert GIT_COMMIT == "abc123f"