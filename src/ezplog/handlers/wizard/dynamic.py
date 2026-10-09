# ///////////////////////////////////////////////////////////////
# EZPL - Wizard Dynamic Progress Mixin
# Project: ezpl
# ///////////////////////////////////////////////////////////////

"""
Dynamic progress methods mixin for Rich Wizard.

This module provides dynamic layered progress bar functionality with
layers that can appear, progress, and disappear automatically.
"""

from __future__ import annotations

# ///////////////////////////////////////////////////////////////
# IMPORTS
# ///////////////////////////////////////////////////////////////
# Standard library imports
import threading
import time
from collections.abc import Generator
from contextlib import contextmanager
from typing import Any, TypedDict

# Third-party imports
from rich.console import Console
from rich.progress import (
    BarColumn,
    DownloadColumn,
    Progress,
    ProgressColumn,
    SpinnerColumn,
    TaskID,
    TaskProgressColumn,
    TextColumn,
    TimeElapsedColumn,
    TimeRemainingColumn,
    TransferSpeedColumn,
)
from rich.text import Text

# ///////////////////////////////////////////////////////////////
# TYPES
# ///////////////////////////////////////////////////////////////


class _StageConfigRequired(TypedDict):
    """Required fields for stage configuration."""

    name: str
    type: str  # "progress", "steps", "spinner", "download", "main"


class StageConfig(_StageConfigRequired, total=False):
    """Configuration for a DynamicLayeredProgress stage.

    Required fields:
        name: Layer name/identifier.
        type: Layer type ("progress", "steps", "spinner", "download", "main").

    Optional fields:
        description: Display description for the layer.
        style: Rich style string.
        total: Total items (for "progress" or "download" type).
        steps: List of step names (for "steps" or "main" type).
        total_size: Total size in bytes (for "download" type).
        filename: Filename (for "download" type).
    """

    description: str
    style: str
    total: int
    steps: list[str]
    total_size: int
    filename: str


# ///////////////////////////////////////////////////////////////
# CLASSES
# ///////////////////////////////////////////////////////////////


class _ConditionalStatusColumn(TextColumn):
    """A text column that only shows status if the field exists."""

    def __init__(self):
        super().__init__("")  # Empty text format, we override render

    def render(self, task):
        """
        Render the status field if it exists in the task.

        Args:
            task: The task object to render

        Returns:
            Text object containing the status or empty text
        """
        if hasattr(task, "fields") and "status" in task.fields:
            return Text(str(task.fields["status"]), style="dim")
        return Text("")


class _ConditionalDetailsColumn(TextColumn):
    """A text column that only shows details if the field exists."""

    def __init__(self):
        super().__init__("")  # Empty text format, we override render

    def render(self, task):
        """
        Render the details field if it exists in the task.

        Args:
            task: The task object to render

        Returns:
            Text object containing the details or empty text
        """
        if hasattr(task, "fields") and "details" in task.fields:
            return Text(str(task.fields["details"]), style="dim")
        return Text("")


class DynamicLayeredProgress:
    """
    Manages a dynamic layered progress bar with disappearing layers.

    This class provides a progress bar system where layers can appear,
    progress, and disappear based on the current state of operations.
    """

    def __init__(
        self,
        console: Console,
        progress_prefix: str,
        stages: list[StageConfig],
        show_time: bool = True,
    ) -> None:
        """
        Initialize the dynamic layered progress bar.

        Args:
            console: Rich Console instance
            progress_prefix: Prefix string for progress bars
            stages: List of stage configurations
            show_time: Whether to show elapsed and remaining time
        """
        self._console = console
        self._progress_prefix = progress_prefix
        self._stages = stages
        self._show_time = show_time
        self._progress: Progress | None = None
        self._task_ids: dict[str, TaskID] = {}
        self._active_layers: list[TaskID] = []
        self._completed_layers: list[TaskID] = []
        self._layer_metadata: dict[
            TaskID, dict[str, Any]
        ] = {}  # Store additional layer info
        self._emergency_stopped = False
        self._emergency_message: str | None = None
        self._lock = threading.Lock()

        # Hierarchy attributes (initialized in _setup_hierarchy)
        self._has_main_layer: bool = False
        self._main_layer_name: str | None = None
        self._sub_layers: list[StageConfig] = []

        # Detect main layer and setup hierarchy
        self._setup_hierarchy()

    def _setup_hierarchy(self) -> None:
        """Setup layer hierarchy and detect main layer."""
        self._has_main_layer = False
        self._main_layer_name = None
        self._sub_layers = []

        # Detect main layer
        for stage in self._stages:
            if stage.get("type") == "main":
                self._has_main_layer = True
                self._main_layer_name = stage.get("name", "main")
                break

        # If main layer found, setup sub-layers
        if self._has_main_layer:
            self._sub_layers = [
                stage for stage in self._stages if stage.get("type") != "main"
            ]
            # Auto-configure main layer steps if not provided
            for stage in self._stages:
                if stage.get("type") == "main" and "steps" not in stage:
                    stage["steps"] = [
                        s.get("name", f"Step {i + 1}")
                        for i, s in enumerate(self._sub_layers)
                    ]

    def _create_progress_bar(self) -> Progress:
        """Create the Rich Progress instance with proper columns."""
        # Build columns for the main progress bar
        columns: list[ProgressColumn] = [
            TextColumn(self._progress_prefix),  # Ezpl prefix
            SpinnerColumn(),
            TextColumn("[bold blue]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            _ConditionalDetailsColumn(),  # Conditional details column
            _ConditionalStatusColumn(),  # Conditional status column
        ]

        # Check if we have any download layers to add download columns
        has_download = any(stage.get("type") == "download" for stage in self._stages)
        if has_download:
            columns.extend(
                [
                    DownloadColumn(),  # Download info column
                    TransferSpeedColumn(),  # Transfer speed column
                ]
            )

        if self._show_time:
            columns.extend(
                [
                    TimeElapsedColumn(),
                    TimeRemainingColumn(),
                ]
            )

        return Progress(*columns, console=self._console)

    def _create_layer(self, layer_config: StageConfig) -> int:
        """Create a new layer in the progress bar.

        Args:
            layer_config: Layer configuration dictionary

        Returns:
            Task ID of the created layer
        """
        layer_name = layer_config.get("name", f"Layer_{len(self._task_ids)}")
        layer_type = layer_config.get("type", "progress")
        layer_desc = layer_config.get("description", layer_name)
        layer_style = layer_config.get("style", "default")

        # Determine layer prefix and styling based on hierarchy
        if self._has_main_layer and layer_type == "main":
            # Main layer: bold and prominent
            layer_style = "bold " + layer_style if layer_style != "default" else "bold"
        elif self._has_main_layer and layer_type != "main":
            # Sub-layer: add indentation and use softer colors
            layer_desc = f"  ├─ {layer_desc}"

        if not self._progress:
            return -1

        if layer_type == "steps":
            # Handle step-based layer
            steps = layer_config.get("steps", [])
            steps_total = len(steps)
            task_id = self._progress.add_task(
                f"[{layer_style}]{layer_desc}",
                total=steps_total,
                steps=steps,  # Store steps for later use
                details="",  # Initialize details field
            )
        elif layer_type == "spinner":
            # Handle spinner layer (indeterminate progress)
            task_id = self._progress.add_task(
                f"[{layer_style}]{layer_desc}",
                total=None,  # Indeterminate
                details="",  # Initialize details field
            )
        elif layer_type == "download":
            # Handle download layer with speed and size info
            total_size = layer_config.get("total_size", 100)
            filename = layer_config.get("filename", "")
            task_id = self._progress.add_task(
                f"[{layer_style}]{layer_desc}",
                total=total_size,
                details="",  # Initialize details field
                filename=filename,  # Store filename for download info
            )
        elif layer_type == "main":
            # Handle main layer (special case)
            steps = layer_config.get("steps", [])
            main_total = len(steps)
            task_id = self._progress.add_task(
                f"[{layer_style}]{layer_desc}",
                total=main_total,
                steps=steps,  # Store steps for later use
                details="",  # Initialize details field
            )
        else:
            # Handle regular progress layer
            progress_total: int | None = layer_config.get("total")
            task_id = self._progress.add_task(
                f"[{layer_style}]{layer_desc}",
                total=progress_total,
                details="",  # Initialize details field
            )

        # Store layer metadata
        self._layer_metadata[task_id] = {
            "name": layer_name,
            "type": layer_type,
            "config": layer_config,
            "is_main": layer_type == "main",
            "is_sub": self._has_main_layer and layer_type != "main",
        }

        self._active_layers.append(task_id)
        self._task_ids[layer_name] = task_id
        return task_id

    def update_layer(self, layer_name: str, progress: int, details: str = "") -> None:
        """Update a specific layer's progress.

        Args:
            layer_name: Name of the layer to update
            progress: Progress value (0-100 or step index)
            details: Additional details to display
        """
        with self._lock:
            if not self._progress:
                return

            task_id = self._task_ids.get(layer_name)
            if task_id is None:
                return

            metadata = self._layer_metadata.get(task_id)
            if metadata is None:
                return

            self._update_layer_unsafe(task_id, metadata, progress, details)

    def _update_layer_unsafe(
        self,
        task_id: TaskID,
        metadata: dict[str, Any],
        progress: int,
        details: str,
    ) -> None:
        """Update layer without acquiring lock (caller must hold lock).

        Args:
            task_id: Task ID to update
            metadata: Layer metadata
            progress: Progress value
            details: Additional details
        """
        if not self._progress:
            return

        # Update the layer based on its type
        if metadata["type"] == "steps":
            # Handle step-based layer
            task = self._get_task(task_id)
            if task is None:
                return
            steps = getattr(task, "fields", {}).get(
                "steps", metadata["config"].get("steps", [])
            )

            if steps and progress < len(steps):
                current_step = steps[progress]
                step_progress = f"Step {progress + 1}/{len(steps)}: {current_step}"

                self._progress.update(
                    task_id,
                    completed=progress,
                    description=f"{task.description} - {step_progress}",
                    details=details,
                )
            else:
                self._progress.update(task_id, completed=progress, details=details)
        elif metadata["type"] == "spinner":
            # Handle spinner layer - update details message
            self._progress.update(
                task_id,
                details=details,  # Use details consistently
            )
        elif metadata["type"] == "download":
            # Handle download layer - update progress and details
            self._progress.update(task_id, completed=progress, details=details)
        else:
            # Handle regular progress layer
            self._progress.update(task_id, completed=progress, details=details)

    def complete_layer(self, layer_name: str) -> None:
        """Mark a layer as completed and animate its success.

        Args:
            layer_name: Name of the layer to complete
        """
        with self._lock:
            if not self._progress:
                return

            task_id = self._task_ids.get(layer_name)
            if task_id is None:
                return

            # Mark as completed based on layer type
            metadata = self._layer_metadata.get(task_id)
            if metadata is None:
                return

            if metadata["type"] == "steps":
                steps = metadata["config"].get("steps", [])
                self._progress.update(task_id, completed=len(steps))
            elif metadata["type"] == "spinner":
                # For spinners, just mark as completed (no progress to update)
                pass
            else:
                total = metadata["config"].get("total", 100)
                self._progress.update(task_id, completed=total)

            # Don't remove main layer - it stays for reference
            if metadata.get("is_main", False):
                # Just mark as completed but keep it visible
                self._completed_layers.append(task_id)
                return

            # Remove the layer (only for sub-layers)
            self._completed_layers.append(task_id)
            metadata["state"] = "completed"

            # Animate success for this specific layer
            self._animate_layer_success(task_id)

            # Update main layer progress if it exists
            if self._has_main_layer:
                self._update_main_layer_progress()

    @staticmethod
    def _clean_description(description: str) -> str:
        """Remove status icons from a task description.

        Args:
            description: The task description string

        Returns:
            Cleaned description without status icons
        """
        for icon in ("❌ ", "⚠️ ", "✅ "):
            description = description.replace(icon, "")
        return description

    def _get_task(self, task_id: TaskID) -> Any | None:
        """Safely get a task from the progress bar.

        Args:
            task_id: Task ID to retrieve

        Returns:
            The task object, or None if not found
        """
        if not self._progress:
            return None
        tasks = getattr(self._progress, "_tasks", {})
        return tasks.get(task_id)

    def _has_task(self, task_id: TaskID) -> bool:
        """Check if a task exists in the progress bar.

        Args:
            task_id: Task ID to check

        Returns:
            True if the task exists
        """
        return self._get_task(task_id) is not None

    def _animate_layer_success(self, task_id: TaskID) -> None:
        """Animate success for a specific layer and then remove it.

        Args:
            task_id: Task ID to animate
        """
        if not self._progress:
            return

        # Flash green 2 times
        for flash in range(2):
            task = self._get_task(task_id)
            if task is not None:
                clean_description = self._clean_description(str(task.description))

                if flash % 2 == 0:  # Green flash
                    success_description = f"[bold green on green]{clean_description}[/]"
                else:  # Normal green
                    success_description = f"[bold green]{clean_description}[/]"

                self._progress.update(
                    task_id,
                    description=success_description,
                )

            time.sleep(0.1)  # Quick flash

        # Fade out by updating with dim style
        task = self._get_task(task_id)
        if task is not None:
            clean_description = self._clean_description(str(task.description))
            faded_description = f"[dim]{clean_description}[/]"
            self._progress.update(task_id, description=faded_description)
            time.sleep(0.3)  # Brief fade out

        # Remove the layer after animation
        if self._has_task(task_id):
            self._progress.remove_task(task_id)
            if task_id in self._active_layers:
                self._active_layers.remove(task_id)
            # Remove from task_ids dict
            for name, tid in list(self._task_ids.items()):
                if tid == task_id:
                    del self._task_ids[name]
                    break

    def _update_main_layer_progress(self) -> None:
        """Update main layer progress based on completed sub-layers."""
        if not self._has_main_layer or not self._main_layer_name:
            return

        if not self._progress:
            return

        # Find main layer task
        main_task_id: TaskID | None = None
        for tid, metadata in self._layer_metadata.items():
            if metadata.get("is_main", False):
                main_task_id = tid
                break

        if main_task_id is None:
            return

        # Calculate progress based on completed sub-layers only (exclude main layer)
        completed_sub_layers = sum(
            1
            for tid in self._completed_layers
            if not self._layer_metadata.get(tid, {}).get("is_main", False)
        )

        # Update main layer
        self._progress.update(main_task_id, completed=completed_sub_layers)

    def handle_error(self, layer_name: str, error: str) -> None:
        """Handle errors in a specific layer.

        Args:
            layer_name: Name of the layer with error
            error: Error message to display
        """
        with self._lock:
            if not self._progress:
                return

            task_id = self._task_ids.get(layer_name)
            if task_id is None:
                return

            # Update with error styling using Rich Text objects
            task = self._get_task(task_id)
            if task is not None:
                error_description = f"[red]❌ {task.description}[/]"
                error_details = f"[red]Error: {error}[/]"

                self._progress.update(
                    task_id,
                    description=error_description,
                    details=error_details,
                )

    def emergency_stop(self, error_message: str = "Critical error occurred") -> None:
        """Emergency stop all layers with animated failure effects.

        Args:
            error_message: The error message to display
        """
        with self._lock:
            if not self._progress:
                return

            # Create failure animation sequence: flash red 3 times
            for flash in range(3):
                # Apply flash effect to all active layers
                for task_id in list(self._active_layers):
                    task = self._get_task(task_id)
                    if task is not None:
                        clean_description = self._clean_description(
                            str(task.description)
                        )

                        if flash % 2 == 0:  # Red flash
                            error_description = (
                                f"[bold red on red]{clean_description}[/]"
                            )
                            error_details = f"[red on red]Stopped: {error_message}[/]"
                        else:  # Normal red
                            error_description = f"[bold red]{clean_description}[/]"
                            error_details = f"[red]Stopped: {error_message}[/]"

                        self._progress.update(
                            task_id,
                            description=error_description,
                            details=error_details,
                        )

                # Brief pause for flash effect
                time.sleep(0.15)

            # Final state: settle on clean error display
            for task_id in list(self._active_layers):
                task = self._get_task(task_id)
                if task is not None:
                    clean_description = self._clean_description(str(task.description))
                    error_description = f"[bold red]{clean_description}[/]"
                    error_details = f"[red]Stopped: {error_message}[/]"

                    self._progress.update(
                        task_id,
                        description=error_description,
                        details=error_details,
                    )

            # Stop the progress bar to freeze the display
            self._progress.stop()

            # Mark as emergency stopped
            self._emergency_stopped = True
            self._emergency_message = error_message

    def is_emergency_stopped(self) -> bool:
        """Check if the progress bar was emergency stopped.

        Returns:
            True if emergency stopped, False otherwise
        """
        return self._emergency_stopped

    def get_emergency_message(self) -> str | None:
        """Get the emergency stop message.

        Returns:
            The emergency message if stopped, None otherwise
        """
        return self._emergency_message

    def start(self) -> None:
        """Start the progress bar and create initial layers."""
        self._progress = self._create_progress_bar()
        self._progress.start()

        # Create layers in order: main layer first, then sub-layers
        if self._has_main_layer:
            # Create main layer first
            main_stage = next(
                (stage for stage in self._stages if stage.get("type") == "main"), None
            )
            if main_stage:
                self._create_layer(main_stage)

            # Then create sub-layers
            for stage in self._stages:
                if stage.get("type") != "main":
                    self._create_layer(stage)
        else:
            # No main layer, create all layers in order
            for stage in self._stages:
                self._create_layer(stage)

    def stop(self, success: bool = True, show_success_animation: bool = True) -> None:
        """Stop the progress bar with appropriate animations.

        Args:
            success: Whether this stop represents a successful completion
            show_success_animation: Whether to show success animations
        """
        if not self._progress:
            return

        if success and show_success_animation:
            # SUCCESS CASE: Final cleanup for any remaining layers
            time.sleep(0.5)
        elif not success:
            # ERROR/WARNING CASE: Freeze current state
            for task_id in list(self._active_layers):
                task = self._get_task(task_id)
                if task is not None:
                    clean_description = self._clean_description(str(task.description))
                    error_description = f"[bold orange]{clean_description}[/]"

                    self._progress.update(
                        task_id,
                        description=error_description,
                    )

        # Stop the underlying Rich progress
        self._progress.stop()


class DynamicProgressMixin:
    """
    Mixin providing dynamic layered progress bar methods for RichWizard.

    This mixin adds dynamic progress functionality with layers that can
    appear, progress, and disappear automatically.
    """

    # Type hints for attributes provided by RichWizard
    _console: Console
    _progress_prefix: str

    # ///////////////////////////////////////////////////////////////
    # DYNAMIC PROGRESS METHODS
    # ///////////////////////////////////////////////////////////////

    @contextmanager
    def dynamic_layered_progress(
        self,
        stages: list[StageConfig],
        show_time: bool = True,
    ) -> Generator[DynamicLayeredProgress]:
        """
        Create a dynamic layered progress bar context manager.

        Args:
            stages: List of stage configurations, each containing:
                - 'name': Layer name/identifier
                - 'type': Layer type ('progress', 'steps', 'spinner', 'download', 'main')
                - 'description': Display description for the layer
                - 'style': Rich style string (optional)
                - 'total': Total items (for 'progress' or 'download' type)
                - 'steps': List of step names (for 'steps' or 'main' type)
                - 'total_size': Total size in bytes (for 'download' type)
                - 'filename': Filename (for 'download' type)
            show_time: Whether to show elapsed and remaining time

        Yields:
            DynamicLayeredProgress instance with methods:
            - update_layer(name, progress, details): Update a layer's progress
            - complete_layer(name): Mark a layer as completed
            - handle_error(name, error): Handle errors in a layer
            - emergency_stop(message): Emergency stop all layers

        Example:
            >>> stages = [
            ...     {"name": "main", "type": "main", "description": "Overall Progress"},
            ...     {"name": "step1", "type": "progress", "description": "Step 1", "total": 100},
            ...     {"name": "step2", "type": "steps", "description": "Step 2", "steps": ["A", "B", "C"]},
            ... ]
            >>> with printer.wizard.dynamic_layered_progress(stages) as progress:
            ...     progress.update_layer("step1", 50, "Processing...")
            ...     progress.complete_layer("step1")
            ...     progress.update_layer("step2", 1, "Step B")
            ...     progress.complete_layer("step2")
        """
        progress_bar = DynamicLayeredProgress(
            self._console, self._progress_prefix, stages, show_time
        )

        try:
            progress_bar.start()
            yield progress_bar
        except BaseException:
            if not progress_bar.is_emergency_stopped():
                progress_bar.stop(success=False, show_success_animation=False)
            raise
        else:
            if not progress_bar.is_emergency_stopped():
                progress_bar.stop(success=True, show_success_animation=True)
        finally:
            if progress_bar.is_emergency_stopped():
                emergency_msg = progress_bar.get_emergency_message()
                if emergency_msg:
                    self._console.print(
                        f"\n[bold red]🚨 EMERGENCY STOP: {emergency_msg}[/bold red]"
                    )


# ///////////////////////////////////////////////////////////////
# PUBLIC API
# ///////////////////////////////////////////////////////////////

__all__ = [
    "DynamicLayeredProgress",
    "DynamicProgressMixin",
    "StageConfig",
]
