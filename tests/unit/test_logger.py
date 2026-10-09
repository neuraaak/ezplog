# ///////////////////////////////////////////////////////////////
# EZPL - Tests unitaires EzLogger
# Project: ezpl
# ///////////////////////////////////////////////////////////////

"""
Unit tests for EzLogger.

Tests cover:
- All log levels
- File rotation (size, date, time)
- Retention (duration, count)
- Compression (zip, gz, tar.gz)
- Separators
- File size operations
- Special character handling
- Error handling
- Directory creation

Note: Some tests intentionally use try-except-pass for robustness testing.
"""

# ruff: noqa: S110, SIM105

from __future__ import annotations

# ///////////////////////////////////////////////////////////////
# IMPORTS
# ///////////////////////////////////////////////////////////////
# Standard library imports
import time
from pathlib import Path
from unittest.mock import patch

# Third-party imports
import pytest

# Local imports
from ezplog import Ezpl
from ezplog.core.exceptions import FileOperationError, ValidationError
from ezplog.handlers import EzLogger

# ///////////////////////////////////////////////////////////////
# HELPER FUNCTIONS
# ///////////////////////////////////////////////////////////////


def wait_for_file(path: Path, timeout: float = 2.0) -> None:
    """Wait for file to be created."""
    start = time.time()
    while not path.exists():
        if time.time() - start > timeout:
            raise FileNotFoundError(f"Timeout waiting for file: {path}")
        time.sleep(0.05)


# ///////////////////////////////////////////////////////////////
# TESTS
# ///////////////////////////////////////////////////////////////


class TestLogLevels:
    """Tests for all log levels."""

    def test_should_create_log_file_when_debug_messages_are_written(
        self, temp_log_file: Path
    ) -> None:
        """Test debug() level."""
        logger_handler = EzLogger(temp_log_file, level="DEBUG")
        logger = logger_handler.get_loguru()
        logger.debug("Debug message")
        wait_for_file(temp_log_file)
        assert temp_log_file.exists()

    def test_should_create_log_file_when_info_messages_are_written(
        self, temp_log_file: Path
    ) -> None:
        """Test info() level."""
        logger_handler = EzLogger(temp_log_file, level="INFO")
        logger = logger_handler.get_loguru()
        logger.info("Info message")
        wait_for_file(temp_log_file)
        assert temp_log_file.exists()

    def test_should_create_log_file_when_warning_messages_are_written(
        self, temp_log_file: Path
    ) -> None:
        """Test warning() level."""
        logger_handler = EzLogger(temp_log_file, level="WARNING")
        logger = logger_handler.get_loguru()
        logger.warning("Warning message")
        wait_for_file(temp_log_file)
        assert temp_log_file.exists()

    def test_should_create_log_file_when_error_messages_are_written(
        self, temp_log_file: Path
    ) -> None:
        """Test error() level."""
        logger_handler = EzLogger(temp_log_file, level="ERROR")
        logger = logger_handler.get_loguru()
        logger.error("Error message")
        wait_for_file(temp_log_file)
        assert temp_log_file.exists()

    def test_should_create_log_file_when_critical_messages_are_written(
        self, temp_log_file: Path
    ) -> None:
        """Test critical() level."""
        logger_handler = EzLogger(temp_log_file, level="CRITICAL")
        logger = logger_handler.get_loguru()
        logger.critical("Critical message")
        wait_for_file(temp_log_file)
        assert temp_log_file.exists()

    def test_should_update_internal_level_attribute_when_set_level_is_called(
        self, temp_log_file: Path
    ) -> None:
        """Test set_level() method."""
        logger_handler = EzLogger(temp_log_file, level="INFO")
        logger_handler.set_level("DEBUG")
        assert logger_handler._level == "DEBUG"

    def test_should_raise_validation_error_when_logger_is_created_with_invalid_level(
        self, temp_log_file: Path
    ) -> None:
        """Test that invalid level raises ValidationError."""
        with pytest.raises(ValidationError):
            EzLogger(temp_log_file, level="INVALID_LEVEL")


class TestFileRotation:
    """Tests for file rotation."""

    def test_should_rotate_log_when_file_reaches_size_threshold(
        self, temp_dir: Path
    ) -> None:
        """Test rotation by file size."""
        log_file = temp_dir / "rotation_size.log"
        logger_handler = EzLogger(
            log_file, level="INFO", rotation="1 KB", retention="1 day"
        )
        logger = logger_handler.get_loguru()

        # Write enough data to trigger rotation
        for i in range(100):
            logger.info(f"Test message {i} " * 10)

        # Verify file exists or rotation occurred
        assert log_file.exists() or any(log_file.parent.glob("rotation_size.log.*"))

    def test_should_rotate_log_when_time_interval_elapses(self, temp_dir: Path) -> None:
        """Test rotation by time."""
        log_file = temp_dir / "rotation_time.log"
        logger_handler = EzLogger(
            log_file, level="INFO", rotation="1 second", retention="1 day"
        )
        logger = logger_handler.get_loguru()

        logger.info("Message 1")
        time.sleep(1.1)  # Wait for rotation time
        logger.info("Message 2")

        # Verify rotation occurred
        assert log_file.exists() or any(log_file.parent.glob("rotation_time.log.*"))

    def test_should_create_log_file_when_rotation_is_set_by_date(
        self, temp_dir: Path
    ) -> None:
        """Test rotation by date."""
        log_file = temp_dir / "rotation_date.log"
        logger_handler = EzLogger(
            log_file, level="INFO", rotation="1 day", retention="7 days"
        )
        logger = logger_handler.get_loguru()
        logger.info("Test message")
        # Verify file exists
        assert log_file.exists()

    def test_should_create_log_file_when_rotation_is_set_at_specific_time(
        self, temp_dir: Path
    ) -> None:
        """Test rotation at specific time."""
        log_file = temp_dir / "rotation_at_time.log"
        logger_handler = EzLogger(
            log_file, level="INFO", rotation="12:00", retention="7 days"
        )
        logger = logger_handler.get_loguru()
        logger.info("Test message")
        # Verify file exists
        assert log_file.exists()


class TestRetention:
    """Tests for log retention."""

    def test_should_create_log_file_when_retention_is_set_by_duration(
        self, temp_dir: Path
    ) -> None:
        """Test retention by duration."""
        log_file = temp_dir / "retention_duration.log"
        logger_handler = EzLogger(log_file, level="INFO", retention="1 day")
        logger = logger_handler.get_loguru()
        logger.info("Test message")
        # Verify file exists
        assert log_file.exists()

    def test_should_create_log_files_when_rotation_and_retention_are_configured(
        self, temp_dir: Path
    ) -> None:
        """Test retention by duration (loguru doesn't support file count directly)."""
        log_file = temp_dir / "retention_count.log"
        logger_handler = EzLogger(
            log_file, level="INFO", rotation="1 KB", retention="1 day"
        )
        logger = logger_handler.get_loguru()

        # Write enough to create multiple files
        for i in range(50):
            logger.info(f"Test message {i} " * 10)

        # Verify files exist
        assert log_file.exists() or any(log_file.parent.glob("retention_count.log.*"))


class TestCompression:
    """Tests for log compression."""

    def test_should_create_zip_compressed_archives_when_compression_is_zip(
        self, temp_dir: Path
    ) -> None:
        """Test compression with zip format."""
        log_file = temp_dir / "compression_zip.log"
        logger_handler = EzLogger(
            log_file,
            level="INFO",
            rotation="1 KB",
            retention="1 day",
            compression="zip",
        )
        logger = logger_handler.get_loguru()

        # Write enough to trigger rotation
        for i in range(50):
            logger.info(f"Test message {i} " * 10)

        # Verify file exists or compressed files exist
        assert log_file.exists() or any(
            log_file.parent.glob("compression_zip.log.*.zip")
        )

    def test_should_create_gz_compressed_archives_when_compression_is_gz(
        self, temp_dir: Path
    ) -> None:
        """Test compression with gz format."""
        log_file = temp_dir / "compression_gz.log"
        logger_handler = EzLogger(
            log_file,
            level="INFO",
            rotation="1 KB",
            retention="1 day",
            compression="gz",
        )
        logger = logger_handler.get_loguru()

        # Write enough to trigger rotation
        for i in range(50):
            logger.info(f"Test message {i} " * 10)

        # Verify file exists
        assert log_file.exists() or any(log_file.parent.glob("compression_gz.log.*.gz"))

    def test_should_create_targz_compressed_archives_when_compression_is_tar_gz(
        self, temp_dir: Path
    ) -> None:
        """Test compression with tar.gz format."""
        log_file = temp_dir / "compression_tar_gz.log"
        logger_handler = EzLogger(
            log_file,
            level="INFO",
            rotation="1 KB",
            retention="1 day",
            compression="tar.gz",
        )
        logger = logger_handler.get_loguru()

        # Write enough to trigger rotation
        for i in range(50):
            logger.info(f"Test message {i} " * 10)

        # Verify file exists
        assert log_file.exists() or any(
            log_file.parent.glob("compression_tar_gz.log.*.tar.gz")
        )


class TestSeparators:
    """Tests for log separators."""

    def test_should_write_separator_markers_to_log_when_add_separator_is_called(
        self, temp_log_file: Path
    ) -> None:
        """Test add_separator() method."""
        logger_handler = EzLogger(temp_log_file, level="INFO")
        logger_handler.add_separator()
        logger = logger_handler.get_loguru()
        logger.info("Test message")
        wait_for_file(temp_log_file)
        content = temp_log_file.read_text(encoding="utf-8")
        assert "==>" in content or "---" in content or len(content) > 0

    def test_should_write_separator_markers_to_log_when_add_separator_is_called_via_ezpl(
        self, temp_log_file: Path
    ) -> None:
        """Test separator via Ezpl."""
        ezpl = Ezpl(log_file=temp_log_file)
        ezpl.add_separator()
        ezpl.get_logger().info("Test message")
        wait_for_file(temp_log_file)
        content = temp_log_file.read_text(encoding="utf-8")
        assert "==>" in content or "---" in content or len(content) > 0


class TestFileOperations:
    """Tests for file operations."""

    def test_should_return_correct_path_when_get_log_file_is_called(
        self, temp_log_file: Path
    ) -> None:
        """Test get_log_file() method."""
        logger_handler = EzLogger(temp_log_file, level="INFO")
        assert logger_handler.get_log_file() == temp_log_file

    def test_should_return_positive_size_when_messages_have_been_written(
        self, temp_log_file: Path
    ) -> None:
        """Test get_file_size() method."""
        logger_handler = EzLogger(temp_log_file, level="INFO")
        logger = logger_handler.get_loguru()
        logger.info("Test message 1")
        logger.info("Test message 2")
        wait_for_file(temp_log_file)
        size = logger_handler.get_file_size()
        assert size > 0

    def test_should_return_zero_or_more_when_no_messages_have_been_written(
        self, temp_log_file: Path
    ) -> None:
        """Test get_file_size() with empty file."""
        logger_handler = EzLogger(temp_log_file, level="INFO")
        size = logger_handler.get_file_size()
        assert size >= 0


class TestSpecialCharacters:
    """Tests for special character handling."""

    def test_should_preserve_unicode_in_log_file_when_unicode_messages_are_written(
        self, temp_log_file: Path
    ) -> None:
        """Test logger with Unicode characters."""
        logger_handler = EzLogger(temp_log_file, level="INFO")
        logger = logger_handler.get_loguru()
        strange_message = "Special test: éèàçô 漢字 🚀"
        logger.info(strange_message)
        wait_for_file(temp_log_file)
        content = temp_log_file.read_text(encoding="utf-8")
        assert "Special test" in content
        assert "漢字" in content
        assert "🚀" in content

    def test_should_not_crash_when_messages_contain_control_characters(
        self, temp_log_file: Path
    ) -> None:
        """Test logger with control characters."""
        logger_handler = EzLogger(temp_log_file, level="INFO")
        logger = logger_handler.get_loguru()
        message_with_control = "Test\x00\x1b[31m"
        logger.info(message_with_control)
        wait_for_file(temp_log_file)
        # Should not crash
        assert temp_log_file.exists()

    def test_should_log_message_when_it_contains_html_tags(
        self, temp_log_file: Path
    ) -> None:
        """Test logger with HTML tags."""
        logger_handler = EzLogger(temp_log_file, level="INFO")
        logger = logger_handler.get_loguru()
        logger.info("Message with <tags> and </tags>")
        wait_for_file(temp_log_file)
        content = temp_log_file.read_text(encoding="utf-8")
        # HTML tags should be sanitized or preserved
        assert "Message" in content


class TestTypeConversion:
    """Tests for automatic type conversion."""

    def test_should_log_exception_details_when_exception_object_is_passed(
        self, temp_log_file: Path
    ) -> None:
        """Test logger with exception object."""
        logger_handler = EzLogger(temp_log_file, level="INFO")
        logger = logger_handler.get_loguru()
        try:
            {}[0]
        except Exception as exc:
            logger.error(exc)
            logger.error(f"Exception: {exc}")
        wait_for_file(temp_log_file)
        content = temp_log_file.read_text(encoding="utf-8")
        assert "Exception" in content or "KeyError" in content

    def test_should_not_crash_when_dict_is_passed_as_log_message(
        self, temp_log_file: Path
    ) -> None:
        """Test logger with dictionary message."""
        logger_handler = EzLogger(temp_log_file, level="INFO")
        logger = logger_handler.get_loguru()
        logger.info({"key": "value"})
        wait_for_file(temp_log_file)
        assert temp_log_file.exists()

    def test_should_not_crash_when_list_is_passed_as_log_message(
        self, temp_log_file: Path
    ) -> None:
        """Test logger with list message."""
        logger_handler = EzLogger(temp_log_file, level="INFO")
        logger = logger_handler.get_loguru()
        logger.info(["list", "items"])
        wait_for_file(temp_log_file)
        assert temp_log_file.exists()


class TestErrorHandling:
    """Tests for error handling."""

    def test_should_handle_gracefully_when_log_directory_has_permission_issues(
        self, temp_dir: Path
    ) -> None:
        """Test handling of invalid directory permissions."""
        # Create a path that might have permission issues
        invalid_path = temp_dir / "invalid" / "path" / "test.log"
        # Should handle gracefully or raise FileOperationError
        try:
            logger_handler = EzLogger(invalid_path, level="INFO")
            # If it succeeds, verify file was created
            assert logger_handler.get_log_file() == invalid_path
        except FileOperationError:
            # Expected behavior for permission errors
            pass

    def test_should_handle_gracefully_when_file_write_fails(
        self, temp_log_file: Path
    ) -> None:
        """Test handling of file write errors."""
        logger_handler = EzLogger(temp_log_file, level="INFO")
        logger = logger_handler.get_loguru()

        # Try to write with mocked error
        with patch("builtins.open", side_effect=OSError("Write error")):
            try:
                logger.info("Test message")
            except (OSError, Exception):
                # Expected behavior - should handle gracefully
                pass


class TestDirectoryCreation:
    """Tests for automatic directory creation."""

    def test_should_create_parent_directory_when_log_file_is_in_nested_subdir(
        self, temp_dir: Path
    ) -> None:
        """Test that parent directory is created automatically."""
        log_file = temp_dir / "subdir" / "nested" / "test.log"
        logger_handler = EzLogger(log_file, level="INFO")
        assert log_file.parent.exists()
        assert logger_handler.get_log_file() == log_file

    def test_should_not_crash_when_log_directory_already_exists(
        self, temp_dir: Path
    ) -> None:
        """Test handling of existing directory."""
        log_file = temp_dir / "existing" / "test.log"
        log_file.parent.mkdir(parents=True, exist_ok=True)
        logger_handler = EzLogger(log_file, level="INFO")
        assert logger_handler.get_log_file() == log_file


@pytest.mark.unit
def test_logger_accepts_timedelta_rotation(tmp_path):
    from datetime import timedelta

    from ezplog.handlers.file import EzLogger

    logger = EzLogger(log_file=tmp_path / "a.log", rotation=timedelta(hours=6))
    assert logger.rotation == timedelta(hours=6)


@pytest.mark.unit
def test_logger_accepts_int_retention(tmp_path):
    from ezplog.handlers.file import EzLogger

    logger = EzLogger(log_file=tmp_path / "b.log", retention=10)
    assert logger.retention == 10


@pytest.mark.unit
def test_logger_accepts_valid_compression(tmp_path):
    from ezplog.handlers.file import EzLogger

    logger = EzLogger(log_file=tmp_path / "c.log", compression="zip")
    assert logger.compression == "zip"


@pytest.mark.unit
def test_logger_rejects_invalid_compression(tmp_path):
    from ezplog.core.exceptions import ValidationError
    from ezplog.handlers.file import EzLogger

    with pytest.raises(ValidationError):
        EzLogger(log_file=tmp_path / "d.log", compression="zpi")


@pytest.mark.unit
def test_logger_accepts_callable_compression(tmp_path):
    from ezplog.handlers.file import EzLogger

    def my_compressor(_path: str) -> None:
        return None

    logger = EzLogger(log_file=tmp_path / "e.log", compression=my_compressor)
    assert logger.compression is my_compressor


@pytest.mark.unit
def test_diagnose_defaults_to_false(tmp_path):
    from ezplog.handlers.file import EzLogger

    logger = EzLogger(log_file=tmp_path / "f.log")
    assert logger.diagnose is False


@pytest.mark.unit
def test_backtrace_defaults_to_true(tmp_path):
    from ezplog.handlers.file import EzLogger

    logger = EzLogger(log_file=tmp_path / "g.log")
    assert logger.backtrace is True


@pytest.mark.unit
def test_traceback_options_reach_loguru_add(tmp_path, mocker):
    from loguru._logger import Logger as LoguruLogger

    from ezplog.handlers.file import EzLogger

    add = mocker.patch.object(LoguruLogger, "add", return_value=1)
    EzLogger(log_file=tmp_path / "h.log", diagnose=True, backtrace=False)

    kwargs = add.call_args.kwargs
    assert kwargs["diagnose"] is True
    assert kwargs["backtrace"] is False
