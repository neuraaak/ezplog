# ///////////////////////////////////////////////////////////////
# EZPL - Tests unitaires ConfigurationManager
# Project: ezpl
# ///////////////////////////////////////////////////////////////

"""
Unit tests for ConfigurationManager.

Tests cover:
- Initialization
- Get/Set/Update operations
- Save/Load operations
- Priority order (env > file > default)
- Getters for specific values
- Reset to defaults
- Export to script
- Error handling
"""

from __future__ import annotations

# ///////////////////////////////////////////////////////////////
# IMPORTS
# ///////////////////////////////////////////////////////////////
# Standard library imports
import json
import os
from pathlib import Path
from unittest.mock import patch

# Third-party imports
import pytest

# Local imports
from ezplog.config import ConfigurationManager
from ezplog.core.exceptions import FileOperationError

# ///////////////////////////////////////////////////////////////
# TESTS
# ///////////////////////////////////////////////////////////////


class TestInitialization:
    """Tests for ConfigurationManager initialization."""

    def test_should_use_default_config_file_when_no_config_file_is_specified(
        self,
    ) -> None:
        """Test initialization with default config file."""
        config = ConfigurationManager()
        assert config._config_file is not None

    def test_should_use_custom_config_file_when_config_file_path_is_given(
        self, temp_config_file: Path
    ) -> None:
        """Test initialization with custom config file."""
        config = ConfigurationManager(config_file=temp_config_file)
        assert config._config_file == temp_config_file

    def test_should_load_default_values_when_no_config_file_exists(
        self, temp_config_file: Path
    ) -> None:
        """Test that initialization loads default values."""
        config = ConfigurationManager(config_file=temp_config_file)
        all_config = config.get_all()
        assert len(all_config) > 0
        # Verify some default keys exist
        assert "log-level" in all_config or "printer-level" in all_config

    def test_should_override_defaults_with_file_values_when_config_file_exists(
        self, temp_config_file: Path
    ) -> None:
        """Test that initialization loads from config file."""
        config_data = {"log-level": "DEBUG", "printer-level": "WARNING"}
        temp_config_file.parent.mkdir(parents=True, exist_ok=True)
        temp_config_file.write_text(json.dumps(config_data), encoding="utf-8")

        config = ConfigurationManager(config_file=temp_config_file)
        assert config.get("log-level") == "DEBUG"
        assert config.get("printer-level") == "WARNING"

    def test_should_override_defaults_with_env_values_when_env_vars_are_set(
        self,
        temp_config_file: Path,
        clean_env: None,  # noqa: ARG002
    ) -> None:
        """Test that initialization loads from environment variables."""
        os.environ["EZPL_LOG_LEVEL"] = "ERROR"
        os.environ["EZPL_PRINTER_LEVEL"] = "DEBUG"

        config = ConfigurationManager(config_file=temp_config_file)
        # Environment should override defaults
        assert config.get("log-level") == "ERROR"
        assert config.get("printer-level") == "DEBUG"

    def test_should_override_defaults_with_user_env_file_values_when_env_file_exists(
        self,
        temp_dir: Path,
        temp_config_file: Path,
        clean_env: None,  # noqa: ARG002
    ) -> None:
        """Test that initialization loads from ~/.ezpl/.env fallback file."""
        env_file = temp_dir / ".env"
        env_file.write_text(
            "EZPL_LOG_LEVEL=CRITICAL\nEZPL_PRINTER_LEVEL=WARNING\n",
            encoding="utf-8",
        )

        with pytest.MonkeyPatch().context() as m:
            m.setattr("ezplog.config.manager.DefaultConfiguration.CONFIG_DIR", temp_dir)
            config = ConfigurationManager(config_file=temp_config_file)

        assert config.get("log-level") == "CRITICAL"
        assert config.get("printer-level") == "WARNING"

    def test_should_warn_and_fallback_to_defaults_when_config_file_has_invalid_json(
        self, temp_config_file: Path
    ) -> None:
        """Test that initialization handles invalid JSON gracefully."""
        temp_config_file.parent.mkdir(parents=True, exist_ok=True)
        temp_config_file.write_text("{invalid json}", encoding="utf-8")

        # Should warn and fall back to defaults
        with pytest.warns(UserWarning, match="Could not load config file"):
            config = ConfigurationManager(config_file=temp_config_file)
        assert config is not None


class TestGetSetUpdate:
    """Tests for get, set, and update operations."""

    def test_should_return_value_when_key_exists_in_config(
        self, config_manager: ConfigurationManager
    ) -> None:
        """Test get() with existing key."""
        config_manager.set("test-key", "test-value")
        assert config_manager.get("test-key") == "test-value"

    def test_should_return_none_when_key_does_not_exist_in_config(
        self, config_manager: ConfigurationManager
    ) -> None:
        """Test get() with non-existing key."""
        assert config_manager.get("non-existing-key") is None
        assert config_manager.get("non-existing-key", "default") == "default"

    def test_should_persist_value_when_set_is_called_with_key_and_value(
        self, config_manager: ConfigurationManager
    ) -> None:
        """Test set() method."""
        config_manager.set("test-key", "test-value")
        assert config_manager.get("test-key") == "test-value"

    def test_should_persist_multiple_values_when_update_is_called_with_dict(
        self, config_manager: ConfigurationManager
    ) -> None:
        """Test update() with multiple keys."""
        config_manager.update({"key1": "value1", "key2": "value2"})
        assert config_manager.get("key1") == "value1"
        assert config_manager.get("key2") == "value2"

    def test_should_return_all_config_entries_when_get_all_is_called(
        self, config_manager: ConfigurationManager
    ) -> None:
        """Test get_all() method."""
        config_manager.set("test-key", "test-value")
        all_config = config_manager.get_all()
        assert isinstance(all_config, dict)
        assert "test-key" in all_config


class TestGetters:
    """Tests for specific getter methods."""

    def test_should_return_valid_log_level_string_when_get_log_level_is_called(
        self, config_manager: ConfigurationManager
    ) -> None:
        """Test get_log_level() method."""
        level = config_manager.get_log_level()
        assert isinstance(level, str)
        assert level in ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]

    def test_should_return_path_object_when_get_log_file_is_called(
        self, config_manager: ConfigurationManager
    ) -> None:
        """Test get_log_file() method."""
        log_file = config_manager.get_log_file()
        assert isinstance(log_file, Path)

    def test_should_return_level_string_when_get_printer_level_is_called(
        self, config_manager: ConfigurationManager
    ) -> None:
        """Test get_printer_level() method."""
        level = config_manager.get_printer_level()
        assert isinstance(level, str)

    def test_should_return_level_string_when_get_file_logger_level_is_called(
        self, config_manager: ConfigurationManager
    ) -> None:
        """Test get_file_logger_level() method."""
        level = config_manager.get_file_logger_level()
        assert isinstance(level, str)

    def test_should_return_positive_int_when_get_indent_step_is_called(
        self, config_manager: ConfigurationManager
    ) -> None:
        """Test get_indent_step() method."""
        step = config_manager.get_indent_step()
        assert isinstance(step, int)
        assert step > 0

    def test_should_return_string_when_get_indent_symbol_is_called(
        self, config_manager: ConfigurationManager
    ) -> None:
        """Test get_indent_symbol() method."""
        symbol = config_manager.get_indent_symbol()
        assert isinstance(symbol, str)

    def test_should_return_string_when_get_base_indent_symbol_is_called(
        self, config_manager: ConfigurationManager
    ) -> None:
        """Test get_base_indent_symbol() method."""
        symbol = config_manager.get_base_indent_symbol()
        assert isinstance(symbol, str)

    def test_should_return_rotation_config_when_get_log_rotation_is_called(
        self, config_manager: ConfigurationManager
    ) -> None:
        """Test get_log_rotation() method."""
        rotation = config_manager.get_log_rotation()
        # Can be None or a string
        assert rotation is None or isinstance(rotation, str)

    def test_should_return_retention_config_when_get_log_retention_is_called(
        self, config_manager: ConfigurationManager
    ) -> None:
        """Test get_log_retention() method."""
        retention = config_manager.get_log_retention()
        # Can be None or a string
        assert retention is None or isinstance(retention, str)

    def test_should_return_compression_config_when_get_log_compression_is_called(
        self, config_manager: ConfigurationManager
    ) -> None:
        """Test get_log_compression() method."""
        compression = config_manager.get_log_compression()
        # Can be None or a string
        assert compression is None or isinstance(compression, str)


class TestFileOperations:
    """Tests for file operations."""

    def test_should_write_values_to_file_when_save_is_called(
        self, temp_config_file: Path
    ) -> None:
        """Test save() method."""
        config = ConfigurationManager(config_file=temp_config_file)
        config.set("test-key", "test-value")
        config.save()

        # Verify file was created and contains the value
        assert temp_config_file.exists()
        content = temp_config_file.read_text(encoding="utf-8")
        assert "test-key" in content
        assert "test-value" in content

    def test_should_create_parent_directory_when_save_is_called_and_dir_does_not_exist(
        self, temp_dir: Path
    ) -> None:
        """Test that save() creates directory if it doesn't exist."""
        config_file = temp_dir / "subdir" / "config.json"
        config = ConfigurationManager(config_file=config_file)
        config.save()
        assert config_file.exists()

    def test_should_raise_file_operation_error_when_save_encounters_permission_denied(
        self, temp_config_file: Path
    ) -> None:
        """Test that save() handles permission errors."""
        config = ConfigurationManager(config_file=temp_config_file)
        config.set("test-key", "test-value")

        with patch(  # noqa: SIM117
            "builtins.open", side_effect=PermissionError("Permission denied")
        ):
            with pytest.raises(FileOperationError):
                config.save()

    def test_should_remove_custom_keys_when_reset_to_defaults_is_called(
        self, config_manager: ConfigurationManager
    ) -> None:
        """Test reset_to_defaults() method."""
        config_manager.set("custom-key", "custom-value")
        config_manager.reset_to_defaults()
        # Custom key should be removed
        assert config_manager.get("custom-key") is None

    def test_should_pick_up_new_file_values_when_reload_is_called(
        self, temp_config_file: Path
    ) -> None:
        """Test reload() method."""
        # Create initial config
        config_data = {"log-level": "INFO"}
        temp_config_file.parent.mkdir(parents=True, exist_ok=True)
        temp_config_file.write_text(json.dumps(config_data), encoding="utf-8")

        config = ConfigurationManager(config_file=temp_config_file)
        assert config.get("log-level") == "INFO"

        # Modify config file
        config_data["log-level"] = "DEBUG"
        temp_config_file.write_text(json.dumps(config_data), encoding="utf-8")

        # Reload
        config.reload()
        assert config.get("log-level") == "DEBUG"


class TestPriorityOrder:
    """Tests for configuration priority order."""

    def test_should_prioritize_env_vars_over_file_config_when_both_are_set(
        self,
        temp_config_file: Path,
        clean_env: None,  # noqa: ARG002
    ) -> None:
        """Test that environment variables override config file."""
        # Set config file
        config_data = {"log-level": "INFO"}
        temp_config_file.parent.mkdir(parents=True, exist_ok=True)
        temp_config_file.write_text(json.dumps(config_data), encoding="utf-8")

        # Set environment variable
        os.environ["EZPL_LOG_LEVEL"] = "ERROR"

        config = ConfigurationManager(config_file=temp_config_file)
        # Environment should override file
        assert config.get("log-level") == "ERROR"

    def test_should_prioritize_file_config_over_defaults_when_file_exists(
        self, temp_config_file: Path
    ) -> None:
        """Test that config file overrides defaults."""
        config_data = {"log-level": "WARNING"}
        temp_config_file.parent.mkdir(parents=True, exist_ok=True)
        temp_config_file.write_text(json.dumps(config_data), encoding="utf-8")

        config = ConfigurationManager(config_file=temp_config_file)
        # File should override default
        assert config.get("log-level") == "WARNING"


class TestExport:
    """Tests for export operations."""

    def test_should_generate_windows_batch_script_when_windows_platform_is_specified(
        self, temp_dir: Path
    ) -> None:
        """Test export_to_script() for Windows."""
        config = ConfigurationManager()
        config.set("log-level", "DEBUG")
        output_file = temp_dir / "config.bat"

        with patch("sys.platform", "win32"):
            config.export_to_script(output_file, platform="windows")

        assert output_file.exists()
        content = output_file.read_text(encoding="utf-8")
        assert 'set "EZPL_LOG_LEVEL=DEBUG"' in content
        assert "set log-level=" not in content

    def test_should_quote_windows_batch_values_when_value_contains_special_chars(
        self, temp_dir: Path
    ) -> None:
        """Windows export should keep values safe in batch files."""
        config = ConfigurationManager()
        config.set("log-level", 'INFO&echo "x"')
        output_file = temp_dir / "config_special.bat"

        with patch("sys.platform", "win32"):
            config.export_to_script(output_file, platform="windows")

        content = output_file.read_text(encoding="utf-8")
        assert 'set "EZPL_LOG_LEVEL=INFO&echo ""x"""' in content

    def test_should_generate_unix_bash_script_when_unix_platform_is_specified(
        self, temp_dir: Path
    ) -> None:
        """Test export_to_script() for Unix."""
        config = ConfigurationManager()
        config.set("log-rotation", "10 MB")
        output_file = temp_dir / "config.sh"

        with patch("sys.platform", "linux"):
            config.export_to_script(output_file, platform="unix")

        assert output_file.exists()
        content = output_file.read_text(encoding="utf-8")
        assert "#!/bin/bash" in content
        assert "export EZPL_LOG_ROTATION='10 MB'" in content
        assert "export log-rotation=" not in content

    def test_should_raise_file_operation_error_when_export_encounters_io_error(
        self, temp_dir: Path
    ) -> None:
        """Test that export handles IO errors."""
        config = ConfigurationManager()
        invalid_path = temp_dir / "invalid" / "path" / "script.sh"

        with patch(  # noqa: SIM117
            "builtins.open", side_effect=OSError("Permission denied")
        ):
            with pytest.raises(FileOperationError):
                config.export_to_script(invalid_path)


class TestErrorHandling:
    """Tests for error handling."""

    def test_should_use_defaults_when_config_file_path_does_not_exist(
        self, temp_dir: Path
    ) -> None:
        """Test handling of missing config file."""
        config_file = temp_dir / "nonexistent" / "config.json"
        config = ConfigurationManager(config_file=config_file)
        # Should use defaults
        assert config is not None

    def test_should_warn_and_fallback_to_defaults_when_config_file_is_corrupted(
        self, temp_config_file: Path
    ) -> None:
        """Test handling of corrupted config file."""
        temp_config_file.parent.mkdir(parents=True, exist_ok=True)
        temp_config_file.write_text("{invalid json}", encoding="utf-8")

        # Should warn and fall back to defaults
        with pytest.warns(UserWarning, match="Could not load config file"):
            config = ConfigurationManager(config_file=temp_config_file)
        assert config is not None


@pytest.mark.unit
def test_defaults_expose_traceback_keys():
    from ezplog.config._defaults import DefaultConfiguration

    defaults = DefaultConfiguration.get_all_defaults()
    assert defaults["log-backtrace"] is True
    assert defaults["log-diagnose"] is False


@pytest.mark.unit
def test_file_logger_defaults_expose_traceback_keys():
    from ezplog.config._defaults import DefaultConfiguration

    defaults = DefaultConfiguration.get_file_logger_defaults()
    assert "log-backtrace" in defaults
    assert "log-diagnose" in defaults
