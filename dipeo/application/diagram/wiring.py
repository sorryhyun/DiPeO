"""Wiring module for diagram bounded context."""

import logging
import os
from pathlib import Path
from typing import TYPE_CHECKING

from dipeo.application.registry.enhanced_service_registry import (
    EnhancedServiceRegistry as ServiceRegistry,
)
from dipeo.application.registry.keys import (
    COMPILE_DIAGRAM_USE_CASE,
    DIAGRAM_COMPILER,
    DIAGRAM_PORT,
    DIAGRAM_SERIALIZER,
    LOAD_DIAGRAM_USE_CASE,
    SERIALIZE_DIAGRAM_USE_CASE,
    TRANSFORMATION_ENGINE,
    VALIDATE_DIAGRAM_USE_CASE,
)
from dipeo.config.base_logger import get_module_logger

if TYPE_CHECKING:
    pass

logger = get_module_logger(__name__)


def wire_diagram(registry: ServiceRegistry) -> None:
    """Wire diagram bounded context services and use cases.

    This includes:
    - Diagram compiler
    - Diagram serializer
    - Compile-time resolver
    - Runtime resolver
    - Transformation engine
    """
    wire_diagram_compiler(registry)
    wire_diagram_serializer(registry)
    wire_resolution_services(registry)
    wire_diagram_port(registry)
    wire_diagram_use_cases(registry)


def wire_diagram_use_cases(registry: ServiceRegistry) -> None:
    """Wire diagram-specific use cases.

    These use cases are conditionally used:
    - COMPILE_DIAGRAM_USE_CASE: Used when compiling sub-diagrams, not in simple diagrams
    - VALIDATE_DIAGRAM_USE_CASE: Used for diagram validation before execution
    - SERIALIZE_DIAGRAM_USE_CASE: Used for format conversion and storage
    - LOAD_DIAGRAM_USE_CASE: Used by sub-diagram nodes to load nested diagrams
    """
    from dipeo.application.diagram.use_cases import (
        CompileDiagramUseCase,
        LoadDiagramUseCase,
        SerializeDiagramUseCase,
        ValidateDiagramUseCase,
    )

    def create_compile_diagram() -> CompileDiagramUseCase:
        compiler = registry.resolve(DIAGRAM_COMPILER)
        return CompileDiagramUseCase(diagram_compiler=compiler)

    registry.register(COMPILE_DIAGRAM_USE_CASE, create_compile_diagram)

    def create_validate_diagram() -> ValidateDiagramUseCase:
        return ValidateDiagramUseCase()

    registry.register(VALIDATE_DIAGRAM_USE_CASE, create_validate_diagram)

    def create_serialize_diagram() -> SerializeDiagramUseCase:
        serializer = registry.resolve(DIAGRAM_SERIALIZER)
        return SerializeDiagramUseCase(diagram_serializer=serializer)

    registry.register(SERIALIZE_DIAGRAM_USE_CASE, create_serialize_diagram)

    def create_load_diagram() -> LoadDiagramUseCase:
        diagram_service = registry.resolve(DIAGRAM_PORT)
        # Use segregated ports from the diagram service
        return LoadDiagramUseCase(
            file_port=diagram_service.file_port, format_port=diagram_service.format_port
        )

    registry.register(LOAD_DIAGRAM_USE_CASE, create_load_diagram)


def wire_diagram_compiler(registry: ServiceRegistry) -> None:
    """Wire diagram compiler.

    Args:
        registry: Service registry to register compiler with
    """
    from dipeo.infrastructure.diagram.adapters import (
        CachingCompilerAdapter,
        StandardCompilerAdapter,
        ValidatingCompilerAdapter,
    )

    compiler = StandardCompilerAdapter(use_interface_based=True)
    enable_validation = os.getenv("DIAGRAM_COMPILER_VALIDATE", "1") == "1"
    enable_caching = os.getenv("DIAGRAM_COMPILER_CACHE", "1") == "1"

    if enable_validation:
        compiler = ValidatingCompilerAdapter(compiler)

    if enable_caching:
        cache_size = int(os.getenv("DIAGRAM_COMPILER_CACHE_SIZE", "100"))
        compiler = CachingCompilerAdapter(compiler, cache_size=cache_size)

    registry.register(DIAGRAM_COMPILER, compiler)


def wire_diagram_serializer(registry: ServiceRegistry) -> None:
    """Wire diagram serializer.

    Args:
        registry: Service registry to register serializer with
    """
    from dipeo.infrastructure.diagram.adapters import (
        CachingSerializerAdapter,
        UnifiedSerializerAdapter,
    )

    serializer = UnifiedSerializerAdapter()
    enable_caching = os.getenv("DIAGRAM_SERIALIZER_CACHE", "1") == "1"
    if enable_caching:
        cache_size = int(os.getenv("DIAGRAM_SERIALIZER_CACHE_SIZE", "50"))
        serializer = CachingSerializerAdapter(serializer, cache_size=cache_size)

    registry.register(DIAGRAM_SERIALIZER, serializer)


def wire_resolution_services(registry: ServiceRegistry) -> None:
    """Wire input resolution services.

    Args:
        registry: Service registry to register resolvers with
    """
    from dipeo.domain.execution.resolution import StandardTransformationEngine

    transform_engine = StandardTransformationEngine()
    registry.register(TRANSFORMATION_ENGINE, transform_engine)


def wire_diagram_port(registry: ServiceRegistry) -> None:
    """Wire the unified diagram port.

    Args:
        registry: Service registry to register diagram port with
    """
    from dipeo.application.registry.keys import FILESYSTEM_ADAPTER
    from dipeo.config import get_settings
    from dipeo.infrastructure.diagram.drivers.diagram_service import DiagramService

    # Ensure dependencies are wired first
    if not registry.has(DIAGRAM_COMPILER):
        wire_diagram_compiler(registry)

    if not registry.has(DIAGRAM_SERIALIZER):
        wire_diagram_serializer(registry)

    # Determine base path using unified config - ensure it's absolute
    settings = get_settings()
    base_path = (Path(settings.storage.base_dir) / settings.storage.data_dir).resolve()

    if registry.has(FILESYSTEM_ADAPTER):
        filesystem = registry.resolve(FILESYSTEM_ADAPTER)
    else:
        from dipeo.infrastructure.storage import LocalFileSystemAdapter

        filesystem = LocalFileSystemAdapter(base_path=Path(settings.storage.base_dir).resolve())

    compiler = registry.resolve(DIAGRAM_COMPILER)
    serializer = registry.resolve(DIAGRAM_SERIALIZER)
    diagram_service = DiagramService(
        filesystem=filesystem,
        base_path=base_path,
        converter=serializer,
        compiler=compiler,
    )

    registry.register(DIAGRAM_PORT, diagram_service)


def wire_diagram_services(registry: ServiceRegistry) -> None:
    """Wire all diagram-related services (backward compatibility)."""
    wire_diagram(registry)


def is_diagram_v2_enabled():
    """Check if diagram V2 is enabled (always True)."""
    return True
