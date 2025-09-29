"""Segregated interfaces for diagram operations following Interface Segregation Principle.

This module splits the monolithic DiagramPort into focused, single-responsibility interfaces.
Part of Phase 3 refactoring to simplify architecture and improve maintainability.
"""

from typing import TYPE_CHECKING, Optional, Protocol

if TYPE_CHECKING:
    from dipeo.diagram_generated import DiagramFormat, DomainDiagram
    from dipeo.domain.base.storage_port import DiagramInfo
    from dipeo.domain.diagram.models.executable_diagram import ExecutableDiagram
    from dipeo.domain.diagram.ports import DiagramCompiler


# ============================================================================
# File Operations Port
# ============================================================================


class DiagramFilePort(Protocol):
    """Interface for diagram file I/O operations.

    Focused on reading and writing diagram files from/to the filesystem.
    """

    async def load_from_file(self, file_path: str) -> "DomainDiagram":
        """Load a diagram from a file path."""
        ...

    async def save_to_file(
        self, diagram: "DomainDiagram", file_path: str, format_type: str = "native"
    ) -> None:
        """Save a diagram to a file."""
        ...

    async def file_exists(self, file_path: str) -> bool:
        """Check if a diagram file exists."""
        ...

    async def delete_file(self, file_path: str) -> None:
        """Delete a diagram file."""
        ...


# ============================================================================
# Format Conversion Port
# ============================================================================


class DiagramFormatPort(Protocol):
    """Interface for diagram format detection and conversion.

    Handles serialization/deserialization between different formats.
    """

    def detect_format(self, content: str) -> "DiagramFormat":
        """Detect the format of diagram content."""
        ...

    def serialize(self, diagram: "DomainDiagram", format_type: str) -> str:
        """Serialize a diagram to a specific format."""
        ...

    def deserialize(
        self, content: str, format_type: str | None = None, diagram_path: str | None = None
    ) -> "DomainDiagram":
        """Deserialize string content to a domain diagram."""
        ...

    def convert_format(self, diagram: "DomainDiagram", from_format: str, to_format: str) -> str:
        """Convert a diagram from one format to another."""
        ...


# ============================================================================
# Repository Operations Port
# ============================================================================


class DiagramRepositoryPort(Protocol):
    """Interface for diagram CRUD and query operations.

    Manages diagram persistence and retrieval with unique IDs.
    """

    async def create(self, name: str, diagram: "DomainDiagram", format_type: str = "native") -> str:
        """Create a new diagram with a unique ID."""
        ...

    async def get(self, diagram_id: str) -> Optional["DomainDiagram"]:
        """Retrieve a diagram by its ID."""
        ...

    async def update(self, diagram_id: str, diagram: "DomainDiagram") -> None:
        """Update an existing diagram."""
        ...

    async def delete(self, diagram_id: str) -> None:
        """Delete a diagram from storage."""
        ...

    async def exists(self, diagram_id: str) -> bool:
        """Check if a diagram exists."""
        ...

    async def list(self, format_type: str | None = None) -> list["DiagramInfo"]:
        """List all diagrams, optionally filtered by format."""
        ...


# ============================================================================
# Compilation Port (Already exists, kept for reference)
# ============================================================================

# DiagramCompiler already exists in ports.py and is well-focused
