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


# ============================================================================
# Unified Port Adapter (Backward Compatibility)
# ============================================================================


class UnifiedDiagramPortAdapter(DiagramFilePort, DiagramFormatPort, DiagramRepositoryPort):
    """Adapter that implements the original DiagramPort interface using segregated ports.

    This provides backward compatibility during the migration period.
    """

    def __init__(
        self,
        file_port: DiagramFilePort,
        format_port: DiagramFormatPort,
        repository_port: DiagramRepositoryPort,
        compiler: "DiagramCompiler",
    ):
        self.file_port = file_port
        self.format_port = format_port
        self.repository_port = repository_port
        self.compiler = compiler

    async def load_from_file(self, file_path: str) -> "DomainDiagram":
        return await self.file_port.load_from_file(file_path)

    def detect_format(self, content: str) -> "DiagramFormat":
        return self.format_port.detect_format(content)

    def serialize(self, diagram: "DomainDiagram", format_type: str) -> str:
        return self.format_port.serialize(diagram, format_type)

    def deserialize(
        self, content: str, format_type: str | None = None, diagram_path: str | None = None
    ) -> "DomainDiagram":
        return self.format_port.deserialize(content, format_type, diagram_path)

    def load_from_string(self, content: str, format_type: str | None = None) -> "DomainDiagram":
        return self.format_port.deserialize(content, format_type)

    async def create_diagram(
        self, name: str, diagram: "DomainDiagram", format_type: str = "native"
    ) -> str:
        return await self.repository_port.create(name, diagram, format_type)

    async def get_diagram(self, diagram_id: str) -> Optional["DomainDiagram"]:
        return await self.repository_port.get(diagram_id)

    async def update_diagram(self, diagram_id: str, diagram: "DomainDiagram") -> None:
        await self.repository_port.update(diagram_id, diagram)

    async def delete_diagram(self, diagram_id: str) -> None:
        await self.repository_port.delete(diagram_id)

    async def exists(self, diagram_id: str) -> bool:
        return await self.repository_port.exists(diagram_id)

    async def list_diagrams(self, format_type: str | None = None) -> list["DiagramInfo"]:
        return await self.repository_port.list(format_type)

    def compile(self, domain_diagram: "DomainDiagram") -> "ExecutableDiagram":
        return self.compiler.compile(domain_diagram)
