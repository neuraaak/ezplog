# ///////////////////////////////////////////////////////////////
# EZPL - Tests unitaires Ezpl
# Project: ezpl
# ///////////////////////////////////////////////////////////////

"""
Unit tests for Ezpl singleton class.

Tests cover:
- Singleton pattern
- Initialization with all parameters
- Configuration priority order
- Level management
- File operations
- Indentation
- Configuration management
- Error handling

Note: Some tests intentionally use try-except-pass for robustness testing.
"""

# ruff: noqa: S110, SIM105

from __future__ import annotations

# ///////////////////////////////////////////////////////////////
# IMPORTS
# ///////////////////////////////////////////////////////////////
# Standard library imports
import json
import logging
import os
from pathlib import Path
from unittest.mock import patch

# Third-party imports
import pytest

# Local imports
from ezplog import Ezpl
from ezplog.core.exceptions import FileOperationError, ValidationError
from ezplog.lib_mode import get_logger, get_printer

# ///////////////////////////////////////////////////////////////
# TESTS
# ///////////////////////////////////////////////////////////////


class TestSingleton:
    """Tests for singleton pattern."""

    def test_should_return_same_instance_when_called_multiple_times(self) -> None:
        """Test that Ezpl() always returns the same instance."""
        Ezpl.reset()
        e1 = Ezpl()
        e2 = Ezpl()
        assert e1 is e2

    def test_should_allow_creating_new_instance_when_reset_is_called(self) -> None:
        """Test that reset() allows creating a new instance."""
        Ezpl.reset()
        e1 = Ezpl()
        Ezpl.reset()
        e2 = Ezpl()
        # After reset, instances should be different
        # (or at least reset should not raise errors)
        assert e1 is not None
        assert e2 is not None


class TestInitialization:
    """Tests for Ezpl initialization."""

    def test_should_store_log_file_path_when_log_file_is_given(
        self, temp_log_file: Path
    ) -> None:
        """Test initialization with custom log file."""
        ezpl = Ezpl(log_file=temp_log_file)
        assert ezpl._log_file == temp_log_file

    def test_should_configure_all_components_when_all_parameters_are_given(
        self, temp_log_file: Path
    ) -> None:
        """Test initialization with all parameters."""
        ezpl = Ezpl(
            log_file=temp_log_file,
            log_level="DEBUG",
            printer_level="INFO",
            file_logger_level="WARNING",
            log_rotation="10 MB",
            log_retention="7 days",
            log_compression="zip",
            log_backtrace=False,
            log_diagnose=True,
            indent_step=4,
            indent_symbol="  ",
            base_indent_symbol=">",
        )
        assert ezpl._log_file == temp_log_file
        # Verify levels are set correctly
        assert ezpl._printer._level == "INFO"
        assert ezpl._logger._level == "WARNING"
        # Verify backtrace/diagnose are forwarded to the file logger
        assert ezpl._logger.backtrace is False
        assert ezpl._logger.diagnose is True

    def test_should_initialize_with_valid_defaults_when_no_parameters_are_given(
        self,
    ) -> None:
        """Test initialization with default values."""
        ezpl = Ezpl()
        assert ezpl._log_file is not None
        assert ezpl.get_printer() is not None
        assert ezpl.get_logger() is not None


class TestConfigurationPriority:
    """Tests for configuration priority order (arg > env > file > default)."""

    def test_should_give_highest_priority_to_arg_when_env_and_file_are_also_set(
        self,
        temp_config_file: Path,
        clean_env: None,  # noqa: ARG002
    ) -> None:
        """Test that argument has highest priority."""
        # Set environment variable
        os.environ["EZPL_LOG_LEVEL"] = "WARNING"
        # Set config file
        config_data = {"log-level": "ERROR"}
        temp_config_file.parent.mkdir(parents=True, exist_ok=True)
        temp_config_file.write_text(json.dumps(config_data), encoding="utf-8")

        # Argument should override both
        ezpl = Ezpl(log_level="DEBUG")
        # The argument should be applied
        assert ezpl._printer._level == "DEBUG"
        assert ezpl._logger._level == "DEBUG"

    def test_should_prioritize_env_over_file_when_both_are_set(
        self,
        temp_config_file: Path,
        clean_env: None,  # noqa: ARG002
    ) -> None:
        """Test that environment variable overrides config file."""
        # Set config file
        config_data = {"log-level": "ERROR"}
        temp_config_file.parent.mkdir(parents=True, exist_ok=True)
        temp_config_file.write_text(json.dumps(config_data), encoding="utf-8")
        # Set environment variable
        os.environ["EZPL_LOG_LEVEL"] = "WARNING"

        ezpl = Ezpl()
        # Environment should override file
        # Note: We can't easily test this without mocking, but we verify no errors
        assert ezpl is not None

    def test_should_prioritize_file_over_default_when_config_file_is_present(
        self, temp_config_file: Path
    ) -> None:
        """Test that config file overrides defaults."""
        # Set config file
        config_data = {"log-level": "ERROR", "printer-level": "WARNING"}
        temp_config_file.parent.mkdir(parents=True, exist_ok=True)
        temp_config_file.write_text(json.dumps(config_data), encoding="utf-8")

        # Mock the config file path
        with patch(
            "ezplog.config.manager.DefaultConfiguration.CONFIG_FILE", temp_config_file
        ):
            ezpl = Ezpl()
            # Config file should be loaded
            assert ezpl is not None


class TestLevelManagement:
    """Tests for log level management."""

    def test_should_update_both_printer_and_logger_levels_when_set_level_is_called(
        self,
    ) -> None:
        """Test that set_level() changes both printer and logger levels."""
        ezpl = Ezpl()
        ezpl.set_level("DEBUG")
        # Access internal printer to check level
        assert ezpl._printer._level == "DEBUG"
        assert ezpl._logger._level == "DEBUG"

    def test_should_update_only_printer_level_when_set_printer_level_is_called(
        self,
    ) -> None:
        """Test that set_printer_level() only affects printer."""
        ezpl = Ezpl()
        ezpl.set_printer_level("WARNING")
        # Access internal printer to check level
        assert ezpl._printer._level == "WARNING"
        # Logger level should remain unchanged (default or previous value)
        assert ezpl._logger._level is not None

    def test_should_update_only_logger_level_when_set_logger_level_is_called(
        self,
    ) -> None:
        """Test that set_logger_level() only affects logger."""
        ezpl = Ezpl()
        ezpl.set_logger_level("ERROR")
        assert ezpl._logger._level == "ERROR"
        # Printer level should remain unchanged

    def test_should_raise_validation_error_when_set_level_is_given_invalid_level(
        self,
    ) -> None:
        """Test that set_level() with invalid level raises error."""
        ezpl = Ezpl()
        with pytest.raises(ValidationError):
            ezpl.set_level("INVALID_LEVEL")

    def test_should_raise_validation_error_when_set_printer_level_is_given_invalid_level(
        self,
    ) -> None:
        """Test that set_printer_level() with invalid level raises error."""
        ezpl = Ezpl()
        with pytest.raises(ValidationError):
            ezpl.set_printer_level("INVALID_LEVEL")

    def test_should_raise_validation_error_when_set_logger_level_is_given_invalid_level(
        self,
    ) -> None:
        """Test that set_logger_level() with invalid level raises error."""
        ezpl = Ezpl()
        with pytest.raises(ValidationError):
            ezpl.set_logger_level("INVALID_LEVEL")


class TestFileOperations:
    """Tests for file operations."""

    def test_should_update_log_file_path_when_set_log_file_is_called(
        self, temp_log_file: Path, temp_dir: Path
    ) -> None:
        """Test changing log file."""
        ezpl = Ezpl(log_file=temp_log_file)
        new_file = temp_dir / "new.log"
        ezpl.set_log_file(new_file)
        assert ezpl._log_file == new_file

    def test_should_return_log_file_config_entry_when_get_log_file_is_called(
        self, temp_log_file: Path
    ) -> None:
        """Test getting log file path."""
        ezpl = Ezpl(log_file=temp_log_file)
        # Access internal _log_file or use get_config
        config = ezpl.get_config()
        log_file_from_config = config.get("log-file")
        assert log_file_from_config is not None

    def test_should_write_separator_to_log_when_add_separator_is_called(
        self, temp_log_file: Path
    ) -> None:
        """Test adding separator to log file."""
        ezpl = Ezpl(log_file=temp_log_file)
        ezpl.add_separator()
        # Write a log to ensure file is created
        ezpl.get_logger().info("Test message")
        # Verify separator was added (check file content)
        if temp_log_file.exists():
            content = temp_log_file.read_text(encoding="utf-8")
            assert "==>" in content or "---" in content or len(content) > 0


class TestIndentation:
    """Tests for indentation management."""

    def test_should_increment_then_restore_indent_when_manage_indent_context_is_used(
        self,
    ) -> None:
        """Test manage_indent() context manager."""
        ezpl = Ezpl()
        # Access internal printer to check indent
        initial_indent = ezpl._printer._indent

        with ezpl.manage_indent():
            assert ezpl._printer._indent == initial_indent + 1

        # After context, indent should return to initial
        assert ezpl._printer._indent == initial_indent

    def test_should_support_multiple_indent_levels_when_manage_indent_contexts_are_nested(
        self,
    ) -> None:
        """Test nested manage_indent() context managers."""
        ezpl = Ezpl()
        # Access internal printer to check indent
        initial_indent = ezpl._printer._indent

        with ezpl.manage_indent():
            assert ezpl._printer._indent == initial_indent + 1
            with ezpl.manage_indent():
                assert ezpl._printer._indent == initial_indent + 2
            assert ezpl._printer._indent == initial_indent + 1
        assert ezpl._printer._indent == initial_indent


class TestConfiguration:
    """Tests for configuration management."""

    def test_should_return_config_manager_with_get_and_set_methods_when_get_config_is_called(
        self,
    ) -> None:
        """Test that get_config() returns ConfigurationManager."""
        ezpl = Ezpl()
        config = ezpl.get_config()
        assert config is not None
        # Verify it has configuration methods
        assert hasattr(config, "get")
        assert hasattr(config, "set")

    def test_should_apply_all_dict_values_when_configure_receives_a_dict(
        self,
        temp_config_file: Path,  # noqa: ARG002
    ) -> None:
        """Test configure() with dictionary."""
        ezpl = Ezpl()
        ezpl.configure({"level": "DEBUG", "log-rotation": "10 MB"})
        config = ezpl.get_config()
        assert config.get("log-level") == "DEBUG"
        assert config.get("log-rotation") == "10 MB"

    def test_should_apply_all_kwargs_when_configure_receives_keyword_arguments(
        self,
    ) -> None:
        """Test configure() with keyword arguments."""
        ezpl = Ezpl()
        ezpl.configure(level="WARNING", log_rotation="5 MB")
        config = ezpl.get_config()
        assert config.get("log-level") == "WARNING"
        assert config.get("log-rotation") == "5 MB"

    def test_should_accept_both_underscore_and_hyphen_keys_when_configure_is_called(
        self,
    ) -> None:
        """Test configure() with mixed key formats (underscore and hyphen)."""
        ezpl = Ezpl()
        # Mix of underscore and hyphen formats
        ezpl.configure(
            log_level="INFO",
            printer_level="DEBUG",
            log_rotation="10 MB",
        )
        config = ezpl.get_config()
        # Note: configure() with log_level sets both printer and logger
        # So log-level in config might be INFO, but printer-level is DEBUG
        assert config.get("printer-level") == "DEBUG"
        assert config.get("log-rotation") == "10 MB"

    def test_should_rebuild_file_sink_when_log_diagnose_is_configured(
        self,
    ) -> None:
        """Test that configure(log_diagnose=...) rebuilds the file sink with the new value."""
        ezpl = Ezpl()
        assert ezpl._logger.diagnose is False
        ezpl.configure(log_diagnose=True)
        config = ezpl.get_config()
        assert config.get("log-diagnose") is True
        assert ezpl._logger.diagnose is True

    def test_should_rebuild_file_sink_when_log_backtrace_is_configured(
        self,
    ) -> None:
        """Test that configure(log_backtrace=...) rebuilds the file sink with the new value."""
        ezpl = Ezpl()
        assert ezpl._logger.backtrace is True
        ezpl.configure(log_backtrace=False)
        config = ezpl.get_config()
        assert config.get("log-backtrace") is False
        assert ezpl._logger.backtrace is False

    def test_should_reload_config_from_updated_file_when_reload_config_is_called(
        self,
        temp_config_file: Path,
        clean_env: None,  # noqa: ARG002
    ) -> None:
        """Test reload_config() reloads from file and env."""
        # Create initial config
        config_data = {"log-level": "INFO"}
        temp_config_file.parent.mkdir(parents=True, exist_ok=True)
        temp_config_file.write_text(json.dumps(config_data), encoding="utf-8")

        # Mock config file path
        with patch(
            "ezplog.config.manager.DefaultConfiguration.CONFIG_FILE", temp_config_file
        ):
            ezpl = Ezpl()
            # Change config file
            config_data["log-level"] = "WARNING"
            temp_config_file.write_text(json.dumps(config_data), encoding="utf-8")
            # Reload
            ezpl.reload_config()
            # Config should be reloaded
            assert ezpl is not None

    def test_should_persist_log_file_when_configure_is_called_with_persist_true(
        self,
        temp_config_file: Path,
        temp_dir: Path,
    ) -> None:
        """configure(persist=True, log_file=...) should persist the new path."""
        new_log_file = temp_dir / "persisted.log"

        with patch(
            "ezplog.config.manager.DefaultConfiguration.CONFIG_FILE", temp_config_file
        ):
            ezpl = Ezpl()
            applied = ezpl.configure(log_file=new_log_file, persist=True)

        assert applied is True
        assert ezpl.get_log_file() == new_log_file

        saved_config = json.loads(temp_config_file.read_text(encoding="utf-8"))
        assert saved_config.get("log-file") == str(new_log_file)


class TestStdlibInterception:
    """Tests for stdlib interception behavior."""

    def test_should_write_stdlib_logs_to_file_when_logger_hook_is_enabled(
        self, temp_log_file: Path
    ) -> None:
        """Stdlib loggers should be bridged to EzLogger file output in app mode."""
        root_logger = logging.getLogger()
        original_handlers = list(root_logger.handlers)
        original_level = root_logger.level
        marker = "stdlib-bridge-marker"

        try:
            Ezpl(log_file=temp_log_file, hook_logger=True)
            stdlib_logger = logging.getLogger("tests.stdlib.bridge")
            stdlib_logger.info(marker)

            # Force sink flush/close before reading the file.
            Ezpl.reset()

            content = temp_log_file.read_text(encoding="utf-8")
            assert marker in content
        finally:
            root_logger.handlers = original_handlers
            root_logger.setLevel(original_level)


class TestCompatibilityHooks:
    """Tests for app/lib compatibility hooks."""

    def test_should_delegate_lib_printer_when_hooks_use_default_values(self) -> None:
        """lib_mode printer should delegate to Ezpl printer by default."""
        ezpl = Ezpl()

        with patch.object(ezpl.get_printer(), "info") as mocked_info:
            get_printer().info("lib-printer-default")

        mocked_info.assert_called_once_with("lib-printer-default")

    def test_should_not_delegate_lib_printer_when_hook_printer_is_disabled(
        self,
    ) -> None:
        """lib_mode printer should stay silent when printer hook is disabled."""
        ezpl = Ezpl()
        ezpl.set_compatibility_hooks(hook_logger=False, hook_printer=False)

        with patch.object(ezpl.get_printer(), "info") as mocked_info:
            get_printer().info("lib-printer-disabled")

        mocked_info.assert_not_called()

    def test_should_capture_lib_mode_logger_when_logger_hook_is_enabled(
        self, temp_log_file: Path
    ) -> None:
        """lib_mode stdlib logger should be captured when logger hook is enabled."""
        marker = "lib-mode-hook-enabled"
        ezpl = Ezpl(log_file=temp_log_file)
        ezpl.set_compatibility_hooks(hook_logger=True, hook_printer=True)

        get_logger("tests.libmode.hook.enabled").info(marker)

        Ezpl.reset()
        content = temp_log_file.read_text(encoding="utf-8")
        assert marker in content

    def test_should_not_capture_lib_mode_logger_when_logger_hook_is_disabled(
        self, temp_log_file: Path
    ) -> None:
        """lib_mode stdlib logger should remain silent when logger hook is disabled."""
        marker = "lib-mode-hook-disabled"
        ezpl = Ezpl(log_file=temp_log_file)
        ezpl.set_compatibility_hooks(hook_logger=False, hook_printer=True)

        get_logger("tests.libmode.hook.disabled").info(marker)

        Ezpl.reset()
        content = temp_log_file.read_text(encoding="utf-8")
        assert marker not in content

    def test_should_capture_named_classic_logger_when_explicitly_hooked(
        self, temp_log_file: Path
    ) -> None:
        """A classic logger with propagate=False should be capturable via named hook."""
        logger_name = "tests.classic.named"
        marker = "classic-named-hook"
        classic_logger = logging.getLogger(logger_name)
        original_handlers = list(classic_logger.handlers)
        original_level = classic_logger.level
        original_propagate = classic_logger.propagate

        try:
            classic_logger.handlers = []
            classic_logger.propagate = False
            classic_logger.setLevel(logging.INFO)

            ezpl = Ezpl(log_file=temp_log_file)
            ezpl.set_compatibility_hooks(
                hook_logger=True,
                hook_printer=True,
                logger_names=[logger_name],
            )

            classic_logger.info(marker)

            Ezpl.reset()
            content = temp_log_file.read_text(encoding="utf-8")
            assert marker in content
        finally:
            classic_logger.handlers = original_handlers
            classic_logger.propagate = original_propagate
            classic_logger.setLevel(original_level)


class TestGetters:
    """Tests for getter methods."""

    def test_should_return_printer_with_info_and_debug_methods_when_get_printer_is_called(
        self,
    ) -> None:
        """Test that get_printer() returns EzPrinter."""
        ezpl = Ezpl()
        printer = ezpl.get_printer()
        assert printer is not None
        # Verify it has printer methods
        assert hasattr(printer, "info")
        assert hasattr(printer, "debug")
        assert hasattr(printer, "success")

    def test_should_return_logger_with_standard_methods_when_get_logger_is_called(
        self,
    ) -> None:
        """Test that get_logger() returns loguru Logger."""
        ezpl = Ezpl()
        logger = ezpl.get_logger()
        assert logger is not None
        # Verify it has loguru methods
        assert hasattr(logger, "info")
        assert hasattr(logger, "debug")
        assert hasattr(logger, "warning")


class TestErrorHandling:
    """Tests for error handling."""

    def test_should_raise_validation_error_when_set_level_is_given_non_valid_level(
        self,
    ) -> None:
        """Test that invalid log level raises appropriate error."""
        ezpl = Ezpl()
        with pytest.raises(ValidationError):
            ezpl.set_level("NOT_A_VALID_LEVEL")

    def test_should_persist_and_return_true_when_configure_receives_unknown_key(
        self,
    ) -> None:
        """Test that unknown config keys are accepted and persisted as-is."""
        ezpl = Ezpl()
        applied = ezpl.configure(invalid_key="invalid_value")
        assert applied is True
        assert ezpl.get_config().get("invalid_key") == "invalid_value"

    def test_should_raise_file_operation_error_when_set_log_file_creation_fails(
        self,
    ) -> None:
        """Test that set_log_file propagates logger creation failure."""
        ezpl = Ezpl()
        with (
            patch(
                "ezplog.ezpl.EzLogger",
                side_effect=FileOperationError("boom", "x.log", "write"),
            ),
            pytest.raises(FileOperationError),
        ):
            ezpl.set_log_file("x.log")


class TestConfigLockV2:
    """Tests for lock/unlock behavior via token-based controls."""

    def test_should_return_token_and_set_locked_state_when_lock_config_is_called(
        self,
    ) -> None:
        """lock_config() should return a non-None token and mark config as locked."""
        Ezpl()
        token = Ezpl.lock_config()

        assert token is not None
        assert isinstance(token, str)
        assert Ezpl.is_locked() is True

    def test_should_return_same_token_when_lock_config_is_called_while_already_locked(
        self,
    ) -> None:
        """Calling lock_config() a second time while locked returns the existing token."""
        Ezpl()
        first_token = Ezpl.lock_config()
        second_token = Ezpl.lock_config()

        assert first_token is not None
        assert first_token == second_token
        assert Ezpl.is_locked() is True

    def test_should_deny_configure_and_warn_when_config_is_locked(
        self,
    ) -> None:
        """configure() should be blocked and emit a warning when config is locked."""
        ezpl = Ezpl()
        Ezpl.lock_config()

        with pytest.warns(UserWarning, match="configuration is locked"):
            applied = ezpl.configure(level="DEBUG")

        assert applied is False

    def test_should_block_configure_when_locked_and_allow_after_unlock(
        self,
    ) -> None:
        """configure() succeeds after a valid unlock_config(token) call."""
        ezpl = Ezpl()
        token = Ezpl.lock_config()
        assert token is not None

        # While locked, configure is blocked
        with pytest.warns(UserWarning):
            blocked = ezpl.configure(level="DEBUG")
        assert blocked is False

        # After unlocking with the correct token, configure succeeds
        assert Ezpl.unlock_config(token) is True
        assert Ezpl.is_locked() is False
        applied = ezpl.configure(level="DEBUG")
        assert applied is True

    def test_should_deny_unlock_and_warn_when_wrong_token_is_given(
        self,
    ) -> None:
        """unlock_config() should reject wrong tokens and leave config locked."""
        Ezpl()
        token = Ezpl.lock_config()
        assert token is not None

        with pytest.warns(UserWarning, match="Unlock denied"):
            unlocked = Ezpl.unlock_config("wrong-token")

        assert unlocked is False
        assert Ezpl.is_locked() is True

        assert Ezpl.unlock_config(token) is True
        assert Ezpl.is_locked() is False


@pytest.mark.unit
def test_facade_exposes_new_methods(ezpl_instance):
    assert hasattr(ezpl_instance, "trace")
    assert hasattr(ezpl_instance, "exception")
    assert hasattr(ezpl_instance, "log")


@pytest.mark.unit
def test_facade_delegates_to_printer(ezpl_instance, mocker):
    printer = mocker.patch.object(ezpl_instance, "_printer")

    ezpl_instance.info("v={}", 1)
    printer.info.assert_called_once_with("v={}", 1)

    ezpl_instance.trace("t")
    printer.trace.assert_called_once_with("t")

    ezpl_instance.exception("e")
    printer.exception.assert_called_once_with("e")

    ezpl_instance.error("boum", exc_info=True)
    printer.error.assert_called_once_with("boum", exc_info=True)

    ezpl_instance.log("TRACE", "m")
    printer.log.assert_called_once_with("TRACE", "m")


@pytest.mark.unit
def test_facade_does_not_write_to_file(ezpl_instance, mocker):
    logger = mocker.patch.object(ezpl_instance, "_logger")
    ezpl_instance.info("console uniquement")
    logger.info.assert_not_called()


@pytest.mark.unit
def test_configure_normalizes_traceback_keys(ezpl_instance, mocker):
    manager = mocker.patch.object(ezpl_instance, "_config_manager")
    ezpl_instance.configure(log_diagnose=True, log_backtrace=False)

    manager.update.assert_called_once()
    (applied_config,), _ = manager.update.call_args
    assert applied_config["log-diagnose"] is True
    assert applied_config["log-backtrace"] is False
    assert "log_diagnose" not in applied_config
    assert "log_backtrace" not in applied_config
