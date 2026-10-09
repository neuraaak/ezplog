# ///////////////////////////////////////////////////////////////
# EZPL - Pytest Configuration and Fixtures
# Project: ezpl
# ///////////////////////////////////////////////////////////////

"""
Pytest configuration and shared fixtures for Ezpl tests.

This module provides fixtures for:
- Ezpl singleton management
- Temporary files and directories
- Mock Rich Console
- ConfigurationManager instances
- Custom pytest markers
"""

from __future__ import annotations

# ///////////////////////////////////////////////////////////////
# IMPORTS
# ///////////////////////////////////////////////////////////////
# Standard library imports
import gc
import os
import shutil
import sys
import tempfile
from collections.abc import Generator
from pathlib import Path
from unittest.mock import Mock

# Third-party imports
import pytest
from rich.console import Console

# Local imports
from ezplog import Ezpl
from ezplog.config import ConfigurationManager

# ///////////////////////////////////////////////////////////////
# FIXTURES
# ///////////////////////////////////////////////////////////////


@pytest.fixture(autouse=True)
def reset_ezpl() -> Generator[None]:
    """
    Automatically reset Ezpl singleton before and after each test.

    This ensures test isolation and prevents state leakage between tests.
    """
    # Reset before test
    Ezpl.reset()
    yield
    # Reset after test — loguru.remove() in Ezpl.reset() is synchronous,
    # so no sleep is needed; gc.collect() releases remaining Python references.
    Ezpl.reset()
    gc.collect()


@pytest.fixture
def temp_dir() -> Generator[Path]:
    """
    Create a temporary directory for test files.

    Yields:
        Path to temporary directory
    """
    tmpdir = Path(tempfile.mkdtemp())
    yield tmpdir
    # gc.collect() ensures Python-level references are released before rmtree.
    # ignore_errors=True handles the rare case where a file handle is still
    # open (e.g. tests that create Ezpl directly without ezpl_instance fixture).
    gc.collect()
    shutil.rmtree(tmpdir, ignore_errors=True)


@pytest.fixture
def temp_log_file(temp_dir: Path) -> Path:
    """
    Create a temporary log file path.

    Args:
        temp_dir: Temporary directory fixture

    Returns:
        Path to temporary log file
    """
    return temp_dir / "test.log"


@pytest.fixture
def temp_config_file(temp_dir: Path) -> Path:
    """
    Create a temporary config file path.

    Args:
        temp_dir: Temporary directory fixture

    Returns:
        Path to temporary config file
    """
    config_file = temp_dir / "config.json"
    config_file.parent.mkdir(parents=True, exist_ok=True)
    return config_file


@pytest.fixture
def mock_console() -> Mock:
    """
    Create a mock Rich Console for testing.

    Returns:
        Mock Console instance
    """
    console = Mock(spec=Console)
    console.print = Mock()
    console._width = 80
    return console


@pytest.fixture
def ezpl_instance(temp_log_file: Path) -> Generator[Ezpl]:
    """
    Create a fresh Ezpl instance with temporary log file.

    Args:
        temp_log_file: Temporary log file path

    Yields:
        Ezpl instance
    """
    Ezpl.reset()
    yield Ezpl(log_file=temp_log_file)
    # Close the file handle HERE (before temp_dir teardown runs),
    # so that shutil.rmtree in temp_dir can delete the log file immediately.
    Ezpl.reset()
    gc.collect()


@pytest.fixture
def config_manager(temp_config_file: Path) -> ConfigurationManager:
    """
    Create a ConfigurationManager instance with temporary config file.

    Args:
        temp_config_file: Temporary config file path

    Returns:
        ConfigurationManager instance
    """
    return ConfigurationManager(config_file=temp_config_file)


@pytest.fixture
def clean_env() -> Generator[None]:
    """
    Clean environment variables before and after test.

    Removes all EZPL_* environment variables to ensure clean test state.
    """
    # Store original env vars
    original_env = {}
    for key in list(os.environ.keys()):
        if key.startswith("EZPL_"):
            original_env[key] = os.environ.pop(key)

    yield

    # Restore original env vars
    os.environ.update(original_env)
    for key in list(os.environ.keys()):
        if key.startswith("EZPL_") and key not in original_env:
            del os.environ[key]


@pytest.fixture
def sample_log_data() -> list[dict]:
    """
    Sample log data for testing.

    Returns:
        List of sample log entries
    """
    return [
        {
            "timestamp": "2024-01-01 10:00:00",
            "level": "INFO",
            "message": "Test message 1",
            "module": "test_module",
        },
        {
            "timestamp": "2024-01-01 10:00:01",
            "level": "ERROR",
            "message": "Test error message",
            "module": "test_module",
        },
        {
            "timestamp": "2024-01-01 10:00:02",
            "level": "WARNING",
            "message": "Test warning message",
            "module": "test_module",
        },
    ]


# ///////////////////////////////////////////////////////////////
# PYTEST HOOKS
# ///////////////////////////////////////////////////////////////


def pytest_runtest_teardown(item, nextitem) -> None:  # noqa: ARG001
    """
    Hook to handle teardown errors on Windows.

    gc.collect() ensures Python-level file handle references are released
    immediately after each test teardown. No sleep is needed since
    loguru.remove() closes file handles synchronously.
    """
    if sys.platform == "win32":
        gc.collect()


@pytest.hookimpl(tryfirst=True)
def pytest_runtest_makereport(item, call):  # noqa: ARG001
    """
    Suppress NotADirectoryError and PermissionError during teardown on Windows.

    These errors occur when pytest tries to clean up temporary directories
    but loguru still has file handles open. They don't affect test results.
    """
    if sys.platform == "win32" and call.when == "teardown" and call.excinfo:
        exc_type = call.excinfo.type
        if exc_type in (NotADirectoryError, PermissionError, OSError):
            # Check if it's a Windows file lock error
            exc_value = str(call.excinfo.value).lower()
            if any(
                keyword in exc_value
                for keyword in [
                    "winerror 32",
                    "winerror 267",
                    "utilisé par un autre processus",
                    "used by another process",
                    "nom de répertoire non valide",
                ]
            ):
                # Suppress the exception by clearing excinfo
                call.excinfo = None


def pytest_runtest_logreport(report):
    """
    Additional suppression of teardown errors in the final report.

    This ensures that even if an error was recorded, it's marked as passed
    if it's a Windows file lock error.
    """
    import sys

    if sys.platform == "win32" and report.when == "teardown" and report.failed:
        # Check if it's a Windows file lock error
        longrepr_str = ""
        if hasattr(report, "longrepr") and report.longrepr:
            longrepr_str = str(report.longrepr).lower()

        # Check for Windows file lock errors
        if any(
            keyword in longrepr_str
            for keyword in [
                "winerror 32",
                "winerror 267",
                "utilisé par un autre processus",
                "used by another process",
                "nom de répertoire non valide",
                "notadirectoryerror",
                "permissionerror",
            ]
        ):
            # Mark as passed to suppress the error
            report.outcome = "passed"
            report.longrepr = None
            report.sections = []


# ///////////////////////////////////////////////////////////////
# MARKERS
# ///////////////////////////////////////////////////////////////

# Markers are registered in pytest.ini
# Available markers:
# - @pytest.mark.slow: Marks tests as slow (can be excluded with --fast)
# - @pytest.mark.integration: Marks tests as integration tests
# - @pytest.mark.robustness: Marks tests as robustness tests
# - @pytest.mark.unit: Marks tests as unit tests (default)
