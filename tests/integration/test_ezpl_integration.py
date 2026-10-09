# ///////////////////////////////////////////////////////////////
# EZPL - Ezpl integration tests
# Project: ezpl
# ///////////////////////////////////////////////////////////////

"""
Integration tests for Ezpl with Printer and Logger.

Tests cover:
- Ezpl + Printer + Logger working together
- Configuration propagation (singleton)
- Shared indentation
- Global level changes affect both printer and logger
- File rotation with active logging
- Configuration via different channels
"""

from __future__ import annotations

# ///////////////////////////////////////////////////////////////
# IMPORTS
# ///////////////////////////////////////////////////////////////
# Standard library imports
from pathlib import Path

# Third-party imports
import pytest

# Local imports
from ezplog import Ezpl

# ///////////////////////////////////////////////////////////////
# TESTS
# ///////////////////////////////////////////////////////////////


class TestEzplPrinterLoggerIntegration:
    """Tests for Ezpl + Printer + Logger integration."""

    def test_should_provide_both_printer_and_logger_when_ezpl_is_created(
        self, temp_log_file: Path
    ) -> None:
        """Test that Ezpl provides both printer and logger."""
        ezpl = Ezpl(log_file=temp_log_file)
        printer = ezpl.get_printer()
        logger = ezpl.get_logger()

        assert printer is not None
        assert logger is not None
        assert hasattr(printer, "info")
        assert hasattr(logger, "info")

    def test_should_share_indentation_state_when_manage_indent_context_is_active(
        self, temp_log_file: Path
    ) -> None:
        """Test that indentation is shared between printer and logger."""
        ezpl = Ezpl(log_file=temp_log_file)
        printer = ezpl.get_printer()

        with ezpl.manage_indent():
            printer.info("Indented message")
            logger = ezpl.get_logger()
            logger.info("Indented log message")

        # Verify no exception raised
        assert printer._indent == 0

    def test_should_affect_both_printer_and_logger_when_set_level_is_called(
        self, temp_log_file: Path
    ) -> None:
        """Test that set_level() affects both printer and logger."""
        ezpl = Ezpl(log_file=temp_log_file)
        ezpl.set_level("DEBUG")

        printer = ezpl.get_printer()
        logger = ezpl.get_logger()

        # Both should accept DEBUG level
        printer.debug("Debug printer message")
        logger.debug("Debug logger message")

        # Verify no exception raised
        assert printer._level == "DEBUG"
        assert ezpl._logger._level == "DEBUG"

    def test_should_set_only_printer_level_when_set_printer_level_is_called(
        self, temp_log_file: Path
    ) -> None:
        """Test that printer level can be set independently."""
        ezpl = Ezpl(log_file=temp_log_file)
        ezpl.set_printer_level("WARNING")
        ezpl.set_logger_level("DEBUG")

        printer = ezpl.get_printer()

        assert printer._level == "WARNING"
        assert ezpl._logger._level == "DEBUG"

    def test_should_set_only_logger_level_when_set_logger_level_is_called(
        self, temp_log_file: Path
    ) -> None:
        """Test that logger level can be set independently."""
        ezpl = Ezpl(log_file=temp_log_file)
        ezpl.set_printer_level("DEBUG")
        ezpl.set_logger_level("ERROR")

        printer = ezpl.get_printer()

        assert printer._level == "DEBUG"
        assert ezpl._logger._level == "ERROR"

    def test_should_propagate_config_to_same_instance_when_singleton_is_reused(
        self, temp_log_file: Path
    ) -> None:
        """Test that singleton instance propagates configuration."""
        ezpl1 = Ezpl(log_file=temp_log_file, log_level="DEBUG")
        printer1 = ezpl1.get_printer()

        ezpl2 = Ezpl()  # Should return same instance
        printer2 = ezpl2.get_printer()

        assert ezpl1 is ezpl2
        assert printer1 is printer2

    def test_should_rotate_log_file_when_active_logging_exceeds_threshold(
        self, temp_dir: Path
    ) -> None:
        """Test file rotation while logging is active."""
        log_file = temp_dir / "rotation_active.log"
        ezpl = Ezpl(
            log_file=log_file,
            log_rotation="1 KB",
            log_retention="1 day",
        )

        logger = ezpl.get_logger()

        # Write enough to trigger rotation
        for i in range(100):
            logger.info(f"Test message {i} " * 10)

        # Verify file exists or rotation occurred
        assert log_file.exists() or any(log_file.parent.glob("rotation_active.log.*"))


class TestConfigurationIntegration:
    """Tests for configuration integration."""

    def test_should_apply_config_when_constructor_args_are_given(
        self, temp_log_file: Path
    ) -> None:
        """Test configuration via constructor arguments."""
        ezpl = Ezpl(
            log_file=temp_log_file,
            log_level="WARNING",
            log_rotation="10 MB",
        )

        assert ezpl.get_printer()._level == "WARNING"
        assert ezpl._logger._level == "WARNING"

    def test_should_apply_config_when_configure_method_is_called(
        self, temp_log_file: Path
    ) -> None:
        """Test configuration via configure() method."""
        ezpl = Ezpl(log_file=temp_log_file)
        ezpl.configure(level="DEBUG", log_rotation="5 MB")

        config = ezpl.get_config()
        assert config.get("log-level") == "DEBUG"
        assert config.get("log-rotation") == "5 MB"

    def test_should_reload_config_from_file_when_reload_config_is_invoked(
        self, temp_config_file: Path, temp_log_file: Path
    ) -> None:
        """Test configuration reload."""
        # Create initial config
        import json

        config_data = {"log-level": "INFO"}
        temp_config_file.parent.mkdir(parents=True, exist_ok=True)
        temp_config_file.write_text(json.dumps(config_data), encoding="utf-8")

        # Mock config file path
        with pytest.MonkeyPatch().context() as m:
            m.setattr(
                "ezplog.config.manager.DefaultConfiguration.CONFIG_FILE",
                temp_config_file,
            )
            ezpl = Ezpl(log_file=temp_log_file)
            ezpl.reload_config()
            # Config should be reloaded
            assert ezpl is not None


class TestWizardIntegration:
    """Tests for RichWizard integration with Ezpl."""

    def test_should_expose_wizard_on_printer_when_accessed_via_get_printer(
        self, temp_log_file: Path
    ) -> None:
        """Test that wizard is accessible via printer."""
        ezpl = Ezpl(log_file=temp_log_file)
        printer = ezpl.get_printer()
        wizard = printer.wizard

        assert wizard is not None
        assert hasattr(wizard, "panel")
        assert hasattr(wizard, "table")
        assert hasattr(wizard, "json")

    def test_should_render_wizard_components_when_printer_and_logger_are_both_used(
        self, temp_log_file: Path
    ) -> None:
        """Test wizard usage with printer and logger."""
        ezpl = Ezpl(log_file=temp_log_file)
        printer = ezpl.get_printer()
        logger = ezpl.get_logger()

        # Use wizard for display
        printer.wizard.success_panel("Success", "Operation completed")
        printer.wizard.table([{"Name": "Alice", "Age": 30}], title="Users")

        # Use logger for file
        logger.info("Logged to file")

        # Verify no exception raised
        assert printer is not None
        assert logger is not None
