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
        """Load a diagram from a file path.

        Args:
            file_path: Path to the diagram file

        Returns:
            DomainDiagram: Loaded diagram

        Raises:
            StorageError: If file cannot be loaded
        """
        ...

    async def save_to_file(
        self, diagram: "DomainDiagram", file_path: str, format_type: str = "native"
    ) -> None:
        """Save a diagram to a file.

        Args:
            diagram: Diagram to save
            file_path: Target file path
            format_type: Format to save as (native, light, readable)
        """
        ...

    async def file_exists(self, file_path: str) -> bool:
        """Check if a diagram file exists.

        Args:
            file_path: Path to check

        Returns:
            bool: True if file exists
        """
        ...

    async def delete_file(self, file_path: str) -> None:
        """Delete a diagram file.

        Args:
            file_path: Path to delete

        Raises:
            StorageError: If file cannot be deleted
        """
        ...


# ============================================================================
# Format Conversion Port
# ============================================================================


class DiagramFormatPort(Protocol):
    """Interface for diagram format detection and conversion.

    Handles serialization/deserialization between different formats.
    """

    def detect_format(self, content: str) -> "DiagramFormat":
        """Detect the format of diagram content.

        Args:
            content: String content to analyze

        Returns:
            DiagramFormat: Detected format
        """
        ...

    def serialize(self, diagram: "DomainDiagram", format_type: str) -> str:
        """Serialize a diagram to a specific format.

        Args:
            diagram: Diagram to serialize
            format_type: Target format (native, light, readable)

        Returns:
            str: Serialized diagram content
        """
        ...

    def deserialize(
        self, content: str, format_type: str | None = None, diagram_path: str | None = None
    ) -> "DomainDiagram":
        """Deserialize string content to a domain diagram.

        Args:
            content: String content to deserialize
            format_type: Optional format hint
            diagram_path: Optional path for context (e.g., prompt resolution)

        Returns:
            DomainDiagram: Deserialized diagram
        """
        ...

    def convert_format(self, diagram: "DomainDiagram", from_format: str, to_format: str) -> str:
        """Convert a diagram from one format to another.

        Args:
            diagram: Diagram to convert
            from_format: Source format
            to_format: Target format

        Returns:
            str: Converted diagram content
        """
        ...


# ============================================================================
# Repository Operations Port
# ============================================================================


class DiagramRepositoryPort(Protocol):
    """Interface for diagram CRUD and query operations.

    Manages diagram persistence and retrieval with unique IDs.
    """

    async def create(self, name: str, diagram: "DomainDiagram", format_type: str = "native") -> str:
        """Create a new diagram with a unique ID.

        Args:
            name: Base name for the diagram
            diagram: Diagram to store
            format_type: Storage format

        Returns:
            str: Unique diagram ID
        """
        ...

    async def get(self, diagram_id: str) -> Optional["DomainDiagram"]:
        """Retrieve a diagram by its ID.

        Args:
            diagram_id: Unique diagram identifier

        Returns:
            DomainDiagram if found, None otherwise
        """
        ...

    async def update(self, diagram_id: str, diagram: "DomainDiagram") -> None:
        """Update an existing diagram.

        Args:
            diagram_id: ID of diagram to update
            diagram: Updated diagram content

        Raises:
            FileNotFoundError: If diagram doesn't exist
        """
        ...

    async def delete(self, diagram_id: str) -> None:
        """Delete a diagram from storage.

        Args:
            diagram_id: ID of diagram to delete

        Raises:
            StorageError: If diagram cannot be deleted
        """
        ...

    async def exists(self, diagram_id: str) -> bool:
        """Check if a diagram exists.

        Args:
            diagram_id: ID to check

        Returns:
            bool: True if diagram exists
        """
        ...

    async def list(self, format_type: str | None = None) -> list["DiagramInfo"]:
        """List all diagrams, optionally filtered by format.

        Args:
            format_type: Optional format filter

        Returns:
            list[DiagramInfo]: List of diagram metadata
        """
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
        """Initialize the adapter with segregated ports.

        Args:
            file_port: Port for file operations
            format_port: Port for format operations
            repository_port: Port for repository operations
            compiler: Diagram compiler
        """
        self.file_port = file_port
        self.format_port = format_port
        self.repository_port = repository_port
        self.compiler = compiler

    # File operations delegation
    async def load_from_file(self, file_path: str) -> "DomainDiagram":
        return await self.file_port.load_from_file(file_path)

    # Format operations delegation
    def detect_format(self, content: str) -> "DiagramFormat":
        return self.format_port.detect_format(content)

    def serialize(self, diagram: "DomainDiagram", format_type: str) -> str:
        return self.format_port.serialize(diagram, format_type)

    def deserialize(
        self, content: str, format_type: str | None = None, diagram_path: str | None = None
    ) -> "DomainDiagram":
        return self.format_port.deserialize(content, format_type, diagram_path)

    def load_from_string(self, content: str, format_type: str | None = None) -> "DomainDiagram":
        """Load a diagram from string content (backward compatibility)."""
        return self.format_port.deserialize(content, format_type)

    # Repository operations delegation
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

    # Compilation
    def compile(self, domain_diagram: "DomainDiagram") -> "ExecutableDiagram":
        return self.compiler.compile(domain_diagram)
