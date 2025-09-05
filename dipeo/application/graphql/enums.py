"""
Strawberry GraphQL enum definitions that map to the generated Python enums.
This file provides proper GraphQL enum value mappings for Strawberry.
"""

from enum import Enum

import strawberry

from dipeo.diagram_generated.enums import DiagramFormat as PythonDiagramFormat


@strawberry.enum
class DiagramFormat(Enum):
    """GraphQL enum for diagram formats with lowercase values."""

    native = "native"
    light = "light"
    readable = "readable"

    @classmethod
    def from_python_enum(cls, python_enum: PythonDiagramFormat) -> "DiagramFormat":
        """Convert from Python enum to GraphQL enum."""
        mapping = {
            PythonDiagramFormat.NATIVE: cls.native,
            PythonDiagramFormat.LIGHT: cls.light,
            PythonDiagramFormat.READABLE: cls.readable,
        }
        return mapping[python_enum]

    def to_python_enum(self) -> PythonDiagramFormat:
        """Convert from GraphQL enum to Python enum."""
        mapping = {
            DiagramFormat.native: PythonDiagramFormat.NATIVE,
            DiagramFormat.light: PythonDiagramFormat.LIGHT,
            DiagramFormat.readable: PythonDiagramFormat.READABLE,
        }
        return mapping[self]
