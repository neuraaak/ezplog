# ///////////////////////////////////////////////////////////////
# EZPL - Main logging singleton
# Project: ezpl
# ///////////////////////////////////////////////////////////////

from __future__ import annotations

# ///////////////////////////////////////////////////////////////
# IMPORTS
# ///////////////////////////////////////////////////////////////
# Standard library imports
import sys
import threading
import warnings
from collections.abc import Generator
from contextlib import contextmanager
from pathlib import Path
from typing import Any
from uuid import uuid4

# Third-party imports
from loguru import logger

# Local imports
from .app_mode import InterceptHandler
from .config import ConfigurationManager
from .core.exceptions import EzplError, InitializationError
from .handlers import EzLogger, EzPrinter

# ///////////////////////////////////////////////////////////////
# GLOBALS
# ///////////////////////////////////////////////////////////////

_APP_PATH = Path(sys.argv[0]).parent

# ///////////////////////////////////////////////////////////////
# CLASSES
# ///////////////////////////////////////////////////////////////


class Ezpl:
    """
    Main logging singleton for the Ezpl framework.

    Ezpl provides a unified, thread-safe interface for console and file logging
    with advanced features including indentation management, pattern-based logging,
    and dynamic progress bars. It implements the Singleton pattern to ensure only
    one instance exists throughout the application lifecycle.

    Attributes:
        _instance: The singleton instance of Ezpl
        _lock: Thread lock for synchronized access
        _config_locked: Whether configuration can be modified
        _log_file: Path to the log file
        _printer: Console output handler
        _logger: File logging handler
        _config_manager: Configuration manager instance

    Note:
        Once initialized, Ezpl cannot be re-configured unless reset.
        Access it via the singleton pattern or module-level functions.

    Example:
        >>> log = Ezpl()
        >>> log.printer.log("INFO", "Application started")
        >>> log.logger.log("INFO", "Starting logging to file")
    """

    _instance: Ezpl | None = None
    _lock: threading.RLock = threading.RLock()
    _config_locked: bool = False
    _config_lock_token: str | None = None
    _log_file: Path
    _printer: EzPrinter
    _logger: EzLogger
    _config_manager: ConfigurationManager
    _lib_printer_hook_enabled: bool = True
    _stdlib_hook_targets: set[str | None] = set()

    # ///////////////////////////////////////////////////////////////
    # INIT
    # ///////////////////////////////////////////////////////////////

    @classmethod
    def is_initialized(cls) -> bool:
        """
        Return True if the Ezpl singleton has already been created.

        Useful for libraries that want to know whether they are the first
        to initialize Ezpl or if they should avoid re-configuring it.
        """
        return cls._instance is not None

    def __new__(
        cls,
        log_file: Path | str | None = None,
        log_level: str | None = None,
        printer_level: str | None = None,
        file_logger_level: str | None = None,
        log_rotation: str | None = None,
        log_retention: str | None = None,
        log_compression: str | None = None,
        log_backtrace: bool | None = None,
        log_diagnose: bool | None = None,
        indent_step: int | None = None,
        indent_symbol: str | None = None,
        base_indent_symbol: str | None = None,
        *,
        lock_config: bool = False,
        hook_logger: bool = True,
        hook_printer: bool = True,
        logger_names: list[str] | None = None,
    ) -> Ezpl:
        """
        Creates and returns a new instance of Ezpl if none exists.

        **Notes:**
        Ensures only one instance of Ezpl exists (Singleton pattern).

        **Priority order for configuration (for each parameter):**
        1. Arguments passed directly (highest priority)
        2. Environment variables (EZPL_*)
        3. Configuration file (~/.ezpl/config.json)
        4. Default values (lowest priority)

        **Args:**

            * `log_file` (Path | str, optional): Path to the log file
            * `log_level` (str, optional): Global log level (applies to both printer and logger)
            * `printer_level` (str, optional): Printer log level
            * `file_logger_level` (str, optional): File logger level
            * `log_rotation` (str, optional): Rotation setting (e.g., "10 MB", "1 day")
            * `log_retention` (str, optional): Retention period (e.g., "7 days")
            * `log_compression` (str, optional): Compression format (e.g., "zip", "gz")
            * `log_backtrace` (bool, optional): Extend tracebacks beyond the catching point
            * `log_diagnose` (bool, optional): Include local variable values in tracebacks
            * `indent_step` (int, optional): Indentation step size
            * `indent_symbol` (str, optional): Symbol for indentation
            * `base_indent_symbol` (str, optional): Base indentation symbol
            * `lock_config` (bool): If True, lock configuration immediately after init.
                Subsequent configure() calls will be blocked unless a valid token is used.
                The lock token is stored in Ezpl._config_lock_token.
            * `hook_logger` (bool): If True, install stdlib logging bridge(s) so
                classic loggers are forwarded to the loguru pipeline.
            * `hook_printer` (bool): If True, allow ezpl.lib_mode.get_printer()
                to delegate to the real EzPrinter instance once initialized.
            * `logger_names` (list[str] | None): Optional stdlib logger names to
                bridge explicitly. When omitted, the root logger is used.

        **Returns:**

            * `Ezpl`: The singleton instance of the Ezpl class.

        **Raises:**

            * `None`.
        """

        # //////
        # Double-checked locking pattern for thread-safe singleton
        if cls._instance is None:
            with cls._lock:
                # Check again after acquiring lock (double-checked locking)
                if cls._instance is None:
                    # Initialize configuration manager
                    cls._config_manager = ConfigurationManager()

                    # Determine configuration values with priority: arg > env > config file > default
                    # Helper function to get value with priority order
                    def get_config_value(
                        arg_value, config_key: str, getter_method
                    ) -> Any:
                        """
                        Get configuration value with priority: arg > env > config file > default

                        Args:
                            arg_value: Value from argument (can be None)
                            config_key: Configuration key name
                            getter_method: Method to get default value from config manager

                        Returns:
                            Final configuration value
                        """
                        # Priority 1: Argument direct
                        if arg_value is not None:
                            return arg_value

                        # Priority 2: Environment variable (already loaded in config_manager)
                        # Priority 3: Config file (already loaded in config_manager)
                        # Priority 4: Default (via getter method)
                        # The config_manager already has the correct priority (env > file > default)
                        config_value = cls._config_manager.get(config_key)
                        if config_value is not None:
                            return config_value

                        # Fallback to default via getter
                        return getter_method()

                    # Log file
                    if log_file:
                        cls._log_file = Path(log_file)
                    else:
                        cls._log_file = cls._config_manager.get_log_file()

                    # Log level (global)
                    final_log_level = get_config_value(
                        log_level, "log-level", cls._config_manager.get_log_level
                    )

                    # Printer level
                    final_printer_level = get_config_value(
                        printer_level,
                        "printer-level",
                        cls._config_manager.get_printer_level,
                    )

                    # File logger level
                    final_file_logger_level = get_config_value(
                        file_logger_level,
                        "file-logger-level",
                        cls._config_manager.get_file_logger_level,
                    )

                    # Rotation settings (can be None)
                    # Priority: arg > env > config file > default
                    # Note: If arg is None (default), we check env/config/default
                    # If user wants to explicitly set None, they can pass None or use configure()
                    final_rotation = (
                        log_rotation
                        if log_rotation is not None
                        else cls._config_manager.get_log_rotation()
                    )
                    final_retention = (
                        log_retention
                        if log_retention is not None
                        else cls._config_manager.get_log_retention()
                    )
                    final_compression = (
                        log_compression
                        if log_compression is not None
                        else cls._config_manager.get_log_compression()
                    )
                    final_backtrace = (
                        log_backtrace
                        if log_backtrace is not None
                        else cls._config_manager.get_log_backtrace()
                    )
                    final_diagnose = (
                        log_diagnose
                        if log_diagnose is not None
                        else cls._config_manager.get_log_diagnose()
                    )

                    # Indent settings
                    final_indent_step = get_config_value(
                        indent_step, "indent-step", cls._config_manager.get_indent_step
                    )
                    final_indent_symbol = get_config_value(
                        indent_symbol,
                        "indent-symbol",
                        cls._config_manager.get_indent_symbol,
                    )
                    final_base_indent_symbol = get_config_value(
                        base_indent_symbol,
                        "base-indent-symbol",
                        cls._config_manager.get_base_indent_symbol,
                    )

                    instance = object.__new__(cls)
                    cls._instance = instance

                    # Initialize printer with resolved configuration
                    cls._printer = EzPrinter(
                        level=final_printer_level,
                        indent_step=final_indent_step,
                        indent_symbol=final_indent_symbol,
                        base_indent_symbol=final_base_indent_symbol,
                    )

                    # Initialize logger with resolved configuration
                    cls._logger = EzLogger(
                        log_file=cls._log_file,
                        level=final_file_logger_level,
                        rotation=final_rotation,
                        retention=final_retention,
                        compression=final_compression,
                        backtrace=final_backtrace,
                        diagnose=final_diagnose,
                    )

                    # Apply global log level with priority: specific > global
                    cls._instance._apply_level_priority(
                        printer_level=printer_level,
                        file_logger_level=file_logger_level,
                        global_level=final_log_level,
                    )

                    # Apply post-init options — inside the critical section,
                    # first construction only (double-checked locking guarantees this)
                    if lock_config:
                        cls._config_lock_token = cls.lock_config()

                    cls._set_compatibility_hooks(
                        hook_logger=hook_logger,
                        hook_printer=hook_printer,
                        logger_names=logger_names,
                    )

        # Type narrowing: _instance is guaranteed to be set at this point
        if cls._instance is None:
            raise InitializationError("Singleton initialization failed unexpectedly")
        return cls._instance

    # ///////////////////////////////////////////////////////////////
    # PRIVATE HELPERS
    # ///////////////////////////////////////////////////////////////

    def _apply_level_priority(
        self,
        *,
        printer_level: str | None = None,
        file_logger_level: str | None = None,
        global_level: str | None = None,
    ) -> None:
        """
        Apply log levels with priority: specific level > global level.

        Only sets levels when a non-None value can be resolved.
        If a specific level is not provided, global_level is used as fallback.
        """
        effective_printer = printer_level if printer_level is not None else global_level
        effective_logger = (
            file_logger_level if file_logger_level is not None else global_level
        )

        if effective_printer:
            self.set_printer_level(effective_printer)

        if effective_logger:
            self.set_logger_level(effective_logger)

    def _rebuild_logger(
        self,
        *,
        level: str | None = None,
    ) -> None:
        """
        Close the current file logger and reinitialize it with current configuration.

        Args:
            level: Override the log level. If None, preserves the current level.
        """
        current_level = (
            level
            or (
                self._logger.level
                if hasattr(self, "_logger") and self._logger
                else None
            )
            or self._config_manager.get_file_logger_level()
        )
        try:
            if hasattr(self, "_logger") and self._logger:
                self._logger.close()
        except (EzplError, OSError, RuntimeError) as e:
            logger.error(f"Error while closing logger: {e}")
        self._logger = EzLogger(
            log_file=self._log_file,
            level=current_level,
            rotation=self._config_manager.get_log_rotation(),
            retention=self._config_manager.get_log_retention(),
            compression=self._config_manager.get_log_compression(),
            backtrace=self._config_manager.get_log_backtrace(),
            diagnose=self._config_manager.get_log_diagnose(),
        )

    def _rebuild_printer(
        self,
        *,
        level: str | None = None,
    ) -> None:
        """
        Reinitialize the console printer with current configuration.

        Args:
            level: Override the log level. If None, preserves the current level.
        """
        current_level = (
            level
            or (
                self._printer.level
                if hasattr(self, "_printer") and self._printer
                else None
            )
            or self._config_manager.get_printer_level()
        )
        self._printer = EzPrinter(
            level=current_level,
            indent_step=self._config_manager.get_indent_step(),
            indent_symbol=self._config_manager.get_indent_symbol(),
            base_indent_symbol=self._config_manager.get_base_indent_symbol(),
        )

    # ///////////////////////////////////////////////////////////////
    # GETTER
    # ///////////////////////////////////////////////////////////////

    def get_printer(self) -> EzPrinter:
        """
        Returns the EzPrinter instance.

        **Returns:**

            * EzPrinter: The console printer instance providing info(), debug(), success(), etc.
                Implements PrinterProtocol for type safety.
        """
        return self._printer

    # ///////////////////////////////////////////////////////////////

    def get_logger(self) -> EzLogger:
        """
        Returns the EzLogger instance.

        **Returns:**

            * EzLogger: The file logger instance for file logging.
                Use logger.info(), logger.debug(), etc. directly.
                For advanced loguru features, use logger.get_loguru()
                Implements LoggerProtocol for type safety.
        """
        return self._logger

    # ///////////////////////////////////////////////////////////////
    # UTILS METHODS
    # ///////////////////////////////////////////////////////////////

    @property
    def printer_level(self) -> str:
        """Return the current printer logging level."""
        return self._printer.level

    @property
    def logger_level(self) -> str:
        """Return the current file logger logging level."""
        return self._logger.level

    def set_level(self, level: str) -> None:
        """
        Set the log level for both the printer and the logger simultaneously.

        **Args:**

            * `level` (str): The desired log level (e.g., "INFO", "WARNING").

        **Returns:**

            * `None`.
        """
        if not self._can_write_config():
            warnings.warn(
                "Ezpl configuration is locked. Call Ezpl.unlock_config(token) to unlock.",
                UserWarning,
                stacklevel=2,
            )
            return
        self.set_logger_level(level)
        self.set_printer_level(level)

    def set_printer_level(self, level: str) -> None:
        """
        Set the log level for the printer only.

        **Args:**

            * `level` (str): The desired log level for the printer.

        **Returns:**

            * `None`.
        """
        if not self._can_write_config():
            warnings.warn(
                "Ezpl configuration is locked. Call Ezpl.unlock_config(token) to unlock.",
                UserWarning,
                stacklevel=2,
            )
            return
        self._printer.set_level(level)

    def set_logger_level(self, level: str) -> None:
        """
        Set the log level for the file logger only.

        **Args:**

            * `level` (str): The desired log level for the file logger.

        **Returns:**

            * `None`.
        """
        if not self._can_write_config():
            warnings.warn(
                "Ezpl configuration is locked. Call Ezpl.unlock_config(token) to unlock.",
                UserWarning,
                stacklevel=2,
            )
            return
        self._logger.set_level(level)

    # ///////////////////////////////////////////////////////////////
    # FACADE METHODS
    # ///////////////////////////////////////////////////////////////

    def trace(self, message: Any, *args: Any, **kwargs: Any) -> None:
        """Log a trace message to the console printer."""
        self._printer.trace(message, *args, **kwargs)

    def debug(self, message: Any, *args: Any, **kwargs: Any) -> None:
        """Log a debug message to the console printer."""
        self._printer.debug(message, *args, **kwargs)

    def info(self, message: Any, *args: Any, **kwargs: Any) -> None:
        """Log an info message to the console printer."""
        self._printer.info(message, *args, **kwargs)

    def success(self, message: Any, *args: Any, **kwargs: Any) -> None:
        """Log a success message to the console printer."""
        self._printer.success(message, *args, **kwargs)

    def warning(self, message: Any, *args: Any, **kwargs: Any) -> None:
        """Log a warning message to the console printer."""
        self._printer.warning(message, *args, **kwargs)

    def error(
        self, message: Any, *args: Any, exc_info: bool = False, **kwargs: Any
    ) -> None:
        """Log an error message to the console printer.

        Args:
            message: Message to display.
            *args: Positional arguments for `{}` formatting.
            exc_info: If True, also render the active exception traceback.
            **kwargs: Keyword arguments for `{}` formatting.
        """
        self._printer.error(message, *args, exc_info=exc_info, **kwargs)

    def critical(
        self, message: Any, *args: Any, exc_info: bool = False, **kwargs: Any
    ) -> None:
        """Log a critical message to the console printer.

        Args:
            message: Message to display.
            *args: Positional arguments for `{}` formatting.
            exc_info: If True, also render the active exception traceback.
            **kwargs: Keyword arguments for `{}` formatting.
        """
        self._printer.critical(message, *args, exc_info=exc_info, **kwargs)

    def exception(self, message: Any, *args: Any, **kwargs: Any) -> None:
        """Log an error message with the active exception traceback (console)."""
        self._printer.exception(message, *args, **kwargs)

    def log(self, level: str, message: Any, *args: Any, **kwargs: Any) -> None:
        """Log a message at the given level to the console printer.

        Args:
            level: Log level name (TRACE, DEBUG, INFO, SUCCESS, WARNING,
                ERROR, CRITICAL).
            message: Message to display.
            *args: Positional arguments for `{}` formatting.
            **kwargs: Keyword arguments for `{}` formatting.
        """
        self._printer.log(level, message, *args, **kwargs)

    # ///////////////////////////////////////////////////////////////

    def add_separator(self) -> None:
        """
        Adds a separator to the log file.

        **Returns:**

            * `None`.
        """
        self._logger.add_separator()

    # ///////////////////////////////////////////////////////////////

    @contextmanager
    def manage_indent(self) -> Generator[None]:
        """
        Context manager to manage indentation level.

        **Returns:**

            * `None`.
        """
        with self._printer.manage_indent():
            yield

    # ///////////////////////////////////////////////////////////////
    # ENHANCED METHODS
    # ///////////////////////////////////////////////////////////////

    @classmethod
    def reset(cls) -> None:
        """
        Reset the singleton instance (useful for testing).

        Warning: This will destroy the current instance and all its state.
        """
        if cls._instance is not None:
            # Close logger handlers to release file handles (important on Windows)
            try:
                if hasattr(cls._instance, "_logger") and cls._instance._logger:
                    cls._instance._logger.close()
            except (EzplError, OSError, RuntimeError) as e:
                logger.error(f"Error during cleanup: {e}")
            cls._instance = None
        cls._remove_all_intercept_handlers()
        cls._lib_printer_hook_enabled = True
        # Also reset configuration lock
        cls._config_locked = False
        cls._config_lock_token = None

    def set_compatibility_hooks(
        self,
        *,
        hook_logger: bool = True,
        hook_printer: bool = True,
        logger_names: list[str] | None = None,
    ) -> None:
        """
        Configure compatibility hooks between Ezpl and classic logging/lib_mode.

        Args:
            hook_logger: If True, bridge stdlib logging records to Ezpl.
                If False, remove previously installed stdlib bridges.
            hook_printer: If True, ezpl.lib_mode.get_printer() delegates to
                Ezpl's real printer once initialized. If False, it stays silent.
            logger_names: Optional stdlib logger names to hook explicitly.
                When omitted, root logger is targeted.

        Notes:
            - This method is safe to call multiple times (idempotent behavior).
            - Hooking named loggers is useful for libraries with propagate=False.
        """
        type(self)._set_compatibility_hooks(
            hook_logger=hook_logger,
            hook_printer=hook_printer,
            logger_names=logger_names,
        )

    # ------------------------------------------------
    # CONFIG LOCK CONTROL
    # ------------------------------------------------

    @classmethod
    def lock_config(cls) -> str:
        """
        Lock Ezpl configuration so that future configure() and set_level() calls
        are blocked until unlock_config(token) is called.

        Intended usage:
            1. Root application configures Ezpl once
            2. Calls token = Ezpl.lock_config()
            3. Stores the token; libraries cannot reconfigure Ezpl without it

        Returns:
            str: A token required to unlock the configuration later.
        """
        with cls._lock:
            if not cls._config_locked:
                cls._config_locked = True
                cls._config_lock_token = uuid4().hex
            token = cls._config_lock_token
            if token is None:
                # Should never happen: token is set whenever _config_locked is True
                raise RuntimeError(
                    "Configuration lock token is None despite lock being active"
                )
            return token

    @classmethod
    def unlock_config(cls, token: str) -> bool:
        """
        Unlock Ezpl configuration.

        Args:
            token: The token returned by lock_config(). Must match exactly.

        Returns:
            True if unlocked successfully, False if the token is wrong.
        """
        with cls._lock:
            if not cls._config_locked:
                return True

            if token != cls._config_lock_token:
                warnings.warn(
                    "Unlock denied: invalid token.",
                    UserWarning,
                    stacklevel=2,
                )
                return False

            cls._config_locked = False
            cls._config_lock_token = None
            return True

    @classmethod
    def is_locked(cls) -> bool:
        """Return True if the configuration is currently locked."""
        return cls._config_locked

    @classmethod
    def is_lib_printer_hook_enabled(cls) -> bool:
        """Return True when lib_mode printer proxy is allowed to delegate."""
        return cls._lib_printer_hook_enabled

    @classmethod
    def _can_write_config(cls) -> bool:
        """Return True when configuration writes are allowed."""
        return not cls._config_locked

    @classmethod
    def _set_compatibility_hooks(
        cls,
        *,
        hook_logger: bool,
        hook_printer: bool,
        logger_names: list[str] | None = None,
    ) -> None:
        """Apply logger/printer compatibility hooks with idempotent semantics."""
        cls._lib_printer_hook_enabled = hook_printer

        targets: list[str | None] = (
            [None] if logger_names is None else list(dict.fromkeys(logger_names))
        )

        if hook_logger:
            for logger_name in targets:
                cls._install_intercept_handler(logger_name)
            return

        if logger_names is None:
            cls._remove_all_intercept_handlers()
            return

        for logger_name in targets:
            cls._remove_intercept_handler(logger_name)

    @classmethod
    def _install_intercept_handler(cls, logger_name: str | None = None) -> None:
        """
        Install InterceptHandler on a stdlib logger.

        Args:
            logger_name: Name of the stdlib logger to hook. When None,
                install on the root logger.

        Notes:
            This method is idempotent: calling it multiple times installs the
            handler only once for a given target logger.
        """
        import logging as _logging

        target = (
            _logging.getLogger()
            if logger_name is None
            else _logging.getLogger(logger_name)
        )
        if not any(isinstance(h, InterceptHandler) for h in target.handlers):
            target.addHandler(InterceptHandler())
        target.setLevel(0)

        # Ensure named loggers can still bubble to parent handlers if needed.
        if logger_name is not None:
            target.propagate = True

        cls._stdlib_hook_targets.add(logger_name)

    @classmethod
    def _remove_intercept_handler(cls, logger_name: str | None = None) -> None:
        """Remove InterceptHandler instances from a stdlib logger."""
        import logging as _logging

        target = (
            _logging.getLogger()
            if logger_name is None
            else _logging.getLogger(logger_name)
        )
        target.handlers = [
            handler
            for handler in target.handlers
            if not isinstance(handler, InterceptHandler)
        ]
        cls._stdlib_hook_targets.discard(logger_name)

    @classmethod
    def _remove_all_intercept_handlers(cls) -> None:
        """Remove InterceptHandler from all tracked stdlib logger targets."""
        tracked_targets = list(cls._stdlib_hook_targets)
        if None not in tracked_targets:
            tracked_targets.append(None)

        for logger_name in tracked_targets:
            cls._remove_intercept_handler(logger_name)

        cls._stdlib_hook_targets.clear()

    def set_log_file(self, log_file: Path | str) -> None:
        """
        Change the log file (requires reinitialization of the logger).

        Args:
            log_file: New path to the log file

        Note: This will reinitialize the file logger but keep the singleton instance.
        """
        new_log_file = Path(log_file)
        if new_log_file != self._log_file:
            self._log_file = new_log_file
            # Update configuration
            self._config_manager.set("log-file", str(new_log_file))
            self._rebuild_logger()

    def get_log_file(self) -> Path:
        """
        Get the current log file path.

        Returns:
            Path to the current log file
        """
        return self._log_file

    def get_config(self) -> ConfigurationManager:
        """
        Get the current configuration manager.

        Returns:
            ConfigurationManager instance for accessing and modifying configuration
        """
        return self._config_manager

    # ///////////////////////////////////////////////////////////////
    # HANDLER OVERRIDE METHODS
    # ///////////////////////////////////////////////////////////////

    def set_printer_class(
        self,
        printer_class: type[EzPrinter] | EzPrinter,
        **init_kwargs: Any,
    ) -> None:
        """
        Replace the current printer with a custom printer class or instance.

        Allows users to override the default printer with a custom class that
        inherits from EzPrinter. The method preserves
        current configuration values (level, indentation settings) unless
        explicitly overridden in init_kwargs.

        Args:
            printer_class: Custom printer class inheriting from EzPrinter,
                or an already instantiated EzPrinter instance
            **init_kwargs: Optional initialization parameters for the printer
                class. If not provided, current configuration values are used.

        Raises:
            TypeError: If printer_class is not a valid class or instance
            ValidationError: If initialization parameters are invalid

        Example:
            >>> from ezpl import Ezpl, EzPrinter
            >>>
            >>> class CustomPrinter(EzPrinter):
            ...     def info(self, message):
            ...         super().info(f"[CUSTOM] {message}")
            >>>
            >>> ezpl = Ezpl()
            >>> ezpl.set_printer_class(CustomPrinter, level="DEBUG")
            >>> ezpl.get_printer().info("Test")
            [CUSTOM] Test
        """
        from .core.exceptions import ValidationError

        # If it's already an instance, use it directly
        if isinstance(printer_class, EzPrinter):
            new_printer = printer_class
        # If it's a class, instantiate it
        elif isinstance(printer_class, type):
            # Validate that it's a subclass of EzPrinter
            if not issubclass(printer_class, EzPrinter):
                raise TypeError(
                    f"printer_class must be a subclass of {EzPrinter.__name__}, "
                    f"got {printer_class.__name__}"
                )

            # Preserve current configuration values if not provided
            current_level = (
                self._printer.level
                if hasattr(self, "_printer") and self._printer
                else self._config_manager.get_printer_level()
            )
            current_indent_step = (
                self._printer.indent_step
                if hasattr(self, "_printer") and self._printer
                else self._config_manager.get_indent_step()
            )
            current_indent_symbol = (
                self._printer.indent_symbol
                if hasattr(self, "_printer") and self._printer
                else self._config_manager.get_indent_symbol()
            )
            current_base_indent_symbol = (
                self._printer.base_indent_symbol
                if hasattr(self, "_printer") and self._printer
                else self._config_manager.get_base_indent_symbol()
            )

            # Merge kwargs with default values
            init_params = {
                "level": init_kwargs.pop("level", current_level),
                "indent_step": init_kwargs.pop("indent_step", current_indent_step),
                "indent_symbol": init_kwargs.pop(
                    "indent_symbol", current_indent_symbol
                ),
                "base_indent_symbol": init_kwargs.pop(
                    "base_indent_symbol", current_base_indent_symbol
                ),
            }
            init_params.update(init_kwargs)

            # Create new instance
            try:
                new_printer = printer_class(**init_params)
            except Exception as e:
                raise ValidationError(
                    f"Failed to initialize printer class {printer_class.__name__}: {e}",
                    "printer_class",
                    str(printer_class),
                ) from e
        else:
            raise TypeError(
                f"printer_class must be a class or an instance of {EzPrinter.__name__}, "
                f"got {type(printer_class).__name__}"
            )

        # Replace the instance
        self._printer = new_printer

    def set_logger_class(
        self,
        logger_class: type[EzLogger] | EzLogger,
        **init_kwargs: Any,
    ) -> None:
        """
        Replace the current logger with a custom logger class or instance.

        Allows users to override the default logger with a custom class that
        inherits from EzLogger. The method preserves current
        configuration values (level, rotation, retention, compression) unless
        explicitly overridden in init_kwargs.

        Args:
            logger_class: Custom logger class inheriting from EzLogger,
                or an already instantiated EzLogger instance
            **init_kwargs: Optional initialization parameters for the logger
                class. If not provided, current configuration values are used.

        Raises:
            TypeError: If logger_class is not a valid class or instance
            ValidationError: If initialization parameters are invalid
            FileOperationError: If file operations fail during logger creation
                (may be raised by the logger class constructor)

        Example:
            >>> from ezpl import Ezpl, EzLogger
            >>>
            >>> class CustomLogger(EzLogger):
            ...     def info(self, message):
            ...         super().info(f"[CUSTOM LOG] {message}")
            >>>
            >>> ezpl = Ezpl()
            >>> ezpl.set_logger_class(CustomLogger, log_file="custom.log")
            >>> ezpl.get_logger().info("Test")
        """
        from .core.exceptions import ValidationError

        # If it's already an instance, use it directly
        if isinstance(logger_class, EzLogger):
            new_logger = logger_class
        # If it's a class, instantiate it
        elif isinstance(logger_class, type):
            # Validate that it's a subclass of EzLogger
            if not issubclass(logger_class, EzLogger):
                raise TypeError(
                    f"logger_class must be a subclass of {EzLogger.__name__}, "
                    f"got {logger_class.__name__}"
                )

            # Preserve current configuration values if not provided
            current_level = (
                self._logger.level
                if hasattr(self, "_logger") and self._logger
                else self._config_manager.get_file_logger_level()
            )
            current_log_file = (
                self._log_file
                if hasattr(self, "_log_file")
                else self._config_manager.get_log_file()
            )
            current_rotation = (
                self._logger.rotation
                if hasattr(self, "_logger") and self._logger
                else self._config_manager.get_log_rotation()
            )
            current_retention = (
                self._logger.retention
                if hasattr(self, "_logger") and self._logger
                else self._config_manager.get_log_retention()
            )
            current_compression = (
                self._logger.compression
                if hasattr(self, "_logger") and self._logger
                else self._config_manager.get_log_compression()
            )
            current_backtrace = (
                self._logger.backtrace
                if hasattr(self, "_logger") and self._logger
                else self._config_manager.get_log_backtrace()
            )
            current_diagnose = (
                self._logger.diagnose
                if hasattr(self, "_logger") and self._logger
                else self._config_manager.get_log_diagnose()
            )

            # Merge kwargs with default values
            init_params = {
                "log_file": init_kwargs.pop("log_file", current_log_file),
                "level": init_kwargs.pop("level", current_level),
                "rotation": init_kwargs.pop("rotation", current_rotation),
                "retention": init_kwargs.pop("retention", current_retention),
                "compression": init_kwargs.pop("compression", current_compression),
                "backtrace": init_kwargs.pop("backtrace", current_backtrace),
                "diagnose": init_kwargs.pop("diagnose", current_diagnose),
            }
            init_params.update(init_kwargs)

            # Close previous logger before creating new one to avoid resource leaks
            try:
                if hasattr(self, "_logger") and self._logger:
                    self._logger.close()
            except (EzplError, OSError, RuntimeError) as e:
                logger.error(f"Error while closing previous logger: {e}")

            # Create new instance
            try:
                new_logger = logger_class(**init_params)
            except Exception as e:
                raise ValidationError(
                    f"Failed to initialize logger class {logger_class.__name__}: {e}",
                    "logger_class",
                    str(logger_class),
                ) from e
        else:
            raise TypeError(
                f"logger_class must be a class or an instance of {EzLogger.__name__}, "
                f"got {type(logger_class).__name__}"
            )

        # Replace the instance
        self._logger = new_logger

    # ///////////////////////////////////////////////////////////////
    # CONFIGURATION METHODS
    # ///////////////////////////////////////////////////////////////

    def reload_config(self) -> None:
        """
        Reload configuration from file and environment variables.

        This method reloads the configuration and reapplies it to handlers.
        Useful when environment variables or the config file have changed
        after the singleton was initialized.

        Note: This will reinitialize handlers with the new configuration.
        """
        # Reload configuration
        self._config_manager.reload()

        # Get configuration values
        printer_level = self._config_manager.get_printer_level()
        file_logger_level = self._config_manager.get_file_logger_level()
        global_log_level = self._config_manager.get_log_level()

        # Check if specific levels are explicitly set (not just defaults)
        # Priority: specific levels > global level
        # Only apply global level if specific levels are not explicitly set
        printer_level_explicit = self._config_manager.has_key("printer-level")
        file_logger_level_explicit = self._config_manager.has_key("file-logger-level")
        global_log_level_explicit = self._config_manager.has_key("log-level")

        # Respect manually set levels: don't override if set via set_level()
        printer_manually_set = self._printer.level_manually_set
        logger_manually_set = self._logger.level_manually_set

        # Reapply to handlers with priority logic (skip if manually set)
        if not printer_manually_set:
            effective_printer = (
                printer_level
                if printer_level_explicit
                else global_log_level
                if global_log_level_explicit
                else printer_level
            )
            self.set_printer_level(effective_printer)

        if not logger_manually_set:
            effective_logger = (
                file_logger_level
                if file_logger_level_explicit
                else (
                    global_log_level if global_log_level_explicit else file_logger_level
                )
            )
            self.set_logger_level(effective_logger)

        # Reinitialize handlers — new instances have _level_manually_set = False by default
        self._rebuild_logger()
        self._rebuild_printer()

    def configure(
        self,
        config_dict: dict[str, Any] | None = None,
        *,
        persist: bool = False,
        **kwargs: Any,
    ) -> bool:
        """
        Configure Ezpl dynamically.

        Args:
            config_dict: Dictionary of configuration values to update
            persist: If True, write changes to ~/.ezpl/config.json so they
                survive future runs. Defaults to False (in-memory only).
            **kwargs: Configuration options (alternative to config_dict):
                - log_file or log-file: Path to log file
                - printer_level or printer-level: Printer log level
                - file_logger_level or file-logger-level: File logger level
                - level or log-level: Set both printer and logger level
                - log_rotation or log-rotation: Rotation setting (e.g., "10 MB", "1 day")
                - log_retention or log-retention: Retention period (e.g., "7 days")
                - log_compression or log-compression: Compression format (e.g., "zip", "gz")
                - log_backtrace or log-backtrace: Extend tracebacks beyond the
                  catching point (default True)
                - log_diagnose or log-diagnose: Include local variable values in
                  tracebacks (default False — enabling this may leak secrets
                  into the log file)
                - indent_step or indent-step: Indentation step size
                - indent_symbol or indent-symbol: Symbol for indentation
                - base_indent_symbol or base-indent-symbol: Base indentation symbol

        Returns:
            True if configuration was applied, False if it was blocked by lock.
        """
        # Merge config_dict and kwargs
        if config_dict:
            kwargs.update(config_dict)

        # If configuration is locked, warn and return False
        if not self._can_write_config():
            warnings.warn(
                "Ezpl configuration is locked. Call Ezpl.unlock_config(token) "
                "to unlock before reconfiguring.",
                UserWarning,
                stacklevel=2,
            )
            return False

        # Normalize keys: convert underscores to hyphens for consistency
        normalized_config = {}
        key_mapping = {
            "log_file": "log-file",
            "printer_level": "printer-level",
            "file_logger_level": "file-logger-level",
            "level": "log-level",
            "log_rotation": "log-rotation",
            "log_retention": "log-retention",
            "log_compression": "log-compression",
            "log_backtrace": "log-backtrace",
            "log_diagnose": "log-diagnose",
            "indent_step": "indent-step",
            "indent_symbol": "indent-symbol",
            "base_indent_symbol": "base-indent-symbol",
        }

        for key, value in kwargs.items():
            # Use normalized key if mapping exists, otherwise keep original
            normalized_key = key_mapping.get(key, key)
            normalized_config[normalized_key] = value

        # Extract log-file before update — set_log_file() owns that write.
        # Keep it persisted in config when requested.
        new_log_file = normalized_config.pop("log-file", None)
        if new_log_file is not None:
            normalized_config["log-file"] = str(Path(new_log_file))

        # Update configuration manager
        self._config_manager.update(normalized_config)
        # Apply changes to handlers
        if new_log_file is not None:
            self.set_log_file(new_log_file)

        # Handle log level changes with priority: specific > global
        self._apply_level_priority(
            printer_level=normalized_config.get("printer-level"),
            file_logger_level=normalized_config.get("file-logger-level"),
            global_level=normalized_config.get("log-level"),
        )

        # Reinitialize logger if rotation settings changed
        rotation_changed = any(
            key in normalized_config
            for key in [
                "log-rotation",
                "log-retention",
                "log-compression",
                "log-backtrace",
                "log-diagnose",
            ]
        )
        if rotation_changed:
            self._rebuild_logger()

        # Reinitialize printer if indent settings changed
        indent_changed = any(
            key in normalized_config
            for key in ["indent-step", "indent-symbol", "base-indent-symbol"]
        )
        if indent_changed:
            self._rebuild_printer()

        if persist:
            self._config_manager.save()

        return True


# ///////////////////////////////////////////////////////////////
# PUBLIC API
# ///////////////////////////////////////////////////////////////

__all__ = [
    "Ezpl",
]
