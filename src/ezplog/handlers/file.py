# ///////////////////////////////////////////////////////////////
# EZPL - File Logger Handler
# Project: ezpl
# ///////////////////////////////////////////////////////////////

"""
File logger handler for Ezpl logging framework.

This module provides a file-based logging handler with advanced formatting,
session separation, and structured output.
"""

from __future__ import annotations

# ///////////////////////////////////////////////////////////////
# IMPORTS
# ///////////////////////////////////////////////////////////////
# Standard library imports
from contextlib import suppress
from datetime import datetime
from pathlib import Path
from typing import Any, cast

# Third-party imports
from loguru import logger
from loguru._logger import Logger as LoguruLogger

# Local imports
from ..core.exceptions import FileOperationError, LoggingError, ValidationError
from ..core.interfaces import LoggingHandler
from ..types.aliases import (
    SUPPORTED_COMPRESSIONS,
    CompressionSpec,
    RetentionSpec,
    RotationSpec,
)
from ..types.enums import LogLevel
from ..utils import safe_str_convert, sanitize_for_file

# ///////////////////////////////////////////////////////////////
# CLASSES
# ///////////////////////////////////////////////////////////////


class EzLogger(LoggingHandler):
    """
    File logger handler with advanced formatting and session management.

    This handler provides file-based logging with:
    - Structured log format
    - Session separators
    - HTML tag sanitization
    - Automatic file creation
    """

    # ///////////////////////////////////////////////////////////////
    # INIT
    # ///////////////////////////////////////////////////////////////

    def __init__(
        self,
        log_file: Path | str,
        level: str = "INFO",
        rotation: RotationSpec = None,
        retention: RetentionSpec = None,
        compression: CompressionSpec = None,
        *,
        backtrace: bool = True,
        diagnose: bool = False,
    ) -> None:
        """
        Initialize the file logger handler.

        Args:
            log_file: Path to the log file
            level: The desired logging level
            rotation: Rotation trigger — size string ("10 MB"), byte count,
                datetime.time, datetime.timedelta, or a predicate callable
            retention: Retention policy — duration string ("7 days"), number of
                files to keep (int), timedelta, or a cleanup callable
            compression: Compression format name (see SUPPORTED_COMPRESSIONS)
                or a callable applied to the rotated file path
            backtrace: If True, extend tracebacks beyond the catching point
            diagnose: If True, include local variable values in tracebacks.
                Defaults to False, unlike loguru: locals routinely hold
                secrets, and log files are archived and shipped elsewhere.

        Raises:
            ValidationError: If the provided level is invalid
            FileOperationError: If file operations fail
        """
        if not LogLevel.is_valid_level(level):
            raise ValidationError(f"Invalid log level: {level}", "level", level)

        if isinstance(compression, str) and compression not in SUPPORTED_COMPRESSIONS:
            raise ValidationError(
                f"Unsupported compression format: {compression!r}. "
                f"Expected one of: {', '.join(sorted(SUPPORTED_COMPRESSIONS))}",
                "compression",
                compression,
            )

        self._level = level.upper()
        self._level_manually_set = False
        self._log_file = Path(log_file)
        self._logger = logger.bind(task="logger")
        self._logger_id: int | None = None
        self._rotation: RotationSpec = rotation
        self._retention: RetentionSpec = retention
        self._compression: CompressionSpec = compression
        self._backtrace = backtrace
        self._diagnose = diagnose

        # Validate and create parent directory
        try:
            self._log_file.parent.mkdir(parents=True, exist_ok=True)
        except OSError as e:
            raise FileOperationError(
                f"Cannot create log directory: {e}",
                str(self._log_file.parent),
                "create_directory",
            ) from e

        # Validate that the file can be created/written
        try:
            if not self._log_file.exists():
                self._log_file.touch()
            # Write test
            with open(self._log_file, "a", encoding="utf-8") as f:
                f.write("")
        except OSError as e:
            raise FileOperationError(
                f"Cannot write to log file: {e}", str(self._log_file), "write"
            ) from e

        self._initialize_logger()

    # ------------------------------------------------
    # PRIVATE HELPER METHODS
    # ------------------------------------------------

    def _initialize_logger(self) -> None:
        """
        Initialize the file logger handler.

        Raises:
            LoggingError: If logger initialization fails
        """
        try:
            # Remove existing handler if any
            logger_id: int | None = self._logger_id
            if logger_id is not None:
                self._logger.remove(logger_id)
            else:
                # First initialization: drop loguru's default stderr sink so
                # intercepted stdlib records only go to the file, not the console.
                with suppress(ValueError):
                    logger.remove(0)

            # Call loguru.add() with keyword arguments directly
            # Note: loguru.add() accepts keyword arguments, not a dict
            self._logger_id = self._logger.add(
                sink=self._log_file,
                level=self._level,
                format=self._custom_formatter,
                filter=lambda record: record["extra"]["task"] == "logger",
                encoding="utf-8",
                rotation=self._rotation if self._rotation else None,
                retention=self._retention if self._retention else None,
                compression=self._compression if self._compression else None,
                backtrace=self._backtrace,
                diagnose=self._diagnose,
            )
        except Exception as e:
            raise LoggingError(f"Failed to initialize file logger: {e}", "file") from e

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
    def rotation(self) -> RotationSpec:
        """Return current rotation setting."""
        return self._rotation

    @property
    def retention(self) -> RetentionSpec:
        """Return current retention setting."""
        return self._retention

    @property
    def compression(self) -> CompressionSpec:
        """Return current compression setting."""
        return self._compression

    @property
    def backtrace(self) -> bool:
        """Return whether tracebacks extend beyond the catching point."""
        return self._backtrace

    @property
    def diagnose(self) -> bool:
        """Return whether local variable values appear in tracebacks."""
        return self._diagnose

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
            LoggingError: If level update fails
        """
        if not LogLevel.is_valid_level(level):
            raise ValidationError(f"Invalid log level: {level}", "level", level)

        old_level = self._level
        try:
            self._level = level.upper()
            self._level_manually_set = True
            self._initialize_logger()
        except Exception as e:
            self._level = old_level  # Rollback to previous level on failure
            raise LoggingError(f"Failed to update log level: {e}", "file") from e

    def log(self, level: str, message: Any) -> None:
        """
        Log a message with the specified level.

        Args:
            level: The log level
            message: The message to log (any type, will be converted to string)

        Raises:
            ValidationError: If the level is invalid
            LoggingError: If logging fails
        """
        if not LogLevel.is_valid_level(level):
            raise ValidationError(f"Invalid log level: {level}", "level", level)

        # Convert message to string robustly
        message = safe_str_convert(message)

        try:
            log_method = getattr(self._logger, level.lower())
            log_method(message)
        except Exception as e:
            raise LoggingError(f"Failed to log message: {e}", "file") from e

    # ///////////////////////////////////////////////////////////////
    # LOGGING METHODS (API primaire - delegates to loguru)
    # ///////////////////////////////////////////////////////////////

    # NOTE: every wrapper below uses `opt(depth=1)` so loguru attributes the
    # record to the actual caller (user code) rather than to this method.
    # Without it, every log line reports `file:info:<line>` etc.

    def trace(self, message: Any, *args, **kwargs) -> None:
        """Log a trace message."""
        message = safe_str_convert(message)
        self._logger.opt(depth=1).trace(message, *args, **kwargs)

    def debug(self, message: Any, *args, **kwargs) -> None:
        """Log a debug message."""
        message = safe_str_convert(message)
        self._logger.opt(depth=1).debug(message, *args, **kwargs)

    def info(self, message: Any, *args, **kwargs) -> None:
        """Log an info message."""
        message = safe_str_convert(message)
        self._logger.opt(depth=1).info(message, *args, **kwargs)

    def success(self, message: Any, *args, **kwargs) -> None:
        """Log a success message."""
        message = safe_str_convert(message)
        self._logger.opt(depth=1).success(message, *args, **kwargs)

    def warning(self, message: Any, *args, **kwargs) -> None:
        """Log a warning message."""
        message = safe_str_convert(message)
        self._logger.opt(depth=1).warning(message, *args, **kwargs)

    def error(self, message: Any, *args, **kwargs) -> None:
        """Log an error message."""
        message = safe_str_convert(message)
        self._logger.opt(depth=1).error(message, *args, **kwargs)

    def critical(self, message: Any, *args, **kwargs) -> None:
        """Log a critical message."""
        message = safe_str_convert(message)
        self._logger.opt(depth=1).critical(message, *args, **kwargs)

    def exception(self, message: Any, *args, **kwargs) -> None:
        """Log an exception with traceback."""
        message = safe_str_convert(message)
        self._logger.opt(depth=1, exception=True).log("ERROR", message, *args, **kwargs)

    # ///////////////////////////////////////////////////////////////
    # LOGURU-SPECIFIC METHODS (delegation)
    # ///////////////////////////////////////////////////////////////

    def bind(self, **kwargs: Any) -> Any:
        """Bind context variables to the logger."""
        return self._logger.bind(**kwargs)

    def opt(self, **kwargs: Any) -> Any:
        """Configure logger options."""
        return self._logger.opt(**kwargs)

    def patch(self, patcher: Any) -> Any:
        """Patch log records."""
        return self._logger.patch(patcher)

    # ///////////////////////////////////////////////////////////////
    # GETTER - Returns the underlying loguru logger for advanced usage
    # ///////////////////////////////////////////////////////////////

    def get_loguru(self) -> LoguruLogger:
        """
        Get the underlying Loguru logger instance for advanced usage.

        **Returns:**

            * loguru.Logger: The loguru logger instance

        **Raises:**

            * LoggingError: If the logger is not initialized
        """
        if not self._logger:
            raise LoggingError("File logger not initialized", "file")
        # logger.bind() returns a BoundLogger internally; cast to declared return type
        return cast(LoguruLogger, self._logger)

    def get_log_file(self) -> Path:
        """
        Get the current log file path.

        Returns:
            Path to the log file
        """
        return self._log_file

    def get_file_size(self) -> int:
        """
        Get the current log file size in bytes.

        Returns:
            File size in bytes, or 0 if file doesn't exist or error occurs
        """
        try:
            if self._log_file.exists():
                return self._log_file.stat().st_size
            return 0
        except Exception:
            return 0

    def close(self) -> None:
        """
        Close the logger handler and release file handles.

        This method removes the loguru handler to release file handles,
        which is especially important on Windows where files can remain locked.
        """
        try:
            # Remove existing handler if any
            logger_id: int | None = self._logger_id
            if logger_id is not None:
                # loguru.remove() synchronously flushes and closes the file handle
                self._logger.remove(logger_id)
                self._logger_id = None
        except Exception as e:
            raise LoggingError("Failed to close logger", "file") from e

    # ///////////////////////////////////////////////////////////////
    # FILE OPERATIONS
    # ///////////////////////////////////////////////////////////////

    def add_separator(self) -> None:
        """
        Add a separator line to the log file for session distinction.

        Raises:
            FileOperationError: If writing to the log file fails
        """
        try:
            current_time = datetime.now().strftime("%Y-%m-%d - %H:%M")
            separator = f"\n\n## ==> {current_time}\n## /////////////////////////////////////////////////////////////////\n"
            with open(self._log_file, "a", encoding="utf-8") as log_file:
                log_file.write(separator)
        except Exception as e:
            raise FileOperationError(
                f"Failed to add separator to log file: {e}",
                str(self._log_file),
                "write",
            ) from e

    # ///////////////////////////////////////////////////////////////
    # FORMATTING METHODS
    # ///////////////////////////////////////////////////////////////

    def _custom_formatter(self, record: Any) -> str:
        """
        Custom formatter for file output.

        Args:
            record: Loguru record to format

        Returns:
            Formatted log message (always returns a string, never raises an exception)
        """
        try:
            if not isinstance(record, dict):
                return "????-??-?? ??:??:?? | FORMAT_ERR | unknown:unknown:? - [FORMAT ERROR: InvalidRecord]\n"

            level = (
                record.get("level", {}).name
                if hasattr(record.get("level", {}), "name")
                else "INFO"
            )
            log_level = LogLevel[level]
            return self._format_message(record, log_level)
        except Exception as e:
            # Never raise an exception inside a formatter — return a safe error message
            try:
                return f"????-??-?? ??:??:?? | FORMAT_ERR | unknown:unknown:? - [FORMAT ERROR: {type(e).__name__}]\n"
            except Exception:
                return "????-??-?? ??:??:?? | FORMAT_ERR | unknown:unknown:? - [FORMAT ERROR]\n"

    def _format_message(self, record: dict[str, Any], log_level: LogLevel) -> str:
        """
        Format a log message for file output.

        Args:
            record: Loguru record
            log_level: LogLevel enum instance

        Returns:
            Formatted log message (always returns a valid string)
        """
        try:
            # Safely format the timestamp
            try:
                time_obj: Any = record.get("time")
                # Check if time_obj is a datetime-like object with strftime
                if time_obj is not None:
                    strftime_method = getattr(time_obj, "strftime", None)
                    if strftime_method is not None and callable(strftime_method):
                        # Safe to call strftime - time_obj is datetime-like
                        timestamp = strftime_method("%Y-%m-%d %H:%M:%S")
                    else:
                        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                else:
                    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            except Exception:
                timestamp = "????-??-?? ??:??:??"

            # Clean the message robustly
            message = safe_str_convert(record.get("message", ""))
            # Sanitize for file output (removes problematic characters)
            message = sanitize_for_file(message)

            # Clean the function name
            fn = str(record.get("function", "unknown"))
            fn = fn.replace("<", "").replace(">", "")

            # Safely extract module and line
            module = str(record.get("module", "unknown"))
            line = str(record.get("line", "?"))

            # NOTE: loguru applies `.format_map(record)` on the value returned by a
            # callable formatter, so any literal `{` / `}` in the interpolated content
            # (e.g. boto3 debug payloads like {'Bucket': ...}) would be re-parsed as
            # placeholders -> KeyError / "Max string recursion exceeded". Doubling
            # braces neutralizes them since nothing here needs to remain a placeholder.
            formatted = (
                f"{timestamp} | "
                f"{log_level.label:<10} | "
                f"{module}:{fn}:{line} - "
                f"{message}\n"
            )
            return formatted.replace("{", "{{").replace("}", "}}")
        except Exception as e:
            # Safe fallback
            try:
                return f"????-??-?? ??:??:?? | FORMAT_ERR | unknown:unknown:? - [FORMAT ERROR: {type(e).__name__}]\n"
            except Exception:
                return "????-??-?? ??:??:?? | FORMAT_ERR | unknown:unknown:? - [FORMAT ERROR]\n"

    # ///////////////////////////////////////////////////////////////
    # REPRESENTATION METHODS
    # ///////////////////////////////////////////////////////////////

    def __str__(self) -> str:
        """String representation of the file logger."""
        return f"EzLogger(file={self._log_file}, level={self._level})"

    def __repr__(self) -> str:
        """Detailed string representation of the file logger."""
        return f"EzLogger(file={self._log_file}, level={self._level}, logger_id={self._logger_id})"


# ///////////////////////////////////////////////////////////////
# PUBLIC API
# ///////////////////////////////////////////////////////////////

__all__ = [
    "EzLogger",
]
