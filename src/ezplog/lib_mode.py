# ///////////////////////////////////////////////////////////////
# LIB_MODE - Passive stdlib-compatible logger and printer for library authors
# Project: ezpl
# ///////////////////////////////////////////////////////////////

"""
Passive logger and printer proxies for library authors.

Libraries should never configure logging or printing themselves. Use the
functions below to obtain objects that are silent by default and automatically
active once the host application initializes Ezpl.

Recommended imports for library code:

    from ezpl.lib_mode import get_logger, get_printer

These imports are intentionally lightweight — no dependency on rich or loguru
is triggered at import time. The lazy delegation happens at call time only.

Usage pattern in a library:

    from ezpl.lib_mode import get_logger, get_printer

    log = get_logger(__name__)       # stdlib Logger, silent by default
    printer = get_printer()          # lazy EzPrinter proxy, silent by default

    def initialize():
        log.info("Service ready")        # captured if app enables logger hooks
        printer.success("Service ready") # delegated to real EzPrinter if app initialized Ezpl
"""

from __future__ import annotations

# ///////////////////////////////////////////////////////////////
# IMPORTS
# ///////////////////////////////////////////////////////////////
# Standard library imports
import logging
from collections.abc import Generator
from contextlib import contextmanager
from typing import Any

# ///////////////////////////////////////////////////////////////
# CLASSES — PRINTER PROXIES
# ///////////////////////////////////////////////////////////////


class _LazyWizard:
    """
    Lazy proxy for RichWizard.

    Delegates any attribute access / method call to the real RichWizard
    when Ezpl is initialized. Returns a silent no-op callable otherwise.
    This covers the full RichWizard API without enumerating every method.
    """

    def _get_real(self) -> Any:
        from .ezpl import Ezpl

        if Ezpl.is_initialized() and Ezpl.is_lib_printer_hook_enabled():
            return Ezpl().get_printer().wizard
        return None

    def __getattr__(self, name: str) -> Any:
        real = self._get_real()
        if real is not None:
            return getattr(real, name)
        return lambda *_args, **_kwargs: None


class _LazyPrinter:
    """
    Lazy proxy for EzPrinter.

    All method calls are silently discarded when Ezpl is not initialized.
    Once the host application calls Ezpl(...), every subsequent call is
    transparently forwarded to the real EzPrinter instance.

    The proxy holds a _LazyWizard so that printer.wizard.xxx() calls also
    resolve correctly.

    Unlike `_LazyWizard`, this proxy declares its log methods explicitly
    rather than relying on `__getattr__` — any new EzPrinter log method must
    be added here by hand, or its arguments would be silently dropped in
    lib mode.
    """

    def __init__(self) -> None:
        self._lazy_wizard = _LazyWizard()

    # --- Internal ---

    def _get_real(self) -> Any:
        from .ezpl import Ezpl

        if Ezpl.is_initialized() and Ezpl.is_lib_printer_hook_enabled():
            return Ezpl().get_printer()
        return None

    # --- Properties ---

    @property
    def level(self) -> str:
        """Return the current logging level, or 'INFO' if Ezpl is not initialized."""
        real = self._get_real()
        return real.level if real is not None else "INFO"

    @property
    def indent_step(self) -> int:
        """Return the configured indentation step, or 3 if Ezpl is not initialized."""
        real = self._get_real()
        return real.indent_step if real is not None else 3

    @property
    def indent_symbol(self) -> str:
        """Return the configured indentation symbol, or '>' if Ezpl is not initialized."""
        real = self._get_real()
        return real.indent_symbol if real is not None else ">"

    @property
    def base_indent_symbol(self) -> str:
        """Return the base indentation symbol, or '~' if Ezpl is not initialized."""
        real = self._get_real()
        return real.base_indent_symbol if real is not None else "~"

    @property
    def wizard(self) -> _LazyWizard:
        """Return the RichWizard proxy (lazy delegation)."""
        return self._lazy_wizard

    # --- Core log methods ---

    def log(self, level: str, message: Any, *args: Any, **kwargs: Any) -> None:
        """Log a message at the given level (no-op if Ezpl not initialized)."""
        real = self._get_real()
        if real is not None:
            real.log(level, message, *args, **kwargs)

    def trace(self, message: Any, *args: Any, **kwargs: Any) -> None:
        """Log a trace message (no-op if Ezpl not initialized)."""
        real = self._get_real()
        if real is not None:
            real.trace(message, *args, **kwargs)

    def info(self, message: Any, *args: Any, **kwargs: Any) -> None:
        """Log an info message (no-op if Ezpl not initialized)."""
        real = self._get_real()
        if real is not None:
            real.info(message, *args, **kwargs)

    def debug(self, message: Any, *args: Any, **kwargs: Any) -> None:
        """Log a debug message (no-op if Ezpl not initialized)."""
        real = self._get_real()
        if real is not None:
            real.debug(message, *args, **kwargs)

    def success(self, message: Any, *args: Any, **kwargs: Any) -> None:
        """Log a success message (no-op if Ezpl not initialized)."""
        real = self._get_real()
        if real is not None:
            real.success(message, *args, **kwargs)

    def warning(self, message: Any, *args: Any, **kwargs: Any) -> None:
        """Log a warning message (no-op if Ezpl not initialized)."""
        real = self._get_real()
        if real is not None:
            real.warning(message, *args, **kwargs)

    def error(
        self, message: Any, *args: Any, exc_info: bool = False, **kwargs: Any
    ) -> None:
        """Log an error message (no-op if Ezpl not initialized)."""
        real = self._get_real()
        if real is not None:
            real.error(message, *args, exc_info=exc_info, **kwargs)

    def critical(
        self, message: Any, *args: Any, exc_info: bool = False, **kwargs: Any
    ) -> None:
        """Log a critical message (no-op if Ezpl not initialized)."""
        real = self._get_real()
        if real is not None:
            real.critical(message, *args, exc_info=exc_info, **kwargs)

    def exception(self, message: Any, *args: Any, **kwargs: Any) -> None:
        """Log an exception with traceback (no-op if Ezpl not initialized)."""
        real = self._get_real()
        if real is not None:
            real.exception(message, *args, **kwargs)

    # --- Pattern methods ---

    def tip(self, message: Any) -> None:
        """Display a tip message (no-op if Ezpl not initialized)."""
        real = self._get_real()
        if real is not None:
            real.tip(message)

    def system(self, message: Any) -> None:
        """Display a system message (no-op if Ezpl not initialized)."""
        real = self._get_real()
        if real is not None:
            real.system(message)

    def install(self, message: Any) -> None:
        """Display an install message (no-op if Ezpl not initialized)."""
        real = self._get_real()
        if real is not None:
            real.install(message)

    def detect(self, message: Any) -> None:
        """Display a detect message (no-op if Ezpl not initialized)."""
        real = self._get_real()
        if real is not None:
            real.detect(message)

    def config(self, message: Any) -> None:
        """Display a config message (no-op if Ezpl not initialized)."""
        real = self._get_real()
        if real is not None:
            real.config(message)

    def deps(self, message: Any) -> None:
        """Display a deps message (no-op if Ezpl not initialized)."""
        real = self._get_real()
        if real is not None:
            real.deps(message)

    def print_pattern(self, pattern: Any, message: Any, level: str = "INFO") -> None:
        """Display a message with pattern format (no-op if Ezpl not initialized)."""
        real = self._get_real()
        if real is not None:
            real.print_pattern(pattern, message, level)

    # --- Rich features ---

    def print_table(self, data: list[dict[str, Any]], title: str | None = None) -> None:
        """Display a table (no-op if Ezpl not initialized)."""
        real = self._get_real()
        if real is not None:
            real.print_table(data, title=title)

    def print_panel(
        self, content: str, title: str | None = None, style: str = "blue"
    ) -> None:
        """Display a panel (no-op if Ezpl not initialized)."""
        real = self._get_real()
        if real is not None:
            real.print_panel(content, title=title, style=style)

    def print_json(
        self,
        data: str | dict | list,
        title: str | None = None,
        indent: int | None = None,
        highlight: bool = True,
    ) -> None:
        """Display JSON data (no-op if Ezpl not initialized)."""
        real = self._get_real()
        if real is not None:
            real.print_json(data, title=title, indent=indent, highlight=highlight)

    # --- Indentation ---

    def get_indent(self) -> str:
        """Return the current indentation string, or '~' if Ezpl not initialized."""
        real = self._get_real()
        return real.get_indent() if real is not None else "~"

    def add_indent(self) -> None:
        """Increase indentation level (no-op if Ezpl not initialized)."""
        real = self._get_real()
        if real is not None:
            real.add_indent()

    def del_indent(self) -> None:
        """Decrease indentation level (no-op if Ezpl not initialized)."""
        real = self._get_real()
        if real is not None:
            real.del_indent()

    def reset_indent(self) -> None:
        """Reset indentation to zero (no-op if Ezpl not initialized)."""
        real = self._get_real()
        if real is not None:
            real.reset_indent()

    @contextmanager
    def manage_indent(self) -> Generator[None]:
        """Context manager for temporary indentation (pass-through if Ezpl not initialized)."""
        real = self._get_real()
        if real is not None:
            with real.manage_indent():
                yield
        else:
            yield

    # --- Misc ---

    def set_level(self, level: str) -> None:
        """Set the logging level (no-op if Ezpl not initialized)."""
        real = self._get_real()
        if real is not None:
            real.set_level(level)

    def mark_level_as_configured(self) -> None:
        """Mark the level as configured (no-op if Ezpl not initialized)."""
        real = self._get_real()
        if real is not None:
            real.mark_level_as_configured()

    def __str__(self) -> str:
        real = self._get_real()
        return str(real) if real is not None else "LazyPrinter(uninitialized)"

    def __repr__(self) -> str:
        real = self._get_real()
        return repr(real) if real is not None else "LazyPrinter(uninitialized)"


# ///////////////////////////////////////////////////////////////
# MODULE-LEVEL SINGLETONS
# ///////////////////////////////////////////////////////////////

# Single shared LazyPrinter instance — stateless proxy, safe to share
_PRINTER: _LazyPrinter = _LazyPrinter()

# ///////////////////////////////////////////////////////////////
# FUNCTIONS
# ///////////////////////////////////////////////////////////////


def get_logger(name: str) -> logging.Logger:
    """
    Return a stdlib-compatible logger for use in library code.

    The returned logger has a NullHandler attached so that no output is
    produced when the host application has not configured any handler.
    When the host application enables logger hooks in Ezpl, all
    records emitted by this logger are automatically forwarded to the
    Rich/loguru pipeline.

    This follows the official Python recommendation for library logging:
    https://docs.python.org/3/howto/logging.html#configuring-logging-for-a-library

    Args:
        name: Logger name. Use __name__ to follow the module-name convention,
            which allows the host application to filter by package prefix.

    Returns:
        logging.Logger: A stdlib logger, passive by design.

    Example:
        >>> from ezpl.lib_mode import get_logger
        >>> log = get_logger(__name__)
        >>> log.info("Service initialized")    # silent without host config
        >>> log.warning("Unexpected state")    # forwarded if intercepted
    """
    log = logging.getLogger(name)
    # Attach NullHandler only once — avoids duplicate handlers on re-import
    if not log.handlers:
        log.addHandler(logging.NullHandler())
    return log


def get_printer() -> _LazyPrinter:
    """
    Return the shared lazy printer proxy for use in library code.

    The returned proxy silently discards all method calls when the host
    application has not initialized Ezpl. Once the app calls Ezpl(...),
    every subsequent call is transparently forwarded to the real EzPrinter.

    The same instance is returned on every call (module-level singleton).
    The proxy is stateless — it holds no indentation or level state of its
    own, delegating everything to the real EzPrinter when available.

    No configuration is triggered by calling this function — it is safe
    to call at module level in library code.

    Returns:
        _LazyPrinter: A lazy proxy implementing the full EzPrinter interface.

    Example:
        >>> from ezpl.lib_mode import get_printer
        >>> printer = get_printer()
        >>> printer.success("Service ready")   # silent without host config
        >>> printer.info("Processing...")      # delegated once app initializes Ezpl
        >>> with printer.manage_indent():
        ...     printer.debug("detail")
    """
    return _PRINTER


# ///////////////////////////////////////////////////////////////
# PUBLIC API
# ///////////////////////////////////////////////////////////////

__all__ = [
    "get_logger",
    "get_printer",
]
