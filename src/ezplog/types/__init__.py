# ///////////////////////////////////////////////////////////////
# EZPL - Types Module
# Project: ezpl
# ///////////////////////////////////////////////////////////////

"""
Types module for Ezpl logging framework.

This module contains type definitions, enumerations, and protocols.
"""

from __future__ import annotations

# ///////////////////////////////////////////////////////////////
# IMPORTS
# ///////////////////////////////////////////////////////////////
# Local imports
from .aliases import (
    SUPPORTED_COMPRESSIONS,
    CompressionSpec,
    RetentionSpec,
    RotationSpec,
)
from .enums import (
    PATTERN_COLORS,
    LogLevel,
    Pattern,
    get_pattern_color,
    get_pattern_color_by_name,
)
from .protocols import LoggerProtocol, PrinterProtocol

# ///////////////////////////////////////////////////////////////
# PUBLIC API
# ///////////////////////////////////////////////////////////////

__all__ = [
    # Log level exports
    "LogLevel",
    # Pattern exports
    "Pattern",
    "PATTERN_COLORS",
    "get_pattern_color",
    "get_pattern_color_by_name",
    # Type alias exports
    "RotationSpec",
    "RetentionSpec",
    "CompressionSpec",
    "SUPPORTED_COMPRESSIONS",
    # Protocol exports
    "PrinterProtocol",
    "LoggerProtocol",
]
