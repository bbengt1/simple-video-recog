"""Version information and build metadata for the Video Recognition System."""

import platform
import sys
from typing import Optional

try:
    import cv2
    opencv_version = cv2.__version__
except ImportError:
    opencv_version = "Not available"

try:
    import coremltools
    coreml_version = coremltools.__version__
except ImportError:
    coreml_version = "Not available"

try:
    import ollama
    ollama_version = getattr(ollama, '__version__', 'Not available')
except ImportError:
    ollama_version = "Not available"

from pydantic import BaseModel, Field


class VersionInfo(BaseModel):
    """Version and build information for the application."""

    version: str = Field(description="Application version (semantic versioning)")
    build_date: str = Field(description="Build timestamp in ISO format")
    git_commit: str = Field(description="Git commit hash (short)")
    python_version: str = Field(description="Runtime Python version")
    platform: str = Field(description="OS and architecture information")
    opencv_version: str = Field(description="OpenCV version")
    coreml_version: str = Field(description="CoreML Tools version")
    ollama_version: str = Field(description="Ollama client version")


# Version constants - updated by CI/CD pipeline
VERSION = "1.0.0"
BUILD_DATE = "2025-11-08"
GIT_COMMIT = "abc123f"  # Set by CI/CD


def get_version_info() -> VersionInfo:
    """Get comprehensive version information for the application.

    Returns:
        VersionInfo object containing all version and runtime information.
    """
    try:
        platform_info = platform.platform()
    except Exception:
        # Fallback to basic platform info if uname fails
        platform_info = f"{platform.system()} {platform.release()}"

    return VersionInfo(
        version=VERSION,
        build_date=BUILD_DATE,
        git_commit=GIT_COMMIT if GIT_COMMIT != "dev" else "dev",  # Use "dev" if not set
        python_version=sys.version,
        platform=platform_info,
        opencv_version=opencv_version,
        coreml_version=coreml_version,
        ollama_version=ollama_version,
    )


def format_version_output() -> str:
    """Format version information for CLI display.

    Returns:
        Formatted version string for console output matching acceptance criteria
    """
    info = get_version_info()

    output = f"""Video Recognition System v{info.version}
Build: {info.build_date} (commit {info.git_commit})
Python: {info.python_version.split()[0]}
Platform: {info.platform}
Dependencies:
  - OpenCV: {info.opencv_version}
  - CoreML Tools: {info.coreml_version}
  - Ollama: {info.ollama_version}
"""

    return output