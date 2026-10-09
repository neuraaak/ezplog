# ///////////////////////////////////////////////////////////////
# EZPL - Robustness Tests - Edge Cases
# Project: ezpl
# ///////////////////////////////////////////////////////////////

"""
Robustness tests for edge cases.

Tests cover:
- Singleton with threads (if applicable)
- Very large log files
- Rotation with compression
- Invalid configuration
- Invalid file paths
- Invalid log levels
- Excessive indentation

Note: This file intentionally uses try-except-pass for robustness testing.
"""

# ruff: noqa: S110, SIM105

from __future__ import annotations

# ///////////////////////////////////////////////////////////////
# IMPORTS
# ///////////////////////////////////////////////////////////////
# Standard library imports
import sys
import threading
from pathlib import Path

# Third-party imports
import pytest

# Local imports
from ezplog import Ezpl
from ezplog.core.exceptions import FileOperationError, LoggingError, ValidationError

pytestmark = pytest.mark.robustness

# ///////////////////////////////////////////////////////////////
# TESTS
# ///////////////////////////////////////////////////////////////


class TestSingletonEdgeCases:
    """Tests for singleton edge cases."""

    def test_should_return_same_instance_when_multiple_threads_call_ezpl(self) -> None:
        """Test singleton behavior with multiple threads."""
        instances = []

        def get_instance():
            instances.append(Ezpl())

        threads = [threading.Thread(target=get_instance) for _ in range(5)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()

        # All instances should be the same
        assert len({id(inst) for inst in instances}) == 1

    def test_should_not_crash_when_reset_is_called_while_instance_is_used(self) -> None:
        """Test reset() while instance is in use."""
        ezpl1 = Ezpl()
        printer1 = ezpl1.get_printer()

        # Reset while using
        Ezpl.reset()

        # Create new instance
        ezpl2 = Ezpl()
        printer2 = ezpl2.get_printer()

        # Should not crash
        assert printer1 is not None
        assert printer2 is not None


class TestLargeFiles:
    """Tests for very large log files."""

    def test_should_create_log_file_when_many_messages_are_written(
        self, temp_dir: Path
    ) -> None:
        """Test creating a large log file."""
        log_file = temp_dir / "large.log"
        ezpl = Ezpl(log_file=log_file)
        logger = ezpl.get_logger()

        # Write many messages
        for i in range(1000):
            logger.info(f"Message {i} " * 10)

        # Should not crash
        assert log_file.exists()

    def test_should_rotate_log_when_file_exceeds_size_threshold(
        self, temp_dir: Path
    ) -> None:
        """Test rotation with large file."""
        log_file = temp_dir / "large_rotation.log"
        ezpl = Ezpl(
            log_file=log_file,
            log_rotation="1 KB",
            log_retention="1 day",
        )
        logger = ezpl.get_logger()

        # Write enough to trigger multiple rotations
        for i in range(200):
            logger.info(f"Message {i} " * 10)

        # Should not crash
        assert log_file.exists() or any(log_file.parent.glob("large_rotation.log.*"))


class TestInvalidConfiguration:
    """Tests for invalid configuration handling."""

    def test_should_raise_logging_error_when_rotation_format_is_invalid(
        self, temp_log_file: Path
    ) -> None:
        """Loguru validates rotation at init — should raise LoggingError."""
        with pytest.raises(LoggingError):
            Ezpl(log_file=temp_log_file, log_rotation="INVALID_FORMAT")

    def test_should_raise_logging_error_when_retention_format_is_invalid(
        self, temp_log_file: Path
    ) -> None:
        """Loguru validates retention at init — should raise LoggingError."""
        with pytest.raises(LoggingError):
            Ezpl(log_file=temp_log_file, log_retention="INVALID_FORMAT")

    def test_should_raise_validation_error_when_compression_format_is_invalid(
        self, temp_log_file: Path
    ) -> None:
        """EzLogger validates compression at construction — should raise ValidationError."""
        with pytest.raises(ValidationError):
            Ezpl(log_file=temp_log_file, log_compression="INVALID_FORMAT")

    def test_should_succeed_when_indent_step_is_negative(self) -> None:
        """EzPrinter does not validate indent_step — Ezpl init should succeed."""
        ezpl = Ezpl(indent_step=-1)
        assert ezpl is not None


class TestInvalidPaths:
    """Tests for invalid file path handling."""

    def test_should_raise_error_when_path_contains_invalid_windows_characters(
        self,
    ) -> None:
        """Invalid path characters should raise on Windows only."""
        invalid_path = Path('test<>:"|?*.log')
        if sys.platform == "win32":
            with pytest.raises((OSError, FileOperationError)):
                _ = Ezpl(log_file=invalid_path)
        else:
            ezpl = Ezpl(log_file=invalid_path)
            assert ezpl is not None

    def test_should_raise_error_when_path_exceeds_maximum_length(self) -> None:
        """Excessively long paths should raise FileOperationError or OSError."""
        long_path = Path("A" * 300) / "test.log"
        with pytest.raises((OSError, FileOperationError)):
            _ = Ezpl(log_file=long_path)

    def test_should_create_parent_directory_automatically_when_it_does_not_exist(
        self, temp_dir: Path
    ) -> None:
        """Test handling of nonexistent parent directory."""
        # Should create directory automatically
        log_file = temp_dir / "nonexistent" / "subdir" / "test.log"
        ezpl = Ezpl(log_file=log_file)
        logger = ezpl.get_logger()
        logger.info("Test")
        # Directory should have been created automatically
        assert log_file.parent.exists()


class TestInvalidLogLevels:
    """Tests for invalid log level handling."""

    def test_should_raise_validation_error_when_log_level_is_empty_string(self) -> None:
        """Empty string is not a valid log level — should raise ValidationError."""
        ezpl = Ezpl()
        with pytest.raises(ValidationError):
            ezpl.set_level("")

    def test_should_raise_error_when_log_level_is_none(self) -> None:
        """None is not a valid log level — should raise AttributeError or ValidationError."""
        ezpl = Ezpl()
        with pytest.raises((AttributeError, ValidationError)):
            ezpl.set_level(None)  # type: ignore[arg-type]

    def test_should_raise_error_when_log_level_is_an_integer(self) -> None:
        """Integer is not a valid log level — should raise AttributeError or ValidationError."""
        ezpl = Ezpl()
        with pytest.raises((AttributeError, ValidationError)):
            ezpl.set_level(42)  # type: ignore[arg-type]


class TestExcessiveIndentation:
    """Tests for excessive indentation handling."""

    def test_should_cap_indent_at_max_when_add_indent_is_called_excessively(
        self,
    ) -> None:
        """Test that excessive indent adds are limited."""
        ezpl = Ezpl()
        printer = ezpl.get_printer()

        # Try to add way more than MAX_INDENT
        for _ in range(100):
            printer.add_indent()

        # Should be limited to MAX_INDENT (10)
        assert printer._indent <= 10

    def test_should_cap_indent_at_max_when_nested_context_managers_exceed_limit(
        self,
    ) -> None:
        """Test excessive nested indentation."""
        ezpl = Ezpl()
        printer = ezpl.get_printer()

        # Try deeply nested context managers
        for _ in range(20):
            with ezpl.manage_indent():
                pass

        # Should be limited
        assert printer._indent <= 10


class TestRotationEdgeCases:
    """Tests for rotation edge cases."""

    def test_should_rotate_and_compress_log_when_rotation_and_compression_are_enabled(
        self, temp_dir: Path
    ) -> None:
        """Test rotation with compression enabled."""
        log_file = temp_dir / "rotation_compressed.log"
        ezpl = Ezpl(
            log_file=log_file,
            log_rotation="1 KB",
            log_retention="1 day",
            log_compression="zip",
        )
        logger = ezpl.get_logger()

        # Write enough to trigger rotation
        for i in range(100):
            logger.info(f"Message {i} " * 10)

        # Should not crash
        assert log_file.exists() or any(
            log_file.parent.glob("rotation_compressed.log.*.zip")
        )

    def test_should_not_crash_when_log_message_equals_rotation_threshold_size(
        self, temp_dir: Path
    ) -> None:
        """Test rotation at exact size threshold."""
        log_file = temp_dir / "exact_size.log"
        ezpl = Ezpl(
            log_file=log_file,
            log_rotation="1 KB",
            log_retention="1 day",
        )
        logger = ezpl.get_logger()

        # Write exactly 1 KB
        message = "A" * 1024
        logger.info(message)

        # Should not crash
        assert log_file.exists()
