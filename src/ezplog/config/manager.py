# ///////////////////////////////////////////////////////////////
# EZPL - Configuration Manager
# Project: ezpl
# ///////////////////////////////////////////////////////////////

"""
Configuration manager for Ezpl logging framework.

This module provides centralized configuration management with support for
file-based configuration, environment variables, and runtime configuration.
"""

from __future__ import annotations

# ///////////////////////////////////////////////////////////////
# IMPORTS
# ///////////////////////////////////////////////////////////////
# Standard library imports
import json
import os
import shlex
import warnings
from pathlib import Path
from typing import Any, cast

# Local imports
from ..core.exceptions import FileOperationError, ValidationError
from ._defaults import DefaultConfiguration

# ///////////////////////////////////////////////////////////////
# CLASSES
# ///////////////////////////////////////////////////////////////


class ConfigurationManager:
    """
    Centralized configuration manager for Ezpl.

    This class handles all configuration operations including loading,
    saving, and merging configuration from multiple sources.
    """

    _ENV_MAPPINGS = {
        "EZPL_LOG_LEVEL": "log-level",
        "EZPL_LOG_FILE": "log-file",
        "EZPL_LOG_DIR": "log-dir",
        "EZPL_PRINTER_LEVEL": "printer-level",
        "EZPL_INDENT_STEP": "indent-step",
        "EZPL_INDENT_SYMBOL": "indent-symbol",
        "EZPL_BASE_INDENT_SYMBOL": "base-indent-symbol",
        "EZPL_FILE_LOGGER_LEVEL": "file-logger-level",
        "EZPL_LOG_FORMAT": "log-format",
        "EZPL_LOG_ROTATION": "log-rotation",
        "EZPL_LOG_RETENTION": "log-retention",
        "EZPL_LOG_COMPRESSION": "log-compression",
    }

    # ///////////////////////////////////////////////////////////////
    # INIT
    # ///////////////////////////////////////////////////////////////

    def __init__(self, config_file: Path | None = None):
        """
        Initialize the configuration manager.

        Args:
            config_file: Optional path to configuration file.
                        Defaults to ~/.ezpl/config.json
        """
        self._config_file = config_file or DefaultConfiguration.CONFIG_FILE
        self._config: dict[str, Any] = {}
        self._explicit_keys: set[str] = set()
        self._load_configuration()

    # ------------------------------------------------
    # PRIVATE HELPER METHODS
    # ------------------------------------------------

    def _load_configuration(self) -> None:
        """
        Load configuration from file and environment variables.

        Priority order:
        1. Environment variables (highest priority)
        2. Configuration file
        3. Default values (lowest priority)
        """
        # Start with defaults — these are never considered "explicit"
        self._config = DefaultConfiguration.get_all_defaults().copy()
        self._explicit_keys = set()

        # Load from file if it exists — keys from file are explicit
        if self._config_file.exists():
            try:
                with open(self._config_file, encoding="utf-8") as f:
                    file_config = json.load(f)
                    self._config.update(file_config)
                    self._explicit_keys.update(file_config.keys())
            except (OSError, json.JSONDecodeError) as e:
                # If file is corrupted, use defaults
                warnings.warn(
                    f"Could not load config file {self._config_file}: {e}",
                    UserWarning,
                    stacklevel=2,
                )

        # Override with environment variables — env keys are explicit
        self._load_from_environment()

    def _load_from_environment(self) -> None:
        """
        Load configuration from environment variables.

        Environment variables should be prefixed with 'EZPL_' and use
        uppercase with underscores (e.g., EZPL_LOG_LEVEL).
        """
        user_env_vars = self._load_user_env_file()

        for env_var, config_key in self._ENV_MAPPINGS.items():
            value = os.getenv(env_var)
            if value is None:
                value = user_env_vars.get(env_var)
            if value is not None:
                # Convert string values to appropriate types
                if config_key in ["indent-step"]:
                    try:
                        self._config[config_key] = int(value)
                    except ValueError as e:
                        raise ValidationError(
                            f"Environment variable {env_var} must be an integer, got: {value!r}",
                            env_var,
                            value,
                        ) from e
                else:
                    self._config[config_key] = value
                self._explicit_keys.add(config_key)

    def _load_user_env_file(self) -> dict[str, str]:
        """
        Load user-level EZPL environment variables from ~/.ezpl/.env.

        Returns:
            Dictionary of environment variables found in user env file.
        """
        env_file = DefaultConfiguration.CONFIG_DIR / ".env"
        env_vars: dict[str, str] = {}

        if not env_file.exists():
            return env_vars

        try:
            with open(env_file, encoding="utf-8") as f:
                for line in f:
                    stripped = line.strip()
                    if not stripped or stripped.startswith("#") or "=" not in stripped:
                        continue
                    key, value = stripped.split("=", 1)
                    env_vars[key.strip()] = value.strip()
        except OSError:
            return {}

        return env_vars

    # ///////////////////////////////////////////////////////////////
    # GETTER
    # ///////////////////////////////////////////////////////////////

    @property
    def config_file(self) -> Path:
        """Return the path to the configuration file."""
        return self._config_file

    def get(self, key: str, default: Any = None) -> Any:
        """
        Get a configuration value.

        Args:
            key: Configuration key
            default: Default value if key not found

        Returns:
            Configuration value or default
        """
        return self._config.get(key, default)

    def has_key(self, key: str) -> bool:
        """
        Check if a configuration key is explicitly set (not just a default).

        A key is considered explicit when it comes from a config file, an
        environment variable, or a direct call to configure()/set()/update().
        Keys that are present only because of default values return False.

        Args:
            key: Configuration key to check

        Returns:
            True if the key was explicitly set, False if it is only a default.
        """
        return key in self._explicit_keys

    def get_log_level(self) -> str:
        """Get the current log level."""
        return cast(str, self.get("log-level", DefaultConfiguration.LOG_LEVEL))

    def get_log_file(self) -> Path:
        """Get the current log file path."""
        log_file = self.get("log-file", DefaultConfiguration.LOG_FILE)
        log_dir = self.get("log-dir", DefaultConfiguration.LOG_DIR)

        # Convert to Path if string
        log_file_path = Path(log_file) if isinstance(log_file, str) else log_file
        log_dir_path = Path(log_dir) if isinstance(log_dir, str) else log_dir

        # If log_file is relative, make it relative to log_dir
        if not log_file_path.is_absolute():
            return log_dir_path / log_file_path
        return log_file_path

    def get_printer_level(self) -> str:
        """Get the current printer level."""
        return cast(str, self.get("printer-level", DefaultConfiguration.PRINTER_LEVEL))

    def get_file_logger_level(self) -> str:
        """Get the current file logger level."""
        return cast(
            str, self.get("file-logger-level", DefaultConfiguration.FILE_LOGGER_LEVEL)
        )

    def get_indent_step(self) -> int:
        """Get the current indent step."""
        return cast(int, self.get("indent-step", DefaultConfiguration.INDENT_STEP))

    def get_indent_symbol(self) -> str:
        """Get the current indent symbol."""
        return cast(str, self.get("indent-symbol", DefaultConfiguration.INDENT_SYMBOL))

    def get_base_indent_symbol(self) -> str:
        """Get the current base indent symbol."""
        return cast(
            str, self.get("base-indent-symbol", DefaultConfiguration.BASE_INDENT_SYMBOL)
        )

    def get_log_format(self) -> str:
        """Get the current log format."""
        return cast(str, self.get("log-format", DefaultConfiguration._LOG_FORMAT))

    def get_log_rotation(self) -> str | None:
        """Get the current log rotation setting."""
        return cast(
            str | None, self.get("log-rotation", DefaultConfiguration.LOG_ROTATION)
        )

    def get_log_retention(self) -> str | None:
        """Get the current log retention setting."""
        return cast(
            str | None, self.get("log-retention", DefaultConfiguration.LOG_RETENTION)
        )

    def get_log_compression(self) -> str | None:
        """Get the current log compression setting."""
        return cast(
            str | None,
            self.get("log-compression", DefaultConfiguration.LOG_COMPRESSION),
        )

    def get_log_backtrace(self) -> bool:
        """Get the current log backtrace setting."""
        return cast(bool, self.get("log-backtrace", DefaultConfiguration.LOG_BACKTRACE))

    def get_log_diagnose(self) -> bool:
        """Get the current log diagnose setting."""
        return cast(bool, self.get("log-diagnose", DefaultConfiguration.LOG_DIAGNOSE))

    def get_all(self) -> dict[str, Any]:
        """
        Get all configuration values.

        Returns:
            Dictionary containing all configuration values
        """
        return self._config.copy()

    # ///////////////////////////////////////////////////////////////
    # SETTER
    # ///////////////////////////////////////////////////////////////

    def set(self, key: str, value: Any) -> None:
        """
        Set a configuration value.

        Args:
            key: Configuration key
            value: Configuration value
        """
        self._config[key] = value
        self._explicit_keys.add(key)

    def update(self, config_dict: dict[str, Any]) -> None:
        """
        Update configuration with new values.

        Args:
            config_dict: Dictionary of configuration values to update
        """
        self._config.update(config_dict)
        self._explicit_keys.update(config_dict.keys())

    # ///////////////////////////////////////////////////////////////
    # FILE OPERATIONS
    # ///////////////////////////////////////////////////////////////

    def save(self) -> None:
        """
        Save current configuration to file.

        Raises:
            FileOperationError: If unable to write to configuration file
        """
        try:
            # Ensure config directory exists
            self._config_file.parent.mkdir(parents=True, exist_ok=True)

            # Save configuration
            with open(self._config_file, "w", encoding="utf-8") as f:
                json.dump(self._config, f, indent=4, ensure_ascii=False)
        except OSError as e:
            raise FileOperationError(
                f"Could not save configuration to {self._config_file}: {e}",
                str(self._config_file),
                "save",
            ) from e

    def reset_to_defaults(self) -> None:
        """Reset configuration to default values."""
        self._config = DefaultConfiguration.get_all_defaults().copy()
        self._explicit_keys = set()

    def reload(self) -> None:
        """
        Reload configuration from file and environment variables.

        This method reloads the configuration, useful when environment
        variables or the config file have changed after initialization.
        """
        self._load_configuration()

    def export_to_script(
        self, output_file: str | Path, platform: str | None = None
    ) -> None:
        """
        Export configuration as environment variables script.

        Args:
            output_file: Path to output script file
            platform: Target platform ('windows', 'unix', or None for auto-detect)

        Raises:
            FileOperationError: If unable to write to output file
        """
        if platform is None:
            import sys

            platform = "windows" if sys.platform == "win32" else "unix"

        output_path = Path(output_file)

        try:
            with open(output_path, "w", encoding="utf-8") as f:
                if platform == "windows":
                    # Generate Batch script for Windows
                    for env_var, config_key in self._ENV_MAPPINGS.items():
                        value = self._config.get(config_key)
                        if value is None:
                            continue
                        safe_value = str(value).replace('"', '""')
                        f.write(f'set "{env_var}={safe_value}"\n')
                else:
                    # Generate Bash script for Unix/Linux/macOS
                    f.write("#!/bin/bash\n")
                    for env_var, config_key in self._ENV_MAPPINGS.items():
                        value = self._config.get(config_key)
                        if value is None:
                            continue
                        f.write(f"export {env_var}={shlex.quote(str(value))}\n")
        except OSError as e:
            raise FileOperationError(
                f"Could not write to {output_path}: {e}",
                str(output_path),
                "export",
            ) from e

    # ///////////////////////////////////////////////////////////////
    # REPRESENTATION METHODS
    # ///////////////////////////////////////////////////////////////

    def __str__(self) -> str:
        """String representation of the configuration."""
        return f"ConfigurationManager(config_file={self._config_file})"

    def __repr__(self) -> str:
        """Detailed string representation of the configuration."""
        return f"ConfigurationManager(config_file={self._config_file}, config={self._config})"


# ///////////////////////////////////////////////////////////////
# PUBLIC API
# ///////////////////////////////////////////////////////////////

__all__ = [
    "ConfigurationManager",
]
