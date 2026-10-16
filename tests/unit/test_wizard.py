# ///////////////////////////////////////////////////////////////
# EZPL - Tests unitaires RichWizard
# Project: ezpl
# ///////////////////////////////////////////////////////////////

"""
Unit tests for RichWizard.

Tests cover:
- Panel methods (all types)
- Table methods (all types)
- JSON display
- Progress bars (all types)
- Dynamic layered progress
- Error handling
"""

from __future__ import annotations

# ///////////////////////////////////////////////////////////////
# IMPORTS
# ///////////////////////////////////////////////////////////////
# Standard library imports
import inspect
import time

# Third-party imports
import pytest

# Local imports
from ezplog import Ezpl

# ///////////////////////////////////////////////////////////////
# TESTS
# ///////////////////////////////////////////////////////////////


@pytest.fixture
def wizard():
    """Create a RichWizard instance for testing."""
    ezpl = Ezpl()
    return ezpl.get_printer().wizard


class TestPanels:
    """Tests for panel methods."""

    def test_should_not_crash_when_panel_is_called_with_content_only(
        self, wizard
    ) -> None:
        """Test basic panel() method."""
        wizard.panel("Test content")
        # Verify no exception raised

    def test_should_not_crash_when_panel_is_called_with_title(self, wizard) -> None:
        """Test panel() with title."""
        wizard.panel("Test content", title="Test Title")
        # Verify no exception raised

    def test_should_not_crash_when_info_panel_is_called(self, wizard) -> None:
        """Test info_panel() method."""
        wizard.info_panel("Info Title", "Info content")
        # Verify no exception raised

    def test_should_not_crash_when_success_panel_is_called(self, wizard) -> None:
        """Test success_panel() method."""
        wizard.success_panel("Success Title", "Success content")
        # Verify no exception raised

    def test_should_not_crash_when_error_panel_is_called(self, wizard) -> None:
        """Test error_panel() method."""
        wizard.error_panel("Error Title", "Error content")
        # Verify no exception raised

    def test_should_not_crash_when_warning_panel_is_called(self, wizard) -> None:
        """Test warning_panel() method."""
        wizard.warning_panel("Warning Title", "Warning content")
        # Verify no exception raised

    def test_should_not_crash_when_installation_panel_is_called_with_pending_status(
        self, wizard
    ) -> None:
        """Test installation_panel() with pending status."""
        wizard.installation_panel("Step 1", "Installing...", status="pending")
        # Verify no exception raised

    def test_should_not_crash_when_installation_panel_is_called_with_success_status(
        self, wizard
    ) -> None:
        """Test installation_panel() with success status."""
        wizard.installation_panel("Step 1", "Installed", status="success")
        # Verify no exception raised

    def test_should_not_crash_when_installation_panel_is_called_with_error_status(
        self, wizard
    ) -> None:
        """Test installation_panel() with error status."""
        wizard.installation_panel("Step 1", "Failed", status="error")
        # Verify no exception raised

    def test_should_not_crash_when_panel_is_called_with_custom_style(
        self, wizard
    ) -> None:
        """Test panel() with custom style."""
        wizard.panel("Content", border_style="red", width=50)
        # Verify no exception raised


class TestTables:
    """Tests for table methods."""

    def test_should_not_crash_when_table_is_called_with_dict_list(self, wizard) -> None:
        """Test basic table() method."""
        data = [{"Name": "Alice", "Age": 30}, {"Name": "Bob", "Age": 25}]
        wizard.table(data)
        # Verify no exception raised

    def test_should_not_crash_when_table_is_called_with_title(self, wizard) -> None:
        """Test table() with title."""
        data = [{"Name": "Alice", "Age": 30}]
        wizard.table(data, title="Users")
        # Verify no exception raised

    def test_should_not_crash_when_table_from_columns_is_called(self, wizard) -> None:
        """Test table_from_columns() method."""
        columns = ["Name", "Age"]
        rows = [["Alice", "30"], ["Bob", "25"]]
        wizard.table_from_columns("Users", columns, rows)
        # Verify no exception raised

    def test_should_not_crash_when_status_table_is_called(self, wizard) -> None:
        """Test status_table() method."""
        data = [
            {"Service": "API", "Status": "success"},
            {"Service": "DB", "Status": "error"},
        ]
        wizard.status_table("Services", data)
        # Verify no exception raised

    def test_should_not_crash_when_dependency_table_is_called(self, wizard) -> None:
        """Test dependency_table() method."""
        deps = {"requests": "2.31.0", "click": "8.1.0", "missing": ""}
        wizard.dependency_table(deps)
        # Verify no exception raised

    def test_should_not_crash_when_command_table_is_called(self, wizard) -> None:
        """Test command_table() method."""
        commands = [
            {
                "command": "install",
                "description": "Install package",
                "category": "Package",
            },
            {
                "command": "update",
                "description": "Update package",
                "category": "Package",
            },
        ]
        wizard.command_table(commands)
        # Verify no exception raised

    def test_should_not_crash_when_table_is_called_with_empty_list(
        self, wizard
    ) -> None:
        """Test table() with empty data."""
        wizard.table([])
        # Should not raise error, just return early
        # Verify no exception raised


class TestJSON:
    """Tests for JSON display."""

    def test_should_not_crash_when_json_is_called_with_dict(self, wizard) -> None:
        """Test json() with dictionary."""
        wizard.json({"name": "Alice", "age": 30})
        # Verify no exception raised

    def test_should_not_crash_when_json_is_called_with_list(self, wizard) -> None:
        """Test json() with list."""
        wizard.json([1, 2, 3, {"nested": "value"}])
        # Verify no exception raised

    def test_should_not_crash_when_json_is_called_with_json_string(
        self, wizard
    ) -> None:
        """Test json() with JSON string."""
        wizard.json('{"key": "value"}')
        # Verify no exception raised

    def test_should_not_crash_when_json_is_called_with_title(self, wizard) -> None:
        """Test json() with title."""
        wizard.json({"key": "value"}, title="Config")
        # Verify no exception raised

    def test_should_not_crash_when_json_is_called_with_custom_indent(
        self, wizard
    ) -> None:
        """Test json() with custom indent."""
        wizard.json({"key": "value"}, indent=4)
        # Verify no exception raised

    def test_should_not_crash_when_json_is_called_with_highlight_disabled(
        self, wizard
    ) -> None:
        """Test json() without highlighting."""
        wizard.json({"key": "value"}, highlight=False)
        # Verify no exception raised

    def test_should_handle_gracefully_when_json_is_called_with_invalid_json_string(
        self, wizard
    ) -> None:
        """Test json() with invalid JSON string."""
        wizard.json("{invalid json}")
        # Should handle gracefully
        # Verify no exception raised


class TestProgressBars:
    """Tests for progress bar methods."""

    def test_should_use_task_id_in_all_progress_method_signatures_when_inspected(
        self,
    ) -> None:
        """Progress context managers should type task IDs as TaskID."""
        from ezplog.handlers.wizard._progress import ProgressMixin

        methods = [
            "progress",
            "spinner",
            "spinner_with_status",
            "download_progress",
            "file_download_progress",
            "dependency_progress",
            "package_install_progress",
            "step_progress",
            "file_copy_progress",
            "installation_progress",
            "build_progress",
            "deployment_progress",
        ]

        for method_name in methods:
            method = getattr(ProgressMixin, method_name)
            signature_text = str(inspect.signature(method))
            assert "TaskID" in signature_text, (
                f"Expected TaskID in signature for {method_name}, got: {signature_text}"
            )

    def test_should_not_crash_when_progress_is_used_with_total(self, wizard) -> None:
        """Test basic progress() method."""
        with wizard.progress("Processing...", total=100) as (progress, task):
            progress.update(task, advance=50)
        # Verify no exception raised

    def test_should_not_crash_when_progress_is_used_with_no_total(self, wizard) -> None:
        """Test progress() with indeterminate total."""
        with wizard.progress("Processing...", total=None) as (progress, task):
            progress.update(task)
        # Verify no exception raised

    def test_should_not_crash_when_spinner_context_is_used(self, wizard) -> None:
        """Test spinner() method."""
        with wizard.spinner("Loading...") as (_progress, _task):
            time.sleep(0.1)
        # Verify no exception raised

    def test_should_not_crash_when_spinner_with_status_context_is_used(
        self, wizard
    ) -> None:
        """Test spinner_with_status() method."""
        with wizard.spinner_with_status("Processing...") as (progress, task):
            progress.update(task, status="Step 1/3")
        # Verify no exception raised

    def test_should_not_crash_when_download_progress_context_is_used(
        self, wizard
    ) -> None:
        """Test download_progress() method."""
        with wizard.download_progress("Downloading...") as (progress, task):
            progress.update(task, advance=50, total=100)
        # Verify no exception raised

    def test_should_not_crash_when_file_download_progress_context_is_used(
        self, wizard
    ) -> None:
        """Test file_download_progress() method."""
        with wizard.file_download_progress("file.zip", 1024000) as (progress, task):
            progress.update(task, advance=512000)
        # Verify no exception raised

    def test_should_not_crash_when_dependency_progress_is_used(self, wizard) -> None:
        """Test dependency_progress() yields once per dependency."""
        deps = ["requests", "click", "rich"]
        seen = []
        for progress, task, dep in wizard.dependency_progress(deps):
            progress.advance(task)
            seen.append(dep)
        assert seen == deps

    def test_should_not_crash_when_package_install_progress_is_used(
        self, wizard
    ) -> None:
        """Test package_install_progress() yields once per package."""
        packages = [("requests", "2.31.0"), ("click", "8.1.0")]
        seen = []
        for progress, task, pkg, ver in wizard.package_install_progress(packages):
            progress.advance(task)
            seen.append((pkg, ver))
        assert seen == packages

    def test_should_not_crash_when_step_progress_context_is_used(self, wizard) -> None:
        """Test step_progress() method."""
        steps = [("Init", "Initializing"), ("Install", "Installing")]
        with wizard.step_progress(steps) as (progress, task, _steps_list):
            for _i in range(len(steps)):
                progress.advance(task)
        # Verify no exception raised

    def test_should_not_crash_when_file_copy_progress_context_is_used(
        self, wizard
    ) -> None:
        """Test file_copy_progress() method."""
        files = ["file1.txt", "file2.txt", "file3.txt"]
        with wizard.file_copy_progress(files) as (progress, task, _files_list):
            for _i in range(len(files)):
                progress.advance(task)
        # Verify no exception raised

    def test_should_not_crash_when_installation_progress_is_used(self, wizard) -> None:
        """Test installation_progress() yields once per step."""
        steps = [("Init", "Initializing"), ("Install", "Installing")]
        seen = []
        for progress, task, name, desc in wizard.installation_progress(steps):
            progress.advance(task)
            seen.append((name, desc))
        assert seen == steps

    def test_should_not_crash_when_build_progress_is_used(self, wizard) -> None:
        """Test build_progress() yields once per weighted phase."""
        phases = [("Compile", 50), ("Test", 30), ("Package", 20)]
        seen = []
        for progress, task, phase, weight in wizard.build_progress(phases):
            progress.update(task, completed=progress.tasks[task].completed + weight)
            seen.append((phase, weight))
        assert seen == phases

    def test_should_not_crash_when_deployment_progress_is_used(self, wizard) -> None:
        """Test deployment_progress() yields once per stage."""
        stages = ["Prepare", "Deploy", "Verify"]
        seen = []
        for progress, task, stage in wizard.deployment_progress(stages):
            progress.advance(task)
            seen.append(stage)
        assert seen == stages

    def test_should_not_crash_when_layered_progress_context_is_used(
        self, wizard
    ) -> None:
        """Test layered_progress() method."""
        layers = [
            {"name": "Layer1", "total": 100},
            {"name": "Layer2", "total": 50},
        ]
        with wizard.layered_progress(layers) as (progress, task_ids):
            for _layer_name, task_id in task_ids.items():
                progress.update(task_id, advance=50)
        # Verify no exception raised


class TestDynamicProgress:
    """Tests for dynamic layered progress."""

    def test_should_not_crash_when_dynamic_layered_progress_is_used_with_single_progress_stage(
        self, wizard
    ) -> None:
        """Test basic dynamic_layered_progress()."""
        stages = [
            {
                "name": "step1",
                "type": "progress",
                "description": "Step 1",
                "total": 100,
            },
        ]
        with wizard.dynamic_layered_progress(stages) as progress:
            progress.update_layer("step1", 50, "Processing...")
            progress.complete_layer("step1")
        # Verify no exception raised

    def test_should_not_crash_when_dynamic_layered_progress_has_main_and_sub_stages(
        self, wizard
    ) -> None:
        """Test dynamic_layered_progress() with main layer."""
        stages = [
            {"name": "main", "type": "main", "description": "Overall Progress"},
            {
                "name": "step1",
                "type": "progress",
                "description": "Step 1",
                "total": 100,
            },
            {
                "name": "step2",
                "type": "steps",
                "description": "Step 2",
                "steps": ["A", "B"],
            },
        ]
        with wizard.dynamic_layered_progress(stages) as progress:
            progress.update_layer("step1", 50)
            progress.complete_layer("step1")
            progress.update_layer("step2", 1)
            progress.complete_layer("step2")
        # Verify no exception raised

    def test_should_not_crash_when_dynamic_layered_progress_has_download_stage(
        self, wizard
    ) -> None:
        """Test dynamic_layered_progress() with download layer."""
        stages = [
            {
                "name": "download",
                "type": "download",
                "description": "Downloading",
                "total_size": 1024000,
                "filename": "file.zip",
            },
        ]
        with wizard.dynamic_layered_progress(stages) as progress:
            progress.update_layer("download", 512000, "Downloading...")
            progress.complete_layer("download")
        # Verify no exception raised

    def test_should_not_crash_when_dynamic_layered_progress_has_spinner_stage(
        self, wizard
    ) -> None:
        """Test dynamic_layered_progress() with spinner layer."""
        stages = [
            {"name": "spinner", "type": "spinner", "description": "Processing..."},
        ]
        with wizard.dynamic_layered_progress(stages) as progress:
            progress.update_layer("spinner", 0, "Working...")
            progress.complete_layer("spinner")
        # Verify no exception raised

    def test_should_not_crash_when_error_is_handled_via_dynamic_layered_progress(
        self, wizard
    ) -> None:
        """Test dynamic_layered_progress() error handling."""
        stages = [
            {
                "name": "step1",
                "type": "progress",
                "description": "Step 1",
                "total": 100,
            },
        ]
        with wizard.dynamic_layered_progress(stages) as progress:
            progress.handle_error("step1", "Test error")
        # Verify no exception raised

    def test_should_not_crash_when_emergency_stop_is_called_on_dynamic_layered_progress(
        self, wizard
    ) -> None:
        """Test dynamic_layered_progress() emergency stop."""
        stages = [
            {
                "name": "step1",
                "type": "progress",
                "description": "Step 1",
                "total": 100,
            },
        ]
        with wizard.dynamic_layered_progress(stages) as progress:
            progress.emergency_stop("Critical error")
        # Verify no exception raised

    def test_should_not_crash_when_dynamic_layered_progress_is_used_with_time_display_disabled(
        self, wizard
    ) -> None:
        """Test dynamic_layered_progress() without time display."""
        stages = [
            {
                "name": "step1",
                "type": "progress",
                "description": "Step 1",
                "total": 100,
            },
        ]
        with wizard.dynamic_layered_progress(stages, show_time=False) as progress:
            progress.update_layer("step1", 50)
            progress.complete_layer("step1")
        # Verify no exception raised


class TestErrorHandling:
    """Tests for error handling in wizard methods."""

    def test_should_handle_gracefully_when_panel_receives_none_as_content(
        self, wizard
    ) -> None:
        """Test panel() with invalid content type."""
        # Should handle gracefully
        wizard.panel(None)
        # Verify no exception raised

    def test_should_handle_gracefully_when_table_receives_invalid_data_structure(
        self, wizard
    ) -> None:
        """Test table() with invalid data structure."""
        # Should handle gracefully
        wizard.table([{"key": "value"}, "invalid"])
        # Verify no exception raised

    def test_should_handle_gracefully_when_json_receives_invalid_json_string(
        self, wizard
    ) -> None:
        """Test json() with invalid JSON."""
        # Should handle gracefully
        wizard.json("{invalid json}")
        # Verify no exception raised
