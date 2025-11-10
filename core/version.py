"""Version information for the video recognition system.

This module provides version and build information for the application.
"""
import platform
import sys
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class VersionInfo(BaseModel):
    """Structured version information."""

    version: str = Field(..., description="Semantic version string")
    build_date: str = Field(..., description="Build date in YYYY-MM-DD format")
    git_commit: Optional[str] = Field(None, description="Git commit hash")
    python_version: str = Field(..., description="Python version")
    platform: str = Field(..., description="Operating system platform")
    architecture: str = Field(..., description="System architecture")


# Version constants - updated by CI/CD pipeline
VERSION = "1.0.0"
BUILD_DATE = "2025-11-08"
GIT_COMMIT = None  # Set by CI/CD


def get_version_info() -> VersionInfo:
    """Get complete version information including runtime details.

    Returns:
        VersionInfo object with version and runtime information
    """
    return VersionInfo(
        version=VERSION,
        build_date=BUILD_DATE,
        git_commit=GIT_COMMIT,
        python_version=f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
        platform=platform.system(),
        architecture=platform.machine()
    )


def format_version_output() -> str:
    """Format version information for CLI display.

    Returns:
        Formatted version string for console output
    """
    info = get_version_info()
    version_str = f"video-recog v{info.version} (build {info.build_date})"
    runtime_str = f" - Python {info.python_version} - {info.platform}"

    if info.git_commit:
        version_str += f" - {info.git_commit[:8]}"

    return version_str + runtime_str