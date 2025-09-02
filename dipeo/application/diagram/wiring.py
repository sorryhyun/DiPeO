"""Wiring module for diagram bounded context."""

import os
import logging
from pathlib import Path
from typing import TYPE_CHECKING

from dipeo.application.registry.service_registry import ServiceRegistry, ServiceKey
from dipeo.application.registry.keys import (
    DIAGRAM_COMPILER,
    DIAGRAM_SERIALIZER,
    RUNTIME_RESOLVER,
    TRANSFORMATION_ENGINE,
    DIAGRAM_PORT,
    COMPILE_DIAGRAM_USE_CASE,
    VALIDATE_DIAGRAM_USE_CASE,
    SERIALIZE_DIAGRAM_USE_CASE,
    LOAD_DIAGRAM_USE_CASE,
)

if TYPE_CHECKING:
    from dipeo.domain.diagram.compilation import DiagramCompiler
    from dipeo.domain.diagram.ports import DiagramStorageSerializer
    from dipeo.domain.diagram.compilation import CompileTimeResolver
    from dipeo.domain.execution.resolution import (
        RuntimeInputResolver,
        TransformationEngine,
    )
    from dipeo.application.diagram.use_cases import (
        CompileDiagramUseCase,
        ValidateDiagramUseCase,
        SerializeDiagramUseCase,
    )

logger = logging.getLogger(__name__)

# Define service keys for diagram context (only internal keys)
DIAGRAM_RESOLVER_KEY = ServiceKey["DiagramResolver"]("diagram.resolver")


def wire_diagram(registry: ServiceRegistry) -> None:
    """Wire diagram bounded context services and use cases.
    
    This includes:
    - Diagram compiler
    - Diagram serializer  
    - Compile-time resolver
    - Runtime resolver
    - Transformation engine
    - GraphQL resolvers
    """
    # Wire core diagram services
    wire_diagram_compiler(registry)
    wire_diagram_serializer(registry)
    wire_resolution_services(registry)
    wire_diagram_port(registry)
    
    # Wire diagram use cases
    wire_diagram_use_cases(registry)
    
    # Wire diagram GraphQL resolvers
    wire_diagram_resolvers(registry)


def wire_diagram_use_cases(registry: ServiceRegistry) -> None:
    """Wire diagram-specific use cases."""
    from dipeo.application.diagram.use_cases import (
        CompileDiagramUseCase,
        ValidateDiagramUseCase, 
        SerializeDiagramUseCase,
        LoadDiagramUseCase,
    )
    
    # Wire compile diagram use case
    def create_compile_diagram() -> CompileDiagramUseCase:
        """Factory for compile diagram use case."""
        compiler = registry.resolve(DIAGRAM_COMPILER)
        return CompileDiagramUseCase(diagram_compiler=compiler)
    
    registry.register(COMPILE_DIAGRAM_USE_CASE, create_compile_diagram)
    
    # Wire validate diagram use case
    def create_validate_diagram() -> ValidateDiagramUseCase:
        """Factory for validate diagram use case."""
        # ValidateDiagramUseCase can create its own validator if not provided
        return ValidateDiagramUseCase()
    
    registry.register(VALIDATE_DIAGRAM_USE_CASE, create_validate_diagram)
    
    # Wire serialize diagram use case
    def create_serialize_diagram() -> SerializeDiagramUseCase:
        """Factory for serialize diagram use case."""
        serializer = registry.resolve(DIAGRAM_SERIALIZER)
        return SerializeDiagramUseCase(diagram_serializer=serializer)
    
    registry.register(SERIALIZE_DIAGRAM_USE_CASE, create_serialize_diagram)
    
    # Wire load diagram use case
    def create_load_diagram() -> LoadDiagramUseCase:
        """Factory for load diagram use case."""
        diagram_service = registry.resolve(DIAGRAM_PORT)
        return LoadDiagramUseCase(diagram_service=diagram_service)
    
    registry.register(LOAD_DIAGRAM_USE_CASE, create_load_diagram)


def wire_diagram_resolvers(registry: ServiceRegistry) -> None:
    """Wire GraphQL resolvers for diagram context."""
    from dipeo.application.graphql.resolvers.diagram import DiagramResolver
    
    def create_diagram_resolver() -> DiagramResolver:
        """Factory for diagram GraphQL resolver."""
        return DiagramResolver(registry)
    
    registry.register(DIAGRAM_RESOLVER_KEY, create_diagram_resolver)


def wire_diagram_compiler(registry: ServiceRegistry) -> None:
    """Wire diagram compiler.
    
    Args:
        registry: Service registry to register compiler with
    """
    from dipeo.infrastructure.diagram.adapters import (
        StandardCompilerAdapter,
        CachingCompilerAdapter,
        ValidatingCompilerAdapter,
    )
    
    # Create base compiler - always use interface-based
    compiler = StandardCompilerAdapter(use_interface_based=True)
    
    # Apply decorators if configured
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
        UnifiedSerializerAdapter,
        CachingSerializerAdapter,
    )
    
    # Always use unified serializer
    serializer = UnifiedSerializerAdapter()
    
    # Apply caching if configured
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
    
    # For now, we'll use a simple runtime resolver placeholder
    # The actual runtime resolution is handled by domain logic
    # in dipeo.domain.execution.resolution.api.resolve_inputs
    class SimpleRuntimeResolver:
        """Placeholder runtime resolver.
        
        The actual resolution logic is in domain.execution.resolution.api.resolve_inputs
        which is called directly by handlers.
        """
        async def resolve_input_value(self, *args, **kwargs):
            # This is not actually used - resolution happens in domain layer
            raise NotImplementedError("Use domain.execution.resolution.api.resolve_inputs")
    
    runtime_resolver = SimpleRuntimeResolver()
    
    # Create transformation engine
    transform_engine = StandardTransformationEngine()
    
    # Register all resolution services
    registry.register(RUNTIME_RESOLVER, runtime_resolver)
    registry.register(TRANSFORMATION_ENGINE, transform_engine)


def wire_diagram_port(registry: ServiceRegistry) -> None:
    """Wire the unified diagram port.
    
    Args:
        registry: Service registry to register diagram port with
    """
    from dipeo.infrastructure.diagram.drivers.diagram_service import DiagramService
    from dipeo.config import get_settings
    from dipeo.application.registry.keys import FILESYSTEM_ADAPTER
    
    # Get filesystem adapter (should already be wired)
    # Determine base path using unified config - ensure it's absolute
    settings = get_settings()
    base_path = (Path(settings.storage.base_dir) / settings.storage.data_dir).resolve()
    
    filesystem = registry.resolve(FILESYSTEM_ADAPTER)
    if not filesystem:
        # Fallback to creating one with the correct base_dir from config
        from dipeo.infrastructure.shared.adapters import LocalFileSystemAdapter
        filesystem = LocalFileSystemAdapter(base_path=Path(settings.storage.base_dir).resolve())
    
    # Resolve dependencies from registry
    compiler = registry.resolve(DIAGRAM_COMPILER)
    serializer = registry.resolve(DIAGRAM_SERIALIZER)
    
    # Create service with adapters
    diagram_service = DiagramService(
        filesystem=filesystem,
        base_path=base_path,
        converter=serializer,  # Serializer implements the port
        compiler=compiler      # Compiler implements the port
    )
    
    registry.register(DIAGRAM_PORT, diagram_service)


# Backward compatibility export
def wire_diagram_services(registry: ServiceRegistry) -> None:
    """Wire all diagram-related services (backward compatibility)."""
    wire_diagram(registry)


# Export for external imports
is_diagram_v2_enabled = lambda: True  # V2 is always enabled now