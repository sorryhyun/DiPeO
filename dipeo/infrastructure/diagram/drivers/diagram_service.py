"""Main diagram service - single source of truth for all diagram operations."""

import asyncio
from pathlib import Path
from typing import TYPE_CHECKING, Optional

from dipeo.diagram_generated import DiagramFormat, DomainDiagram
from dipeo.domain.base import StorageError
from dipeo.domain.base.mixins import InitializationMixin, LoggingMixin
from dipeo.domain.base.storage_port import DiagramInfo, FileSystemPort
from dipeo.domain.diagram.models.executable_diagram import ExecutableDiagram
from dipeo.domain.diagram.services import DiagramFormatDetector

if TYPE_CHECKING:
    from dipeo.domain.diagram.ports import DiagramCompiler, DiagramStorageSerializer


class DiagramService(LoggingMixin, InitializationMixin):
    """Single source of truth for all diagram operations.

    This service provides a unified interface by composing segregated ports:
    - File operations (DiagramFilePort)
    - Format operations (DiagramFormatPort)
    - Repository operations (DiagramRepositoryPort)
    - Compilation (DiagramCompiler)

    The service delegates to focused, single-responsibility adapters
    while maintaining backward compatibility with the old DiagramPort interface.
    """

    def __init__(
        self,
        filesystem: FileSystemPort,
        base_path: str | Path,
        converter: "DiagramStorageSerializer | None" = None,
        compiler: "DiagramCompiler | None" = None,
    ):
        # Initialize tracking from InitializationMixin
        self._initialized = False
        self._initialization_lock = asyncio.Lock()

        self.filesystem = filesystem
        self.base_path = Path(base_path)

        # Use V2 adapter if provided, otherwise use default
        if converter is None:
            from dipeo.infrastructure.diagram.adapters import UnifiedSerializerAdapter

            self.converter = UnifiedSerializerAdapter()
        else:
            self.converter = converter

        if compiler is None:
            from dipeo.infrastructure.diagram.adapters import StandardCompilerAdapter

            self.compiler = StandardCompilerAdapter(use_interface_based=True)
        else:
            self.compiler = compiler

        # Import segregated adapters
        from dipeo.infrastructure.diagram.drivers.segregated_adapters import (
            FileAdapter,
            FormatAdapter,
            RepositoryAdapter,
        )

        # Create segregated adapters
        self.format_port = FormatAdapter(self.converter)
        self.file_port = FileAdapter(filesystem, base_path, self.format_port)
        self.repository_port = RepositoryAdapter(filesystem, base_path, self.format_port)

        self.format_detector = DiagramFormatDetector()

    async def initialize(self) -> None:
        """Initialize the diagram service and its dependencies."""
        try:
            self.filesystem.mkdir(self.base_path, parents=True)
        except Exception as e:
            raise StorageError(f"Failed to initialize diagram storage: {e}") from e

        # Initialize adapters if they have initialize method
        if hasattr(self.converter, "initialize"):
            await self.converter.initialize()
        if hasattr(self.compiler, "initialize"):
            await self.compiler.initialize()

    # ============================================================================
    # Format Operations (delegated to FormatAdapter)
    # ============================================================================

    def detect_format(self, content: str) -> DiagramFormat:
        """Detect the format of diagram content."""
        return self.format_port.detect_format(content)

    def serialize(self, diagram: DomainDiagram, format_type: str) -> str:
        """Serialize a DomainDiagram to string."""
        return self.format_port.serialize(diagram, format_type)

    def deserialize(
        self, content: str, format_type: str | None = None, diagram_path: str | None = None
    ) -> DomainDiagram:
        """Deserialize string content to DomainDiagram."""
        return self.format_port.deserialize(content, format_type, diagram_path)

    def load_from_string(self, content: str, format_type: str | None = None) -> DomainDiagram:
        """Load a diagram from string content (backward compatibility)."""
        return self.format_port.deserialize(content, format_type)

    # ============================================================================
    # File Operations (delegated to FileAdapter)
    # ============================================================================

    async def load_from_file(self, file_path: str) -> DomainDiagram:
        """Load a diagram from a file path."""
        if not self._initialized:
            await self.initialize()
        return await self.file_port.load_from_file(file_path)

    # ============================================================================
    # Repository Operations (delegated to RepositoryAdapter)
    # ============================================================================

    async def create_diagram(
        self, name: str, diagram: DomainDiagram, format_type: str = "native"
    ) -> str:
        """Create a new diagram with a unique ID."""
        if not self._initialized:
            await self.initialize()
        return await self.repository_port.create(name, diagram, format_type)

    async def get_diagram(self, diagram_id: str) -> Optional[DomainDiagram]:
        """Get a diagram by its ID."""
        if not self._initialized:
            await self.initialize()
        return await self.repository_port.get(diagram_id)

    async def update_diagram(self, diagram_id: str, diagram: DomainDiagram) -> None:
        """Update an existing diagram."""
        if not self._initialized:
            await self.initialize()
        await self.repository_port.update(diagram_id, diagram)

    async def delete_diagram(self, diagram_id: str) -> None:
        """Delete a diagram from storage."""
        if not self._initialized:
            await self.initialize()
        await self.repository_port.delete(diagram_id)

    async def exists(self, diagram_id: str) -> bool:
        """Check if a diagram exists."""
        if not self._initialized:
            await self.initialize()
        return await self.repository_port.exists(diagram_id)

    async def list_diagrams(self, format_type: str | None = None) -> list[DiagramInfo]:
        """List all diagrams, optionally filtered by format."""
        if not self._initialized:
            await self.initialize()
        return await self.repository_port.list(format_type)

    # ============================================================================
    # Compilation Operations
    # ============================================================================

    def compile(self, domain_diagram: DomainDiagram) -> ExecutableDiagram:
        """Compile a DomainDiagram to ExecutableDiagram."""
        return self.compiler.compile(domain_diagram)
