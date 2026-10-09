# ///////////////////////////////////////////////////////////////
# EZPL - Tests unitaires Protocols
# Project: ezpl
# ///////////////////////////////////////////////////////////////

"""
Unit tests for Protocol type checking.

Tests cover:
- PrinterProtocol conformance
- LoggerProtocol conformance
- Runtime validation with isinstance()
- Type annotations
- Protocol method signatures
"""

from __future__ import annotations

# ///////////////////////////////////////////////////////////////
# IMPORTS
# ///////////////////////////////////////////////////////////////
# Standard library imports
import inspect
from contextlib import AbstractContextManager

# Third-party imports
import pytest

# Local imports
from ezplog import Ezpl
from ezplog.handlers.file import EzLogger
from ezplog.types.protocols import LoggerProtocol, PrinterProtocol

# ///////////////////////////////////////////////////////////////
# TESTS
# ///////////////////////////////////////////////////////////////


class TestPrinterProtocol:
    """Tests for PrinterProtocol conformance."""

    def test_should_conform_to_printer_protocol_when_get_printer_is_called(
        self,
    ) -> None:
        """Test that get_printer() returns a PrinterProtocol-conforming object."""
        ezpl = Ezpl()
        printer = ezpl.get_printer()

        # Runtime check
        assert isinstance(printer, PrinterProtocol)

    def test_should_have_all_core_log_methods_when_printer_is_instantiated(
        self,
    ) -> None:
        """Test that printer has all core logging methods."""
        ezpl = Ezpl()
        printer = ezpl.get_printer()

        # Check method existence
        assert hasattr(printer, "info")
        assert hasattr(printer, "debug")
        assert hasattr(printer, "success")
        assert hasattr(printer, "warning")
        assert hasattr(printer, "error")
        assert hasattr(printer, "critical")

        # Check they are callable
        assert callable(printer.info)
        assert callable(printer.debug)
        assert callable(printer.success)

    def test_should_have_all_pattern_methods_when_printer_is_instantiated(self) -> None:
        """Test that printer has all pattern methods."""
        ezpl = Ezpl()
        printer = ezpl.get_printer()

        assert hasattr(printer, "tip")
        assert hasattr(printer, "system")
        assert hasattr(printer, "install")
        assert hasattr(printer, "detect")
        assert hasattr(printer, "config")
        assert hasattr(printer, "deps")

    def test_should_have_all_indent_methods_when_printer_is_instantiated(self) -> None:
        """Test that printer has indentation management methods."""
        ezpl = Ezpl()
        printer = ezpl.get_printer()

        assert hasattr(printer, "add_indent")
        assert hasattr(printer, "del_indent")
        assert hasattr(printer, "reset_indent")
        assert hasattr(printer, "manage_indent")

    def test_should_have_wizard_property_when_printer_is_instantiated(self) -> None:
        """Test that printer has wizard property."""
        ezpl = Ezpl()
        printer = ezpl.get_printer()

        assert hasattr(printer, "wizard")
        wizard = printer.wizard
        assert wizard is not None


class TestLoggerProtocol:
    """Tests for LoggerProtocol conformance."""

    def test_should_conform_to_logger_protocol_when_get_logger_is_called(self) -> None:
        """Test that get_logger() returns a LoggerProtocol-conforming object."""
        ezpl = Ezpl()
        logger = ezpl.get_logger()

        # Runtime check
        assert isinstance(logger, LoggerProtocol)

    def test_should_have_all_core_log_methods_when_logger_is_instantiated(self) -> None:
        """Test that logger has all core logging methods."""
        ezpl = Ezpl()
        logger = ezpl.get_logger()

        # Check method existence
        assert hasattr(logger, "trace")
        assert hasattr(logger, "debug")
        assert hasattr(logger, "info")
        assert hasattr(logger, "success")
        assert hasattr(logger, "warning")
        assert hasattr(logger, "error")
        assert hasattr(logger, "critical")
        assert hasattr(logger, "exception")

        # Check they are callable
        assert callable(logger.info)
        assert callable(logger.debug)
        assert callable(logger.error)

    def test_should_have_bind_opt_and_patch_methods_when_logger_is_instantiated(
        self,
    ) -> None:
        """Test that logger has loguru-specific methods."""
        ezpl = Ezpl()
        logger = ezpl.get_logger()

        assert hasattr(logger, "bind")
        assert hasattr(logger, "opt")
        assert hasattr(logger, "patch")

    def test_should_have_set_level_and_separator_methods_when_logger_is_instantiated(
        self,
    ) -> None:
        """Test that logger has Ezpl-specific methods."""
        ezpl = Ezpl()
        logger = ezpl.get_logger()

        assert hasattr(logger, "set_level")
        assert hasattr(logger, "log")
        assert hasattr(logger, "add_separator")
        assert hasattr(logger, "get_log_file")
        assert hasattr(logger, "close")

    def test_should_not_crash_when_all_core_logger_methods_are_called(self) -> None:
        """Test that logger methods actually work."""
        ezpl = Ezpl()
        logger = ezpl.get_logger()

        # These should not raise exceptions
        logger.info("Test info")
        logger.debug("Test debug")
        logger.success("Test success")
        logger.error("Test error")


class TestProtocolTypeAnnotations:
    """Tests for type annotations with protocols."""

    def test_should_accept_printer_argument_when_function_uses_printer_protocol_annotation(
        self,
    ) -> None:
        """Test function accepting PrinterProtocol."""

        def process(printer: PrinterProtocol) -> None:
            printer.info("Processing")
            printer.success("Done")

        ezpl = Ezpl()
        # Should work without type errors
        process(ezpl.get_printer())

    def test_should_accept_logger_argument_when_function_uses_logger_protocol_annotation(
        self,
    ) -> None:
        """Test function accepting LoggerProtocol."""

        def log_process(logger: LoggerProtocol) -> None:
            logger.info("Starting")
            logger.success("Completed")

        ezpl = Ezpl()
        # Should work without type errors
        log_process(ezpl.get_logger())

    def test_should_not_crash_when_function_accepts_both_printer_and_logger_protocols(
        self,
    ) -> None:
        """Test function accepting both protocols."""

        def dual_log(printer: PrinterProtocol, logger: LoggerProtocol) -> None:
            printer.info("Console message")
            logger.info("File message")

        ezpl = Ezpl()
        dual_log(ezpl.get_printer(), ezpl.get_logger())


class TestProtocolInheritance:
    """Tests for protocol inheritance and extension."""

    def test_should_have_all_required_protocol_methods_when_printer_is_validated(
        self,
    ) -> None:
        """Test that protocols can be used for custom implementations."""
        # This test verifies that the protocol is properly defined
        # and can be used to validate custom implementations

        ezpl = Ezpl()
        printer = ezpl.get_printer()

        # Should conform to protocol
        assert isinstance(printer, PrinterProtocol)

        # Should have all required methods
        required_methods = [
            "info",
            "debug",
            "success",
            "warning",
            "error",
            "critical",
            "tip",
            "system",
            "install",
            "detect",
            "config",
            "deps",
            "print_pattern",
            "print_json",
            "add_indent",
            "del_indent",
            "reset_indent",
            "manage_indent",
        ]

        for method in required_methods:
            assert hasattr(printer, method), f"Missing method: {method}"
            assert callable(getattr(printer, method)), f"Method not callable: {method}"

    def test_should_have_all_required_protocol_methods_when_logger_is_validated(
        self,
    ) -> None:
        """Test that LoggerProtocol can validate custom implementations."""
        ezpl = Ezpl()
        logger = ezpl.get_logger()

        # Should conform to protocol
        assert isinstance(logger, LoggerProtocol)

        # Should have all required methods
        required_methods = [
            "trace",
            "debug",
            "info",
            "success",
            "warning",
            "error",
            "critical",
            "exception",
            "bind",
            "opt",
            "patch",
            "set_level",
            "log",
            "add_separator",
            "get_log_file",
            "close",
        ]

        for method in required_methods:
            assert hasattr(logger, method), f"Missing method: {method}"


@pytest.mark.unit
def test_ez_printer_satisfies_printer_protocol():
    from ezplog.handlers.console import EzPrinter
    from ezplog.types import PrinterProtocol

    printer: PrinterProtocol = EzPrinter(level="DEBUG")
    assert isinstance(printer, PrinterProtocol)


@pytest.mark.unit
def test_lazy_printer_exposes_new_methods():
    from ezplog.lib_mode import _LazyPrinter

    proxy = _LazyPrinter()
    assert hasattr(proxy, "trace")
    assert hasattr(proxy, "exception")


@pytest.mark.unit
def test_lazy_printer_forwards_args_and_exc_info(mocker):
    from ezplog.lib_mode import _LazyPrinter

    proxy = _LazyPrinter()
    real = mocker.Mock()
    mocker.patch.object(_LazyPrinter, "_get_real", return_value=real)

    proxy.info("v={}", 1)
    real.info.assert_called_once_with("v={}", 1)

    proxy.error("boum", exc_info=True)
    real.error.assert_called_once_with("boum", exc_info=True)

    proxy.trace("t")
    real.trace.assert_called_once_with("t")

    proxy.exception("e")
    real.exception.assert_called_once_with("e")


@pytest.mark.unit
def test_lazy_printer_new_methods_are_silent_when_uninitialized():
    from ezplog.lib_mode import _LazyPrinter

    proxy = _LazyPrinter()
    proxy.trace("silencieux")
    proxy.exception("silencieux")


class TestStrictSignatureAlignment:
    """Strict signature checks between protocols and implementations."""

    def test_should_return_context_manager_when_manage_indent_is_called_on_printer(
        self,
    ) -> None:
        """manage_indent should provide a context manager compatible with protocol."""
        ezpl = Ezpl()
        printer = ezpl.get_printer()
        manage_indent_context = printer.manage_indent()
        assert isinstance(manage_indent_context, AbstractContextManager)

    def test_should_have_matching_signatures_when_logger_bind_opt_patch_are_compared_to_protocol(
        self,
    ) -> None:
        """bind/opt/patch signatures should be strictly identical."""
        for method_name in ("bind", "opt", "patch"):
            protocol_method = getattr(LoggerProtocol, method_name)
            implementation_method = getattr(EzLogger, method_name)
            assert str(inspect.signature(protocol_method)) == str(
                inspect.signature(implementation_method)
            )
