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
        self._initialized = False
        self._initialization_lock = asyncio.Lock()

        self.filesystem = filesystem
        self.base_path = Path(base_path)

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

        from dipeo.infrastructure.diagram.drivers.segregated_adapters import (
            FileAdapter,
            FormatAdapter,
            RepositoryAdapter,
        )

        self.format_port = FormatAdapter(self.converter)
        self.file_port = FileAdapter(filesystem, base_path, self.format_port)
        self.repository_port = RepositoryAdapter(filesystem, base_path, self.format_port)

        self.format_detector = DiagramFormatDetector()

    async def initialize(self) -> None:
        try:
            self.filesystem.mkdir(self.base_path, parents=True)
        except Exception as e:
            raise StorageError(f"Failed to initialize diagram storage: {e}") from e

        if hasattr(self.converter, "initialize"):
            await self.converter.initialize()
        if hasattr(self.compiler, "initialize"):
            await self.compiler.initialize()

    def detect_format(self, content: str) -> DiagramFormat:
        return self.format_port.detect_format(content)

    def serialize(self, diagram: DomainDiagram, format_type: str) -> str:
        return self.format_port.serialize(diagram, format_type)

    def deserialize(
        self, content: str, format_type: str | None = None, diagram_path: str | None = None
    ) -> DomainDiagram:
        return self.format_port.deserialize(content, format_type, diagram_path)

    def load_from_string(self, content: str, format_type: str | None = None) -> DomainDiagram:
        return self.format_port.deserialize(content, format_type)

    async def load_from_file(self, file_path: str) -> DomainDiagram:
        if not self._initialized:
            await self.initialize()
        return await self.file_port.load_from_file(file_path)

    async def create_diagram(
        self, name: str, diagram: DomainDiagram, format_type: str = "native"
    ) -> str:
        if not self._initialized:
            await self.initialize()
        return await self.repository_port.create(name, diagram, format_type)

    async def get_diagram(self, diagram_id: str) -> Optional[DomainDiagram]:
        if not self._initialized:
            await self.initialize()
        return await self.repository_port.get(diagram_id)

    async def update_diagram(self, diagram_id: str, diagram: DomainDiagram) -> None:
        if not self._initialized:
            await self.initialize()
        await self.repository_port.update(diagram_id, diagram)

    async def delete_diagram(self, diagram_id: str) -> None:
        if not self._initialized:
            await self.initialize()
        await self.repository_port.delete(diagram_id)

    async def exists(self, diagram_id: str) -> bool:
        if not self._initialized:
            await self.initialize()
        return await self.repository_port.exists(diagram_id)

    async def list_diagrams(self, format_type: str | None = None) -> list[DiagramInfo]:
        if not self._initialized:
            await self.initialize()
        return await self.repository_port.list(format_type)

    def compile(self, domain_diagram: DomainDiagram) -> ExecutableDiagram:
        return self.compiler.compile(domain_diagram)
