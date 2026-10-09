# ///////////////////////////////////////////////////////////////
# EZPL - Demonstration script
# Project: ezpl
# ///////////////////////////////////////////////////////////////

"""
Demonstration script for testing Ezpl features.

This script demonstrates:
- Log levels
- Pattern methods
- Rich features (panels, tables, JSON)
- Progress bars
- Indentation
- Configuration
"""

from __future__ import annotations

# ///////////////////////////////////////////////////////////////
# IMPORTS
# ///////////////////////////////////////////////////////////////
# Standard library imports
import sys
import time
from pathlib import Path

# Add the parent directory to the path to import ezpl.
sys.path.insert(0, str(Path(__file__).parent.parent))

# Local imports
from ezpl import Ezpl

# ///////////////////////////////////////////////////////////////
# INITIALIZATION
# ///////////////////////////////////////////////////////////////

# Create a temporary log file for the demo.
log_file = Path("demo.log")

# Initialize Ezpl.
ezpl = Ezpl(log_file=log_file, log_level="DEBUG")
printer = ezpl.get_printer()
logger = ezpl.get_logger()

# ///////////////////////////////////////////////////////////////
# SECTION 1: LOG LEVELS
# ///////////////////////////////////////////////////////////////

print("\n" + "=" * 80)
print("SECTION 1: LOG LEVELS")
print("=" * 80 + "\n")

printer.debug("Debug message - for development")
printer.info("Information message - normal operation")
printer.success("Success message - operation completed")
printer.warning("Warning message - attention required")
printer.error("Error message - issue detected")
printer.critical("Critical message - severe error")

# Logs in the file.
logger.debug("Debug in file")
logger.info("Info in file")
logger.warning("Warning in file")
logger.error("Error in file")

# ///////////////////////////////////////////////////////////////
# SECTION 2: PATTERN METHODS
# ///////////////////////////////////////////////////////////////

print("\n" + "=" * 80)
print("SECTION 2: PATTERN METHODS")
print("=" * 80 + "\n")

printer.tip("Tip: use type hints to improve your code")
printer.system("Checking the system...")
printer.install("Installing the 'requests' dependency...")
printer.detect("Detecting Python 3.11.3")
printer.config("Configuration loaded from ~/.ezpl/config.json")
printer.deps("Checking dependencies: rich, loguru, click")

# ///////////////////////////////////////////////////////////////
# SECTION 3: RICH FEATURES - PANELS
# ///////////////////////////////////////////////////////////////

print("\n" + "=" * 80)
print("SECTION 3: RICH FEATURES - PANELS")
print("=" * 80 + "\n")

wizard = printer.wizard

# Simple panel
wizard.panel("Panel content", title="Simple panel", style="blue")

# Status panels
wizard.info_panel("Information", "This is an information message")
wizard.success_panel("Success", "Operation completed successfully!")
wizard.error_panel("Error", "An error occurred")
wizard.warning_panel("Warning", "Attention: check the configuration")

# Installation panel
wizard.installation_panel("Installation", "Installing ezpl...", status="in_progress")

# ///////////////////////////////////////////////////////////////
# SECTION 4: RICH FEATURES - TABLES
# ///////////////////////////////////////////////////////////////

print("\n" + "=" * 80)
print("SECTION 4: RICH FEATURES - TABLES")
print("=" * 80 + "\n")

# Simple table
data = [
    {"Name": "Alice", "Age": 30, "City": "Paris"},
    {"Name": "Bob", "Age": 25, "City": "Lyon"},
    {"Name": "Charlie", "Age": 35, "City": "Marseille"},
]
wizard.table(data, title="User list")

# Status table (title is the first parameter)
status_data = [
    {"Service": "API", "Status": "✅ Active", "Uptime": "99.9%"},
    {"Service": "DB", "Status": "✅ Active", "Uptime": "99.8%"},
    {"Service": "Cache", "Status": "⚠️ Degraded", "Uptime": "95.2%"},
]
wizard.status_table("Service status", status_data, status_column="Status")

# Dependency table (takes a dict, not a list)
deps_dict = {
    "requests": "2.31.0",
    "click": "8.1.0",
    "rich": "13.7.0",
}
wizard.dependency_table(deps_dict)

# Command table (no title parameter)
commands = [
    {"command": "python demo.py", "description": "Run the demo"},
    {"command": "pytest tests/", "description": "Run the tests"},
    {"command": "ezpl logs view", "description": "View logs"},
]
wizard.command_table(commands)

# ///////////////////////////////////////////////////////////////
# SECTION 5: RICH FEATURES - JSON
# ///////////////////////////////////////////////////////////////

print("\n" + "=" * 80)
print("SECTION 5: RICH FEATURES - JSON")
print("=" * 80 + "\n")

# Simple JSON
config_dict = {
    "app_name": "ezpl",
    "version": "1.0.0",
    "features": ["logging", "rich", "cli"],
    "settings": {
        "log_level": "INFO",
        "log_rotation": "10 MB",
        "log_retention": "7 days",
    },
}
wizard.json(config_dict, title="Configuration")

# JSON list
data_list = [
    {"id": 1, "name": "Item 1", "active": True},
    {"id": 2, "name": "Item 2", "active": False},
    {"id": 3, "name": "Item 3", "active": True},
]
wizard.json(data_list, title="Item list")

# ///////////////////////////////////////////////////////////////
# SECTION 6: PROGRESS BARS
# ///////////////////////////////////////////////////////////////

print("\n" + "=" * 80)
print("SECTION 6: PROGRESS BARS")
print("=" * 80 + "\n")

# Simple progress bar
print("Simple progress bar:")
with wizard.progress("Processing...", total=100) as (progress, task):
    for _i in range(100):
        progress.update(task, advance=1)
        time.sleep(0.01)

# Spinner
print("\nSpinner:")
with wizard.spinner("Loading...") as (progress, task):
    time.sleep(2)

# Download progress
print("\nDownload progress:")
with wizard.download_progress("Downloading file.zip") as (progress, task):
    for _i in range(0, 100, 10):
        progress.update(task, advance=10, total=100)
        time.sleep(0.1)

# File download progress
print("\nFile download progress:")
with wizard.file_download_progress("large_file.zip", 1024000) as (progress, task):
    for _i in range(0, 1024000, 102400):
        progress.update(task, advance=102400)
        time.sleep(0.1)

# Dependency progress
print("\nDependency progress:")
dependencies = ["requests", "click", "rich", "loguru"]
gen = wizard.dependency_progress(dependencies)
first_yield = gen.__enter__()
progress, task, dep = first_yield
progress.advance(task)
try:
    while True:
        progress, task, dep = next(gen.gen)
        progress.advance(task)
        time.sleep(0.1)
except (StopIteration, AttributeError):
    pass
gen.__exit__(None, None, None)

# Step progress
print("\nStep progress:")
steps = [("Init", "Initializing"), ("Process", "Processing"), ("Done", "Completed")]
with wizard.step_progress(steps) as (progress, task, steps_list):
    for _i in range(len(steps)):
        progress.advance(task)
        time.sleep(0.2)

# ///////////////////////////////////////////////////////////////
# SECTION 7: INDENTATION
# ///////////////////////////////////////////////////////////////

print("\n" + "=" * 80)
print("SECTION 7: INDENTATION")
print("=" * 80 + "\n")

printer.info("Message at level 0")
with ezpl.manage_indent():
    printer.info("Message at level 1")
    with ezpl.manage_indent():
        printer.info("Message at level 2")
        with ezpl.manage_indent():
            printer.info("Message at level 3")
    printer.info("Back to level 1")
printer.info("Back to level 0")

# ///////////////////////////////////////////////////////////////
# SECTION 8: CONFIGURATION
# ///////////////////////////////////////////////////////////////

print("\n" + "=" * 80)
print("SECTION 8: CONFIGURATION")
print("=" * 80 + "\n")

# Show the current configuration.
config = ezpl.get_config()
printer.info(f"Log level: {config.get('log-level')}")
printer.info(f"Printer level: {config.get('printer-level')}")
printer.info(f"Logger level: {config.get('file-logger-level')}")

# Change the configuration.
ezpl.configure(printer_level="WARNING")
printer.info("After configuration - this message should be displayed")
printer.warning("Warning message - should be displayed")

# Restore INFO.
ezpl.configure(printer_level="INFO")
printer.info("Back to INFO level")

# ///////////////////////////////////////////////////////////////
# SECTION 9: FILE LOGGING
# ///////////////////////////////////////////////////////////////

print("\n" + "=" * 80)
print("SECTION 9: FILE LOGGING")
print("=" * 80 + "\n")

logger.info("Information message in file")
logger.debug("Debug message in file")
logger.warning("Warning message in file")
logger.error("Error message in file")

# Add a separator.
ezpl.add_separator()

logger.info("Message after the separator")

# Show the log-file path.
printer.info(f"Log file: {ezpl.get_log_file()}")

# ///////////////////////////////////////////////////////////////
# SECTION 10: DYNAMIC LAYERED PROGRESS
# ///////////////////////////////////////////////////////////////

print("\n" + "=" * 80)
print("SECTION 10: DYNAMIC LAYERED PROGRESS")
print("=" * 80 + "\n")

stages = [
    {
        "name": "main",
        "type": "main",
        "description": "Main progress",
        "steps": ["Step 1", "Step 2", "Step 3"],
    },
    {
        "name": "download",
        "type": "download",
        "description": "Download",
        "total_size": 1024000,
        "filename": "file.zip",
    },
    {"name": "process", "type": "progress", "description": "Processing", "total": 100},
]

with wizard.dynamic_layered_progress(stages, show_time=True) as progress:
    # Update the main layer.
    progress.update_layer("main", 0, "Starting...")
    time.sleep(0.5)

    # Update the download.
    progress.update_layer("download", 512000, "Downloading...")
    time.sleep(0.5)

    # Update processing.
    progress.update_layer("process", 50, "Processing at 50%")
    time.sleep(0.5)

    # Complete the layers.
    progress.complete_layer("download")
    progress.complete_layer("process")
    progress.complete_layer("main")

# ///////////////////////////////////////////////////////////////
# END
# ///////////////////////////////////////////////////////////////

print("\n" + "=" * 80)
print("DEMONSTRATION COMPLETE")
print("=" * 80 + "\n")

printer.success("All examples completed successfully!")
printer.info(f"See the log file: {log_file}")
