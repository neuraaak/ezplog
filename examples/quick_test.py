# ///////////////////////////////////////////////////////////////
# EZPL - Interactive quick test
# Project: ezpl
# ///////////////////////////////////////////////////////////////

"""
Interactive script for quickly testing Ezpl features.

Usage:
    python examples/quick_test.py
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
# FUNCTIONS
# ///////////////////////////////////////////////////////////////


def main():
    """Main entry point for interactive tests."""

    # Initialize Ezpl.
    log_file = Path("quick_test.log")
    ezpl = Ezpl(log_file=log_file, log_level="DEBUG")
    printer = ezpl.get_printer()
    logger = ezpl.get_logger()
    wizard = printer.wizard

    print("\n" + "=" * 80)
    print("EZPL - INTERACTIVE QUICK TEST")
    print("=" * 80)

    # Menu
    while True:
        print("\nAvailable options:")
        print("1. Test log levels")
        print("2. Test patterns")
        print("3. Test panels")
        print("4. Test tables")
        print("5. Test JSON")
        print("6. Test progress bars")
        print("7. Test indentation")
        print("8. Test file logging")
        print("9. Show configuration")
        print("0. Quit")

        choice = input("\nYour choice: ").strip()

        if choice == "0":
            break
        elif choice == "1":
            test_log_levels(printer)
        elif choice == "2":
            test_patterns(printer)
        elif choice == "3":
            test_panels(wizard)
        elif choice == "4":
            test_tables(wizard)
        elif choice == "5":
            test_json(wizard)
        elif choice == "6":
            test_progress_bars(wizard)
        elif choice == "7":
            test_indentation(ezpl, printer)
        elif choice == "8":
            test_file_logging(logger, ezpl)
        elif choice == "9":
            show_config(ezpl)
        else:
            print("Invalid choice!")

    print("\n✅ Tests completed!")
    print(f"See the log file: {log_file}")


def test_log_levels(printer):
    """Test log levels."""
    print("\n--- Log level test ---")
    printer.debug("Message DEBUG")
    printer.info("Message INFO")
    printer.success("Message SUCCESS")
    printer.warning("Message WARNING")
    printer.error("Message ERROR")
    printer.critical("Message CRITICAL")


def test_patterns(printer):
    """Test patterns."""
    print("\n--- Pattern test ---")
    printer.tip("Tip: use type hints")
    printer.system("System message")
    printer.install("Installation in progress")
    printer.detect("Detection completed")
    printer.config("Configuration loaded")
    printer.deps("Dependencies verified")


def test_panels(wizard):
    """Test panels."""
    print("\n--- Panel test ---")
    wizard.info_panel("Info", "Information message")
    wizard.success_panel("Success", "Operation completed successfully")
    wizard.error_panel("Error", "An error occurred")
    wizard.warning_panel("Warning", "Attention required")


def test_tables(wizard):
    """Test tables."""
    print("\n--- Table test ---")
    data = [
        {"Name": "Alice", "Age": 30},
        {"Name": "Bob", "Age": 25},
    ]
    wizard.table(data, title="Users")


def test_json(wizard):
    """Test JSON."""
    print("\n--- JSON test ---")
    data = {"app": "ezpl", "version": "1.0.0", "features": ["logging", "rich"]}
    wizard.json(data, title="Configuration")


def test_progress_bars(wizard):
    """Test progress bars."""
    print("\n--- Progress bar test ---")
    with wizard.progress("Processing...", total=50) as (progress, task):
        for _i in range(50):
            progress.update(task, advance=1)
            time.sleep(0.02)


def test_indentation(ezpl, printer):
    """Test indentation."""
    print("\n--- Indentation test ---")
    printer.info("Level 0")
    with ezpl.manage_indent():
        printer.info("Level 1")
        with ezpl.manage_indent():
            printer.info("Level 2")
        printer.info("Back to level 1")
    printer.info("Back to level 0")


def test_file_logging(logger, ezpl):
    """Test file logging."""
    print("\n--- File logging test ---")
    logger.info("INFO message in file")
    logger.debug("DEBUG message in file")
    logger.warning("WARNING message in file")
    logger.error("ERROR message in file")
    print(f"Log file: {ezpl.get_log_file()}")


def show_config(ezpl):
    """Show the current configuration."""
    print("\n--- Current configuration ---")
    config = ezpl.get_config()
    print(f"Log level: {config.get('log-level')}")
    print(f"Printer level: {config.get('printer-level')}")
    print(f"Logger level: {config.get('file-logger-level')}")
    print(f"Log file: {ezpl.get_log_file()}")


if __name__ == "__main__":
    main()
