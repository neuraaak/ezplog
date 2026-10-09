# ///////////////////////////////////////////////////////////////
# EZPL - Console Printer Handler
# Project: ezpl
# ///////////////////////////////////////////////////////////////

"""
Console printer handler for Ezpl logging framework.

This module provides a console-based logging handler with advanced formatting,
indentation management, and color support using Rich.
"""

from __future__ import annotations

# ///////////////////////////////////////////////////////////////
# IMPORTS
# ///////////////////////////////////////////////////////////////
# Standard library imports
import sys
from collections.abc import Generator
from contextlib import contextmanager
from typing import Any

# Third-party imports
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.text import Text

# Local imports
from ..core.exceptions import ValidationError
from ..core.interfaces import IndentationManager, LoggingHandler
from ..types.enums import LogLevel, Pattern, get_pattern_color
from ..utils import safe_str_convert, sanitize_for_console
from .wizard import RichWizard

# ///////////////////////////////////////////////////////////////
# CLASSES
# ///////////////////////////////////////////////////////////////


class EzPrinter(LoggingHandler, IndentationManager):
    """
    Console printer handler with advanced formatting and indentation support using Rich.

    This handler provides console-based logging with:
    - Color-coded log levels using Rich
    - Indentation management
    - Robust character handling (Rich handles special characters automatically)
    - Context manager support
    - Pattern-based logging (SUCCESS, ERROR, WARN, TIP, etc.)
    - Access to RichWizard for advanced display features
    """

    _MAX_INDENT = 10  # Maximum indentation level

    # ///////////////////////////////////////////////////////////////
    # INIT
    # ///////////////////////////////////////////////////////////////

    def __init__(
        self,
        level: str = "INFO",
        indent_step: int = 3,
        indent_symbol: str = ">",
        base_indent_symbol: str = "~",
    ) -> None:
        """
        Initialize the console printer handler.

        Args:
            level: The desired logging level
            indent_step: Number of spaces for each indentation level
            indent_symbol: Symbol for indentation levels
            base_indent_symbol: Symbol for the base indentation

        Raises:
            ValidationError: If the provided level is invalid
        """
        if not LogLevel.is_valid_level(level):
            raise ValidationError(f"Invalid log level: {level}", "level", level)

        self._level = level.upper()
        self._level_manually_set = False
        self._indent = 0
        self._indent_step = indent_step
        self._indent_symbol = indent_symbol
        self._base_indent_symbol = base_indent_symbol

        # Initialize Rich Console
        self._console = Console()
        self._level_numeric = LogLevel.get_no(self._level)

        # Initialize Rich Wizard for advanced display features
        self._wizard = RichWizard(self._console)

    # ///////////////////////////////////////////////////////////////
    # UTILS METHODS
    # ///////////////////////////////////////////////////////////////

    @property
    def level(self) -> str:
        """Return the current logging level."""
        return self._level

    @property
    def level_manually_set(self) -> bool:
        """Return whether level was set manually at runtime."""
        return self._level_manually_set

    @property
    def indent_step(self) -> int:
        """Return the configured indentation step."""
        return self._indent_step

    @property
    def indent_symbol(self) -> str:
        """Return the configured indentation symbol."""
        return self._indent_symbol

    @property
    def base_indent_symbol(self) -> str:
        """Return the configured base indentation symbol."""
        return self._base_indent_symbol

    def mark_level_as_configured(self) -> None:
        """Mark the current level as coming from configuration (not manual set)."""
        self._level_manually_set = False

    def set_level(self, level: str) -> None:
        """
        Set the logging level.

        Args:
            level: The desired logging level

        Raises:
            ValidationError: If the provided level is invalid
        """
        if not LogLevel.is_valid_level(level):
            raise ValidationError(f"Invalid log level: {level}", "level", level)

        self._level = level.upper()
        self._level_numeric = LogLevel.get_no(self._level)
        self._level_manually_set = True

    def log(self, level: str, message: Any, *args: Any, **kwargs: Any) -> None:
        """
        Log a message with the specified level.

        Args:
            level: The log level
            message: The message to log (any type, will be safely converted to string)
            *args: Positional arguments for loguru-style `{}` formatting
            **kwargs: Keyword arguments for loguru-style `{}` formatting

        Raises:
            ValidationError: If the level is invalid
        """
        if not LogLevel.is_valid_level(level):
            raise ValidationError(f"Invalid log level: {level}", "level", level)

        # Convert message to string robustly
        message = safe_str_convert(message)
        message = sanitize_for_console(message)
        message = self._apply_format(message, args, kwargs)

        try:
            level_numeric = LogLevel.get_no(level)
            if level_numeric < self._level_numeric:
                return  # Level too low, skip

            # Map log levels to patterns for consistent output
            pattern_map = {
                "TRACE": Pattern.TRACE,
                "DEBUG": Pattern.DEBUG,
                "INFO": Pattern.INFO,
                "SUCCESS": Pattern.SUCCESS,
                "WARNING": Pattern.WARN,
                "ERROR": Pattern.ERROR,
                "CRITICAL": Pattern.ERROR,  # Critical also uses ERROR pattern
            }
            pattern_enum = pattern_map.get(level.upper(), Pattern.INFO)
            self.print_pattern(pattern_enum, message, level)

        except Exception as e:
            # Never raise an exception, just log the error safely
            try:
                self._console.print(
                    f"[bold red]LOGGING ERROR:[/bold red] {type(e).__name__}"
                )
            except Exception as e:
                raise ValueError(f"Failed to print logging error: {e}") from e

    # ///////////////////////////////////////////////////////////////
    # PRIVATE HELPER METHODS
    # ///////////////////////////////////////////////////////////////

    @staticmethod
    def _apply_format(
        message: str, args: tuple[Any, ...], kwargs: dict[str, Any]
    ) -> str:
        """
        Apply loguru-style `{}` formatting when arguments are supplied.

        Returns the message untouched when no arguments are given, so that
        literal braces are preserved. Any formatting failure falls back to the
        raw message: a logging call must never break the caller.
        """
        if not args and not kwargs:
            return message
        try:
            return message.format(*args, **kwargs)
        except (IndexError, KeyError, ValueError):
            return message

    def _print_traceback_if_active(self) -> None:
        """
        Render the active exception traceback, if any.

        `Console.print_exception()` raises when no exception is being handled,
        so the call is guarded. Local variables are never shown: a traceback
        may end up in a log file, and locals routinely hold secrets.
        """
        if sys.exc_info()[0] is None:
            return
        self._console.print_exception(show_locals=False)

    # ///////////////////////////////////////////////////////////////
    # LOGGING METHODS (API primaire)
    # ///////////////////////////////////////////////////////////////

    def info(self, message: Any, *args: Any, **kwargs: Any) -> None:
        """Log an informational message with pattern format."""
        message = self._apply_format(safe_str_convert(message), args, kwargs)
        self.print_pattern(Pattern.INFO, message, "INFO")

    def trace(self, message: Any, *args: Any, **kwargs: Any) -> None:
        """Log a trace message with pattern format."""
        message = self._apply_format(safe_str_convert(message), args, kwargs)
        self.print_pattern(Pattern.TRACE, message, "TRACE")

    def debug(self, message: Any, *args: Any, **kwargs: Any) -> None:
        """Log a debug message with pattern format."""
        message = self._apply_format(safe_str_convert(message), args, kwargs)
        self.print_pattern(Pattern.DEBUG, message, "DEBUG")

    def success(self, message: Any, *args: Any, **kwargs: Any) -> None:
        """Log a success message with pattern format."""
        message = self._apply_format(safe_str_convert(message), args, kwargs)
        self.print_pattern(Pattern.SUCCESS, message, "INFO")

    def warning(self, message: Any, *args: Any, **kwargs: Any) -> None:
        """Log a warning message with pattern format."""
        message = self._apply_format(safe_str_convert(message), args, kwargs)
        self.print_pattern(Pattern.WARN, message, "WARNING")

    def error(
        self, message: Any, *args: Any, exc_info: bool = False, **kwargs: Any
    ) -> None:
        """Log an error message with pattern format.

        Args:
            message: Message to display.
            *args: Positional arguments for `{}` formatting.
            exc_info: If True, also render the active exception traceback.
            **kwargs: Keyword arguments for `{}` formatting.
        """
        message = self._apply_format(safe_str_convert(message), args, kwargs)
        self.print_pattern(Pattern.ERROR, message, "ERROR")
        if exc_info:
            self._print_traceback_if_active()

    def critical(
        self, message: Any, *args: Any, exc_info: bool = False, **kwargs: Any
    ) -> None:
        """Log a critical message with pattern format.

        Args:
            message: Message to display.
            *args: Positional arguments for `{}` formatting.
            exc_info: If True, also render the active exception traceback.
            **kwargs: Keyword arguments for `{}` formatting.
        """
        message = self._apply_format(safe_str_convert(message), args, kwargs)
        self.print_pattern(Pattern.ERROR, message, "CRITICAL")
        if exc_info:
            self._print_traceback_if_active()

    def exception(self, message: Any, *args: Any, **kwargs: Any) -> None:
        """Log an error message followed by the active exception traceback."""
        self.error(message, *args, exc_info=True, **kwargs)

    # ------------------------------------------------
    # ADDITIONAL PATTERN METHODS
    # ------------------------------------------------

    def tip(self, message: Any) -> None:
        """Display a tip message with pattern format."""
        self.print_pattern(Pattern.TIP, message, "INFO")

    def system(self, message: Any) -> None:
        """Display a system message with pattern format."""
        self.print_pattern(Pattern.SYSTEM, message, "INFO")

    def install(self, message: Any) -> None:
        """Display an installation message with pattern format."""
        self.print_pattern(Pattern.INSTALL, message, "INFO")

    def detect(self, message: Any) -> None:
        """Display a detection message with pattern format."""
        self.print_pattern(Pattern.DETECT, message, "INFO")

    def config(self, message: Any) -> None:
        """Display a configuration message with pattern format."""
        self.print_pattern(Pattern.CONFIG, message, "INFO")

    def deps(self, message: Any) -> None:
        """Display a dependencies message with pattern format."""
        self.print_pattern(Pattern.DEPS, message, "INFO")

    def print_pattern(
        self, pattern: str | Pattern, message: Any, level: str = "INFO"
    ) -> None:
        """
        Display a message with pattern format: • PATTERN :: message

        Args:
            pattern: Pattern name (string) or Pattern enum
            message: Message to display
            level: Log level for filtering (default: INFO)
        """
        try:
            # Convert pattern to Pattern enum if string
            if isinstance(pattern, str):
                try:
                    pattern_enum = Pattern[pattern.upper()]
                except KeyError:
                    # If pattern not found, use INFO as default
                    pattern_enum = Pattern.INFO
            else:
                pattern_enum = pattern

            # Check if level should be displayed
            level_numeric = LogLevel.get_no(level)
            if level_numeric < self._level_numeric:
                return  # Level too low, don't display

            # Convert message to string safely and sanitize for console
            message = safe_str_convert(message)
            message = sanitize_for_console(message)

            # Get pattern color
            pattern_color = get_pattern_color(pattern_enum)
            pattern_name = pattern_enum.value

            # Build text with pattern format: • PATTERN :: message
            text = Text()
            text.append("• ", style=pattern_color)
            text.append(pattern_name.ljust(8), style=f"bold {pattern_color}")
            text.append(":: ", style="dim white")

            # Handle indentation - add it just before the message (after ":: ")
            indent_str = self.get_indent()
            if indent_str and indent_str != "~":
                # Add indentation just before the message
                text.append(indent_str, style="dim")
                text.append(" ", style="dim")

            # Add the message
            text.append(str(message), style="white")

            self._console.print(text)

        except Exception as e:
            # Robust error handling: never raise exception
            try:
                error_msg = f"[bold red]PATTERN ERROR:[/bold red] {type(e).__name__}"
                self._console.print(error_msg)
            except Exception as e:
                raise ValueError(f"Failed to print pattern: {e}") from e

    # ///////////////////////////////////////////////////////////////
    # INDENTATION MANAGEMENT
    # ///////////////////////////////////////////////////////////////

    def get_indent(self) -> str:
        """
        Get the current indentation string.

        Returns:
            The current indentation string
        """
        try:
            indent_spaces = " " * (self._indent * self._indent_step)
            if self._indent > 0:
                return f"{indent_spaces}{self._indent_symbol}"
            else:
                return self._base_indent_symbol
        except Exception:
            return "~"  # Safe fallback

    def add_indent(self) -> None:
        """Increase the indentation level by one (with maximum limit)."""
        self._indent = min(self._indent + 1, self._MAX_INDENT)

    def del_indent(self) -> None:
        """Decrease the indentation level by one, ensuring it doesn't go below zero."""
        self._indent = max(0, self._indent - 1)

    def reset_indent(self) -> None:
        """Reset the indentation level to zero."""
        self._indent = 0

    @contextmanager
    def manage_indent(self) -> Generator[None]:
        """
        Context manager for temporary indentation.

        Yields:
            None
        """
        try:
            self.add_indent()
            yield
        finally:
            self.del_indent()

    # ///////////////////////////////////////////////////////////////
    # WIZARD ACCESS
    # ///////////////////////////////////////////////////////////////

    @property
    def wizard(self) -> RichWizard:
        """
        Get the Rich Wizard instance for advanced display features.

        Returns:
            RichWizard instance for panels, tables, JSON, etc.

        Example:
            >>> printer.wizard.success_panel("Success", "Operation completed")
            >>> printer.wizard.status_table("Status", data)
            >>> printer.wizard.dependency_table({"tool": "1.0.0"})
        """
        return self._wizard

    # ///////////////////////////////////////////////////////////////
    # ENHANCED METHODS (Rich features)
    # ///////////////////////////////////////////////////////////////

    def print_table(self, data: list[dict[str, Any]], title: str | None = None) -> None:
        """
        Display a table using Rich (delegates to RichWizard).

        Args:
            data: List of dictionaries representing table rows
            title: Optional table title
        """
        self._wizard.table(data, title=title)

    def print_panel(
        self, content: str, title: str | None = None, style: str = "blue"
    ) -> None:
        """
        Display a panel using Rich (delegates to RichWizard).

        Args:
            content: Panel content
            title: Optional panel title
            style: Panel style (Rich style string, used as border_style)
        """
        self._wizard.panel(content, title=title, border_style=style)

    def print_progress(self, *args, **kwargs) -> None:
        """
        Display a progress bar using Rich.

        Note: This is a placeholder. For full progress functionality,
        users should use Rich's Progress context manager directly.
        """
        try:
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                *args,
                **kwargs,
            ):
                # Placeholder - users should use Rich.Progress context manager directly
                pass
        except Exception as e:
            try:
                self._console.print(f"[red]Progress error:[/red] {type(e).__name__}")
            except Exception as e:
                raise ValueError(f"Failed to print progress: {e}") from e

    def print_json(
        self,
        data: str | dict | list,
        title: str | None = None,
        indent: int | None = None,
        highlight: bool = True,
    ) -> None:
        """
        Display JSON data in a formatted and syntax-highlighted way using Rich (delegates to RichWizard).

        Args:
            data: JSON data to display (dict, list, or JSON string)
            title: Optional title for the JSON display
            indent: Number of spaces for indentation (default: 2)
            highlight: Whether to enable syntax highlighting (default: True)

        Examples:
            >>> printer.print_json({"name": "Alice", "age": 30})
            >>> printer.print_json('{"key": "value"}', title="Config")
            >>> printer.print_json([1, 2, 3], indent=4)
        """
        self._wizard.json(data, title=title, indent=indent, highlight=highlight)

    # ///////////////////////////////////////////////////////////////
    # REPRESENTATION METHODS
    # ///////////////////////////////////////////////////////////////

    def __str__(self) -> str:
        """String representation of the console printer."""
        return f"EzPrinter(level={self._level}, indent={self._indent})"

    def __repr__(self) -> str:
        """Detailed string representation of the console printer."""
        return f"EzPrinter(level={self._level}, indent={self._indent}, indent_step={self._indent_step})"


# ///////////////////////////////////////////////////////////////
# PUBLIC API
# ///////////////////////////////////////////////////////////////

__all__ = [
    "EzPrinter",
]
