# ///////////////////////////////////////////////////////////////
# EZPL - Type aliases for loguru sink options
# Project: ezplog
# ///////////////////////////////////////////////////////////////

"""
Type aliases mirroring the value types loguru accepts for file sinks.

The previous `str | None` annotations were narrower than reality: values such
as `timedelta(hours=6)` for rotation or `10` for retention already worked at
runtime but failed type checking.
"""

from __future__ import annotations

# ///////////////////////////////////////////////////////////////
# IMPORTS
# ///////////////////////////////////////////////////////////////
# Standard library imports
from collections.abc import Callable
from datetime import time, timedelta

# ///////////////////////////////////////////////////////////////
# TYPE ALIASES
# ///////////////////////////////////////////////////////////////

RotationSpec = str | int | time | timedelta | Callable[..., bool] | None
"""Rotation trigger: size string, byte count, time of day, interval, or predicate."""

RetentionSpec = str | int | timedelta | Callable[..., None] | None
"""Retention policy: duration string, file count, timedelta, or cleanup callable."""

CompressionSpec = str | Callable[[str], None] | None
"""Compression format name, or a callable applied to the rotated file path."""

# ///////////////////////////////////////////////////////////////
# CONSTANTS
# ///////////////////////////////////////////////////////////////

SUPPORTED_COMPRESSIONS: frozenset[str] = frozenset(
    {"gz", "bz2", "xz", "lzma", "tar", "tar.gz", "tar.bz2", "tar.xz", "zip"}
)
"""Compression format names accepted by loguru."""

# ///////////////////////////////////////////////////////////////
# PUBLIC API
# ///////////////////////////////////////////////////////////////

__all__ = [
    "RotationSpec",
    "RetentionSpec",
    "CompressionSpec",
    "SUPPORTED_COMPRESSIONS",
]
