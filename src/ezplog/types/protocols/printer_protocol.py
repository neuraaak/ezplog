# ///////////////////////////////////////////////////////////////
# EZPL - Printer Protocol
# Project: ezpl
# ///////////////////////////////////////////////////////////////

"""
Printer Protocol for Ezpl logging framework.

This module defines the Protocol (abstract interface) that all printer
implementations must follow. It provides type checking and ensures
consistent API across different printer implementations.
"""

from __future__ import annotations

# ///////////////////////////////////////////////////////////////
# IMPORTS
# ///////////////////////////////////////////////////////////////
# Standard library imports
from contextlib import AbstractContextManager
from typing import Any, Protocol, runtime_checkable

# Local imports
from ..enums import Pattern

# ///////////////////////////////////////////////////////////////
# PROTOCOLS
# ///////////////////////////////////////////////////////////////


@runtime_checkable
class PrinterProtocol(Protocol):
    """
    Protocol defining the interface for printer implementations.

    All printer implementations must conform to this protocol to ensure
    consistent API and type safety.

    **Required Methods:**
        - Logging methods: info(), debug(), success(), warning(), error(), critical()
        - Pattern methods: tip(), system(), install(), detect(), config(), deps()
        - Enhanced methods: print_pattern(), print_json()
        - Utility methods: set_level(), log()
        - Indentation methods: add_indent(), del_indent(), reset_indent(), manage_indent()

    **Required Properties:**
        - wizard: Access to RichWizard instance for advanced features
    """

    # ///////////////////////////////////////////////////////////////
    # CORE LOGGING METHODS
    # ///////////////////////////////////////////////////////////////

    def trace(self, message: Any, *args: Any, **kwargs: Any) -> None:
        """Log a trace message."""
        ...

    def info(self, message: Any, *args: Any, **kwargs: Any) -> None:
        """Log an informational message."""
        ...

    def debug(self, message: Any, *args: Any, **kwargs: Any) -> None:
        """Log a debug message."""
        ...

    def success(self, message: Any, *args: Any, **kwargs: Any) -> None:
        """Log a success message."""
        ...

    def warning(self, message: Any, *args: Any, **kwargs: Any) -> None:
        """Log a warning message."""
        ...

    def error(
        self, message: Any, *args: Any, exc_info: bool = False, **kwargs: Any
    ) -> None:
        """Log an error message, optionally with the active traceback."""
        ...

    def critical(
        self, message: Any, *args: Any, exc_info: bool = False, **kwargs: Any
    ) -> None:
        """Log a critical message, optionally with the active traceback."""
        ...

    def exception(self, message: Any, *args: Any, **kwargs: Any) -> None:
        """Log an error message followed by the active exception traceback."""
        ...

    # ///////////////////////////////////////////////////////////////
    # PATTERN METHODS
    # ///////////////////////////////////////////////////////////////

    def tip(self, message: Any) -> None:
        """Display a tip message."""
        ...

    def system(self, message: Any) -> None:
        """Display a system message."""
        ...

    def install(self, message: Any) -> None:
        """Display an installation message."""
        ...

    def detect(self, message: Any) -> None:
        """Display a detection message."""
        ...

    def config(self, message: Any) -> None:
        """Display a configuration message."""
        ...

    def deps(self, message: Any) -> None:
        """Display a dependencies message."""
        ...

    # ///////////////////////////////////////////////////////////////
    # ENHANCED METHODS
    # ///////////////////////////////////////////////////////////////

    def print_pattern(
        self, pattern: str | Pattern, message: Any, level: str = "INFO"
    ) -> None:
        """Display a message with pattern format."""
        ...

    def print_json(
        self,
        data: str | dict | list,
        title: str | None = None,
        indent: int | None = None,
        highlight: bool = True,
    ) -> None:
        """Display JSON data in formatted way."""
        ...

    # ///////////////////////////////////////////////////////////////
    # UTILITY METHODS
    # ///////////////////////////////////////////////////////////////

    @property
    def level(self) -> str:
        """Get the current logging level."""
        ...

    def set_level(self, level: str) -> None:
        """Set the logging level."""
        ...

    def log(self, level: str, message: Any, *args: Any, **kwargs: Any) -> None:
        """Log a message at the given level."""
        ...

    # ///////////////////////////////////////////////////////////////
    # INDENTATION METHODS
    # ///////////////////////////////////////////////////////////////

    def add_indent(self) -> None:
        """Increase indentation level."""
        ...

    def del_indent(self) -> None:
        """Decrease indentation level."""
        ...

    def reset_indent(self) -> None:
        """Reset indentation to zero."""
        ...

    def manage_indent(self) -> AbstractContextManager[None]:
        """Context manager for temporary indentation."""
        ...

    # ///////////////////////////////////////////////////////////////
    # PROPERTIES
    # ///////////////////////////////////////////////////////////////

    @property
    def wizard(self) -> Any:
        """Get RichWizard instance for advanced features."""
        ...


# ///////////////////////////////////////////////////////////////
# PUBLIC API
# ///////////////////////////////////////////////////////////////

__all__ = [
    "PrinterProtocol",
]
