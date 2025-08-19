"""Wiring module for diagram bounded context."""

import os
import logging
from pathlib import Path
from typing import TYPE_CHECKING

from dipeo.application.registry.service_registry import ServiceRegistry, ServiceKey
from dipeo.application.registry.keys import (
    DIAGRAM_COMPILER,
    DIAGRAM_SERIALIZER,
    COMPILE_TIME_RESOLVER,
    RUNTIME_RESOLVER,
    TRANSFORMATION_ENGINE,
    DIAGRAM_PORT,
)

if TYPE_CHECKING:
    from dipeo.domain.diagram.compilation import DiagramCompiler
    from dipeo.domain.diagram.ports import DiagramStorageSerializer
    from dipeo.domain.diagram.resolution.interfaces import (
        CompileTimeResolverV2,
        RuntimeInputResolverV2,
        TransformationEngineV2,
    )
    from dipeo.application.diagram.use_cases import (
        CompileDiagramUseCase,
        ValidateDiagramUseCase,
        SerializeDiagramUseCase,
    )

logger = logging.getLogger(__name__)

# Define service keys for diagram context
COMPILE_DIAGRAM_USE_CASE = ServiceKey["CompileDiagramUseCase"]("diagram.use_case.compile")
VALIDATE_DIAGRAM_USE_CASE = ServiceKey["ValidateDiagramUseCase"]("diagram.use_case.validate")
SERIALIZE_DIAGRAM_USE_CASE = ServiceKey["SerializeDiagramUseCase"]("diagram.use_case.serialize")
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
    logger.info("🔧 Wiring diagram bounded context")
    
    # Wire core diagram services
    wire_diagram_compiler(registry)
    wire_diagram_serializer(registry)
    wire_resolution_services(registry)
    wire_diagram_port(registry)
    
    # Wire diagram use cases
    wire_diagram_use_cases(registry)
    
    # Wire diagram GraphQL resolvers
    wire_diagram_resolvers(registry)
    
    logger.info("✅ Diagram bounded context wired")


def wire_diagram_use_cases(registry: ServiceRegistry) -> None:
    """Wire diagram-specific use cases."""
    from dipeo.application.registry.keys import (
        DIAGRAM_COMPILER,
        DIAGRAM_SERIALIZER,
    )
    from dipeo.application.diagram.use_cases import (
        CompileDiagramUseCase,
        ValidateDiagramUseCase, 
        SerializeDiagramUseCase,
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
    
    # Determine which compiler variant to use
    use_interface_based = os.getenv("DIAGRAM_USE_INTERFACE_COMPILER", "1") == "1"
    enable_caching = os.getenv("DIAGRAM_COMPILER_CACHE", "1") == "1"
    enable_validation = os.getenv("DIAGRAM_COMPILER_VALIDATE", "1") == "1"
    
    # Create base compiler
    compiler = StandardCompilerAdapter(use_interface_based=use_interface_based)
    
    # Apply decorators
    if enable_validation:
        compiler = ValidatingCompilerAdapter(compiler)
        logger.info("Diagram compiler validation enabled")
    
    if enable_caching:
        cache_size = int(os.getenv("DIAGRAM_COMPILER_CACHE_SIZE", "100"))
        compiler = CachingCompilerAdapter(compiler, cache_size=cache_size)
        logger.info(f"Diagram compiler caching enabled (size={cache_size})")
    
    registry.register(DIAGRAM_COMPILER, compiler)
    logger.info(f"Registered diagram compiler (interface_based={use_interface_based})")


def wire_diagram_serializer(registry: ServiceRegistry) -> None:
    """Wire diagram serializer.
    
    Args:
        registry: Service registry to register serializer with
    """
    from dipeo.infrastructure.diagram.adapters import (
        UnifiedSerializerAdapter,
        FormatStrategyAdapter,
        CachingSerializerAdapter,
    )
    
    # Determine which serializer to use
    use_strategy_based = os.getenv("DIAGRAM_USE_STRATEGY_SERIALIZER", "0") == "1"
    enable_caching = os.getenv("DIAGRAM_SERIALIZER_CACHE", "1") == "1"
    
    if use_strategy_based:
        serializer = FormatStrategyAdapter()
    else:
        serializer = UnifiedSerializerAdapter()

    if enable_caching:
        cache_size = int(os.getenv("DIAGRAM_SERIALIZER_CACHE_SIZE", "50"))
        serializer = CachingSerializerAdapter(serializer, cache_size=cache_size)

    registry.register(DIAGRAM_SERIALIZER, serializer)


def wire_resolution_services(registry: ServiceRegistry) -> None:
    """Wire input resolution services.
    
    Args:
        registry: Service registry to register resolvers with
    """
    from dipeo.infrastructure.diagram.adapters import (
        StandardCompileTimeResolverAdapter,
        StandardRuntimeResolverAdapter,
        StandardTransformationEngineAdapter,
        CompositeResolverAdapter,
        CachingRuntimeResolverAdapter,
    )
    
    # Create compile-time resolver
    compile_resolver = StandardCompileTimeResolverAdapter()
    
    # Optionally use composite resolver for fallback
    use_composite = os.getenv("DIAGRAM_USE_COMPOSITE_RESOLVER", "0") == "1"
    if use_composite:
        # Could add multiple resolvers here for fallback
        compile_resolver = CompositeResolverAdapter([compile_resolver])

    # Create runtime resolver
    runtime_resolver = StandardRuntimeResolverAdapter()
    
    # Optionally add caching
    enable_runtime_cache = os.getenv("DIAGRAM_RUNTIME_RESOLVER_CACHE", "1") == "1"
    if enable_runtime_cache:
        runtime_resolver = CachingRuntimeResolverAdapter(runtime_resolver)

    # Create transformation engine
    transform_engine = StandardTransformationEngineAdapter()
    
    # Register all resolution services
    registry.register(COMPILE_TIME_RESOLVER, compile_resolver)
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