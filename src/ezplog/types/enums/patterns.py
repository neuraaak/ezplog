# ///////////////////////////////////////////////////////////////
# EZPL - Pattern definitions
# Project: ezpl
# ///////////////////////////////////////////////////////////////

"""
Pattern definitions for Ezpl logging framework.

This module defines contextual patterns for enhanced console output with the format:
• PATTERN :: message
"""

from __future__ import annotations

# ///////////////////////////////////////////////////////////////
# IMPORTS
# ///////////////////////////////////////////////////////////////
# Standard library imports
from enum import Enum

# ///////////////////////////////////////////////////////////////
# CLASSES
# ///////////////////////////////////////////////////////////////


class Pattern(Enum):
    """
    Contextual patterns for console output.

    Patterns provide semantic meaning beyond log levels, allowing for
    more expressive and contextual logging.
    """

    # Main patterns
    TRACE = "TRACE"
    SUCCESS = "SUCCESS"
    ERROR = "ERROR"
    WARN = "WARN"
    TIP = "TIP"
    DEBUG = "DEBUG"
    INFO = "INFO"

    # System patterns
    SYSTEM = "SYSTEM"
    INSTALL = "INSTALL"
    DETECT = "DETECT"
    CONFIG = "CONFIG"
    DEPS = "DEPS"


# ///////////////////////////////////////////////////////////////
# VARIABLES
# ///////////////////////////////////////////////////////////////

# Color mapping for patterns (Rich color names)
PATTERN_COLORS: dict[Pattern, str] = {
    # Main patterns
    Pattern.TRACE: "dim cyan",  # ⚪ Trace (dimmed)
    Pattern.SUCCESS: "bright_green",  # 🟢 Success
    Pattern.ERROR: "bright_red",  # 🔴 Error
    Pattern.WARN: "bright_yellow",  # 🟡 Warning
    Pattern.TIP: "bright_magenta",  # 🟣 Tip
    Pattern.DEBUG: "dim white",  # ⚪ Debug (dimmed)
    Pattern.INFO: "bright_blue",  # 🔵 Info
    # System patterns
    Pattern.SYSTEM: "bright_blue",  # 🔵 System operations
    Pattern.INSTALL: "bright_green",  # 🟢 Installation
    Pattern.DETECT: "bright_blue",  # 🔵 Detection/Analysis
    Pattern.CONFIG: "bright_green",  # 🟢 Configuration
    Pattern.DEPS: "bright_cyan",  # 🔵 Dependencies
}

# ///////////////////////////////////////////////////////////////
# FUNCTIONS
# ///////////////////////////////////////////////////////////////


def get_pattern_color(pattern: Pattern) -> str:
    """
    Get the Rich color style for a pattern.

    Args:
        pattern: The pattern to get the color for

    Returns:
        Rich color style string
    """
    return PATTERN_COLORS.get(pattern, "white")


def get_pattern_color_by_name(pattern_name: str) -> str:
    """
    Get the Rich color style for a pattern by name.

    Args:
        pattern_name: The pattern name (case-insensitive)

    Returns:
        Rich color style string
    """
    try:
        pattern = Pattern[pattern_name.upper()]
        return get_pattern_color(pattern)
    except KeyError:
        return "white"


# ///////////////////////////////////////////////////////////////
# PUBLIC API
# ///////////////////////////////////////////////////////////////

__all__ = [
    "PATTERN_COLORS",
    "Pattern",
    "get_pattern_color",
    "get_pattern_color_by_name",
]
