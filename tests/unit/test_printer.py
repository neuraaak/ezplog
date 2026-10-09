# ///////////////////////////////////////////////////////////////
# EZPL - Tests unitaires Printer
# Project: ezpl
# ///////////////////////////////////////////////////////////////

"""
Unit tests for EzPrinter.

Tests cover:
- All log levels
- All pattern methods
- Indentation management
- Rich features (tables, panels, JSON)
- Special character handling
- Type conversion
- Error handling
"""

from __future__ import annotations

# ///////////////////////////////////////////////////////////////
# IMPORTS
# ///////////////////////////////////////////////////////////////
# Third-party imports
import pytest

# Local imports
from ezplog import Ezpl
from ezplog.handlers.console import EzPrinter
from ezplog.types import Pattern

# ///////////////////////////////////////////////////////////////
# TESTS
# ///////////////////////////////////////////////////////////////


class TestLogLevels:
    """Tests for all log level methods."""

    def test_should_not_crash_when_debug_message_is_printed(self) -> None:
        """Test debug() method."""
        ezpl = Ezpl()
        printer = ezpl.get_printer()
        printer.debug("Debug message")
        # Verify no exception raised

    def test_should_not_crash_when_info_message_is_printed(self) -> None:
        """Test info() method."""
        ezpl = Ezpl()
        printer = ezpl.get_printer()
        printer.info("Info message")
        # Verify no exception raised

    def test_should_not_crash_when_success_message_is_printed(self) -> None:
        """Test success() method."""
        ezpl = Ezpl()
        printer = ezpl.get_printer()
        printer.success("Success message")
        # Verify no exception raised

    def test_should_not_crash_when_warning_message_is_printed(self) -> None:
        """Test warning() method."""
        ezpl = Ezpl()
        printer = ezpl.get_printer()
        printer.warning("Warning message")
        # Verify no exception raised

    def test_should_not_crash_when_warning_message_is_printed_via_warning_method(
        self,
    ) -> None:
        """Test warning() method."""
        ezpl = Ezpl()
        printer = ezpl.get_printer()
        printer.warning("Warn message")
        # Verify no exception raised

    def test_should_not_crash_when_error_message_is_printed(self) -> None:
        """Test error() method."""
        ezpl = Ezpl()
        printer = ezpl.get_printer()
        printer.error("Error message")
        # Verify no exception raised

    def test_should_not_crash_when_critical_message_is_printed(self) -> None:
        """Test critical() method."""
        ezpl = Ezpl()
        printer = ezpl.get_printer()
        printer.critical("Critical message")
        # Verify no exception raised

    def test_should_not_crash_when_all_log_levels_are_used_in_sequence(self) -> None:
        """Test all log levels in sequence."""
        ezpl = Ezpl()
        printer = ezpl.get_printer()
        printer.debug("Debug message")
        printer.info("Info message")
        printer.success("Success message")
        printer.warning("Warning message")
        printer.error("Error message")
        printer.critical("Critical message")
        # Verify no exception raised


class TestPatternMethods:
    """Tests for all pattern methods."""

    def test_should_not_crash_when_tip_pattern_is_used(self) -> None:
        """Test tip() pattern method."""
        ezpl = Ezpl()
        printer = ezpl.get_printer()
        printer.tip("Tip message")
        # Verify no exception raised

    def test_should_not_crash_when_system_pattern_is_used(self) -> None:
        """Test system() pattern method."""
        ezpl = Ezpl()
        printer = ezpl.get_printer()
        printer.system("System message")
        # Verify no exception raised

    def test_should_not_crash_when_install_pattern_is_used(self) -> None:
        """Test install() pattern method."""
        ezpl = Ezpl()
        printer = ezpl.get_printer()
        printer.install("Install message")
        # Verify no exception raised

    def test_should_not_crash_when_detect_pattern_is_used(self) -> None:
        """Test detect() pattern method."""
        ezpl = Ezpl()
        printer = ezpl.get_printer()
        printer.detect("Detect message")
        # Verify no exception raised

    def test_should_not_crash_when_config_pattern_is_used(self) -> None:
        """Test config() pattern method."""
        ezpl = Ezpl()
        printer = ezpl.get_printer()
        printer.config("Config message")
        # Verify no exception raised

    def test_should_not_crash_when_deps_pattern_is_used(self) -> None:
        """Test deps() pattern method."""
        ezpl = Ezpl()
        printer = ezpl.get_printer()
        printer.deps("Deps message")
        # Verify no exception raised

    def test_should_not_crash_when_all_patterns_are_used_in_sequence(self) -> None:
        """Test all pattern methods in sequence."""
        ezpl = Ezpl()
        printer = ezpl.get_printer()
        printer.tip("Tip")
        printer.system("System")
        printer.install("Install")
        printer.detect("Detect")
        printer.config("Config")
        printer.deps("Deps")
        # Verify no exception raised

    def test_should_not_crash_when_print_pattern_is_called_with_string_pattern(
        self,
    ) -> None:
        """Test print_pattern() with string pattern."""
        ezpl = Ezpl()
        printer = ezpl.get_printer()
        printer.print_pattern("SUCCESS", "Custom pattern message")
        # Verify no exception raised

    def test_should_not_crash_when_print_pattern_is_called_with_enum_pattern(
        self,
    ) -> None:
        """Test print_pattern() with Pattern enum."""
        ezpl = Ezpl()
        printer = ezpl.get_printer()
        printer.print_pattern(Pattern.SUCCESS, "Enum pattern message")
        # Verify no exception raised


class TestIndentation:
    """Tests for indentation management."""

    def test_should_return_string_when_get_indent_is_called(self) -> None:
        """Test get_indent() returns indentation string."""
        ezpl = Ezpl()
        printer = ezpl.get_printer()
        indent = printer.get_indent()
        assert isinstance(indent, str)

    def test_should_increment_indent_level_when_add_indent_is_called(self) -> None:
        """Test add_indent() increases indentation level."""
        ezpl = Ezpl()
        printer = ezpl.get_printer()
        initial_indent = printer._indent
        printer.add_indent()
        assert printer._indent == initial_indent + 1

    def test_should_decrement_indent_level_when_del_indent_is_called(self) -> None:
        """Test del_indent() decreases indentation level."""
        ezpl = Ezpl()
        printer = ezpl.get_printer()
        printer.add_indent()
        initial_indent = printer._indent
        printer.del_indent()
        assert printer._indent == initial_indent - 1

    def test_should_not_go_below_zero_when_del_indent_is_called_at_zero(self) -> None:
        """Test del_indent() does not go below zero."""
        ezpl = Ezpl()
        printer = ezpl.get_printer()
        printer.reset_indent()
        printer.del_indent()
        assert printer._indent >= 0

    def test_should_reset_indent_to_zero_when_reset_indent_is_called(self) -> None:
        """Test reset_indent() sets indentation to zero."""
        ezpl = Ezpl()
        printer = ezpl.get_printer()
        printer.add_indent()
        printer.add_indent()
        printer.reset_indent()
        assert printer._indent == 0

    def test_should_increment_then_restore_indent_when_manage_indent_context_exits(
        self,
    ) -> None:
        """Test manage_indent() context manager."""
        ezpl = Ezpl()
        printer = ezpl.get_printer()
        initial_indent = printer._indent

        with ezpl.manage_indent():
            assert printer._indent == initial_indent + 1

        assert printer._indent == initial_indent

    def test_should_track_nested_levels_when_multiple_manage_indent_contexts_are_used(
        self,
    ) -> None:
        """Test nested manage_indent() context managers."""
        ezpl = Ezpl()
        printer = ezpl.get_printer()
        initial_indent = printer._indent

        with ezpl.manage_indent():
            assert printer._indent == initial_indent + 1
            with ezpl.manage_indent():
                assert printer._indent == initial_indent + 2
            assert printer._indent == initial_indent + 1
        assert printer._indent == initial_indent

    def test_should_cap_indent_at_max_when_add_indent_exceeds_maximum(self) -> None:
        """Test that indentation is limited to MAX_INDENT."""
        ezpl = Ezpl()
        printer = ezpl.get_printer()
        printer.reset_indent()

        # Try to add more than MAX_INDENT
        for _ in range(20):
            printer.add_indent()

        # Indentation should be limited to MAX_INDENT (10)
        assert printer._indent <= 10

    def test_should_not_crash_when_messages_are_printed_with_varying_indent_levels(
        self,
    ) -> None:
        """Test indentation with actual messages."""
        ezpl = Ezpl()
        printer = ezpl.get_printer()
        printer.info("Level 0")
        with ezpl.manage_indent():
            printer.info("Level 1")
            with ezpl.manage_indent():
                printer.info("Level 2")
        printer.info("Back to level 0")
        # Verify no exception raised


class TestRichFeatures:
    """Tests for Rich-specific features."""

    def test_should_not_crash_when_print_table_receives_list_of_dicts(self) -> None:
        """Test print_table() with list of dictionaries."""
        ezpl = Ezpl()
        printer = ezpl.get_printer()
        data = [
            {"Name": "Alice", "Age": 30},
            {"Name": "Bob", "Age": 25},
        ]
        printer.print_table(data)
        # Verify no exception raised

    def test_should_not_crash_when_print_table_receives_title(self) -> None:
        """Test print_table() with title."""
        ezpl = Ezpl()
        printer = ezpl.get_printer()
        data = [{"Name": "Alice", "Age": 30}]
        printer.print_table(data, title="Users")
        # Verify no exception raised

    def test_should_not_crash_when_print_panel_is_called_with_basic_content(
        self,
    ) -> None:
        """Test print_panel() basic usage."""
        ezpl = Ezpl()
        printer = ezpl.get_printer()
        printer.print_panel("Important message")
        # Verify no exception raised

    def test_should_not_crash_when_print_panel_receives_title(self) -> None:
        """Test print_panel() with title."""
        ezpl = Ezpl()
        printer = ezpl.get_printer()
        printer.print_panel("Important message", title="Alert")
        # Verify no exception raised

    def test_should_not_crash_when_print_panel_receives_custom_style(self) -> None:
        """Test print_panel() with custom style."""
        ezpl = Ezpl()
        printer = ezpl.get_printer()
        printer.print_panel("Important message", title="Alert", style="red")
        # Verify no exception raised

    def test_should_not_crash_when_print_json_receives_dict(self) -> None:
        """Test print_json() with dictionary."""
        ezpl = Ezpl()
        printer = ezpl.get_printer()
        printer.print_json({"key": "value", "number": 42})
        # Verify no exception raised

    def test_should_not_crash_when_print_json_receives_list(self) -> None:
        """Test print_json() with list."""
        ezpl = Ezpl()
        printer = ezpl.get_printer()
        printer.print_json([1, 2, 3, {"nested": "value"}])
        # Verify no exception raised

    def test_should_not_crash_when_print_json_receives_json_string(self) -> None:
        """Test print_json() with JSON string."""
        ezpl = Ezpl()
        printer = ezpl.get_printer()
        printer.print_json('{"key": "value"}')
        # Verify no exception raised

    def test_should_not_crash_when_print_json_receives_title(self) -> None:
        """Test print_json() with title."""
        ezpl = Ezpl()
        printer = ezpl.get_printer()
        printer.print_json({"key": "value"}, title="Config")
        # Verify no exception raised

    def test_should_not_crash_when_print_json_receives_custom_indent(self) -> None:
        """Test print_json() with custom indent."""
        ezpl = Ezpl()
        printer = ezpl.get_printer()
        printer.print_json({"key": "value"}, indent=4)
        # Verify no exception raised

    def test_should_return_wizard_with_panel_table_and_json_when_wizard_property_is_accessed(
        self,
    ) -> None:
        """Test wizard property returns RichWizard instance."""
        ezpl = Ezpl()
        printer = ezpl.get_printer()
        wizard = printer.wizard
        assert wizard is not None
        assert hasattr(wizard, "panel")
        assert hasattr(wizard, "table")
        assert hasattr(wizard, "json")


class TestSpecialCharacters:
    """Tests for special character handling."""

    def test_should_not_crash_when_message_contains_windows_path_backslashes(
        self,
    ) -> None:
        """Test printer with Windows path containing backslashes."""
        ezpl = Ezpl()
        printer = ezpl.get_printer()
        printer.error("Path: C:\\Users\\Test\\file.txt")
        # Verify no exception raised

    def test_should_not_crash_when_message_contains_braces_and_tags(self) -> None:
        """Test printer with braces and tags."""
        ezpl = Ezpl()
        printer = ezpl.get_printer()
        printer.error("Message with {braces} and <tags>")
        # Verify no exception raised

    def test_should_not_crash_when_message_contains_unicode_characters(self) -> None:
        """Test printer with Unicode characters."""
        ezpl = Ezpl()
        printer = ezpl.get_printer()
        printer.error("Unicode: éèàçô 漢字 🚀")
        # Verify no exception raised

    def test_should_not_crash_when_message_contains_ansi_escape_codes(self) -> None:
        """Test printer with ANSI escape sequences."""
        ezpl = Ezpl()
        printer = ezpl.get_printer()
        printer.error("ANSI: \x1b[31mRed\x1b[0m")
        # Verify no exception raised


class TestTypeConversion:
    """Tests for automatic type conversion."""

    def test_should_not_crash_when_dict_is_passed_as_message(self) -> None:
        """Test printer with dictionary message."""
        ezpl = Ezpl()
        printer = ezpl.get_printer()
        printer.info({"key": "value"})
        # Verify no exception raised

    def test_should_not_crash_when_integer_is_passed_as_message(self) -> None:
        """Test printer with integer message."""
        ezpl = Ezpl()
        printer = ezpl.get_printer()
        printer.info(12345)
        # Verify no exception raised

    def test_should_not_crash_when_list_is_passed_as_message(self) -> None:
        """Test printer with list message."""
        ezpl = Ezpl()
        printer = ezpl.get_printer()
        printer.info(["list", "items"])
        # Verify no exception raised

    def test_should_not_crash_when_exception_is_passed_as_message(self) -> None:
        """Test printer with exception object."""
        ezpl = Ezpl()
        printer = ezpl.get_printer()
        try:
            _ = 1 / 0  # noqa: B018
        except Exception as exc:
            printer.error(exc)
            printer.error(f"Exception: {exc}")
        # Verify no exception raised

    def test_should_not_crash_when_none_is_passed_as_message(self) -> None:
        """Test printer with None message."""
        ezpl = Ezpl()
        printer = ezpl.get_printer()
        printer.info(None)
        # Verify no exception raised

    def test_should_not_crash_when_custom_object_is_passed_as_message(self) -> None:
        """Test printer with custom object."""
        ezpl = Ezpl()
        printer = ezpl.get_printer()

        class CustomObject:
            def __str__(self):
                return "CustomObject"

        printer.info(CustomObject())
        # Verify no exception raised


@pytest.mark.unit
def test_apply_format_positional(capsys):
    printer = EzPrinter(level="DEBUG")
    printer.info("valeur={}", 42)
    assert "valeur=42" in capsys.readouterr().out


@pytest.mark.unit
def test_apply_format_keyword(capsys):
    printer = EzPrinter(level="DEBUG")
    printer.info("user={user}", user="alice")
    assert "user=alice" in capsys.readouterr().out


@pytest.mark.unit
def test_apply_format_without_args_is_literal(capsys):
    printer = EzPrinter(level="DEBUG")
    printer.info("accolades {litterales} conservees")
    assert "{litterales}" in capsys.readouterr().out


@pytest.mark.unit
def test_apply_format_malformed_falls_back_to_raw(capsys):
    printer = EzPrinter(level="DEBUG")
    printer.info("accolade non fermee {", 1)
    assert "accolade non fermee {" in capsys.readouterr().out


@pytest.mark.unit
def test_apply_format_missing_key_falls_back_to_raw(capsys):
    printer = EzPrinter(level="DEBUG")
    printer.info("valeur={absente}", autre=1)
    assert "{absente}" in capsys.readouterr().out


@pytest.mark.unit
def test_log_accepts_trace_level(capsys):
    printer = EzPrinter(level="TRACE")
    printer.log("TRACE", "message de trace")
    assert "message de trace" in capsys.readouterr().out


@pytest.mark.unit
def test_trace_is_displayed_at_trace_level(capsys):
    printer = EzPrinter(level="TRACE")
    printer.trace("message de trace")
    assert "message de trace" in capsys.readouterr().out


@pytest.mark.unit
def test_trace_is_filtered_at_info_level(capsys):
    printer = EzPrinter(level="INFO")
    printer.trace("message de trace")
    assert "message de trace" not in capsys.readouterr().out


@pytest.mark.unit
def test_exception_renders_traceback_inside_except(capsys):
    printer = EzPrinter(level="DEBUG")
    try:
        raise ValueError("boum")
    except ValueError:
        printer.exception("echec du traitement")
    out = capsys.readouterr().out
    assert "echec du traitement" in out
    assert "ValueError" in out


@pytest.mark.unit
def test_exception_outside_except_does_not_raise(capsys):
    printer = EzPrinter(level="DEBUG")
    printer.exception("pas d'exception active")
    out = capsys.readouterr().out
    assert "pas d'exception active" in out
    assert "Traceback" not in out


@pytest.mark.unit
def test_error_with_exc_info_renders_traceback(capsys):
    printer = EzPrinter(level="DEBUG")
    try:
        raise KeyError("absente")
    except KeyError:
        printer.error("cle manquante", exc_info=True)
    out = capsys.readouterr().out
    assert "cle manquante" in out
    assert "KeyError" in out


@pytest.mark.unit
def test_error_without_exc_info_has_no_traceback(capsys):
    printer = EzPrinter(level="DEBUG")
    try:
        raise KeyError("absente")
    except KeyError:
        printer.error("cle manquante")
    out = capsys.readouterr().out
    assert "cle manquante" in out
    assert "KeyError" not in out
