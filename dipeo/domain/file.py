"""Backward compatibility re-export for file module.

This module maintains backward compatibility for imports during the migration
of file to integrations bounded context.

DEPRECATED: Use dipeo.domain.integrations instead.
"""

# Re-export value objects
from dipeo.domain.integrations.file_value_objects import (
    Checksum,
    FileExtension,
    FileSize,
)

# Create sub-module namespace for backward compatibility
class value_objects:
    Checksum = Checksum
    FileExtension = FileExtension
    FileSize = FileSize

__all__ = [
    "Checksum",
    "FileExtension",
    "FileSize",
    "value_objects",
]