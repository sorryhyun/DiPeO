"""Application wiring for diagram compilation and conversion services.

This module provides wiring for diagram-related services using domain architecture.
"""

import os
import logging
from typing import Any

from dipeo.application.registry import ServiceRegistry
from dipeo.application.registry.registry_tokens import (
    DIAGRAM_COMPILER,
    DIAGRAM_SERIALIZER,
    COMPILE_TIME_RESOLVER,
    RUNTIME_RESOLVER,
    TRANSFORMATION_ENGINE,
    DIAGRAM_PORT,
)

logger = logging.getLogger(__name__)


def wire_diagram_compiler(registry: ServiceRegistry) -> None:
    """Wire diagram compiler.
    
    Args:
        registry: Service registry to register compiler with
    """
    # Use domain port implementation
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
    # Use domain port implementation
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
        logger.info("Using strategy-based diagram serializer")
    else:
        serializer = UnifiedSerializerAdapter()
        logger.info("Using unified diagram serializer")
    
    if enable_caching:
        cache_size = int(os.getenv("DIAGRAM_SERIALIZER_CACHE_SIZE", "50"))
        serializer = CachingSerializerAdapter(serializer, cache_size=cache_size)
        logger.info(f"Diagram serializer caching enabled (size={cache_size})")
    
    registry.register(DIAGRAM_SERIALIZER, serializer)
    logger.info("Registered diagram serializer")


def wire_resolution_services(registry: ServiceRegistry) -> None:
    """Wire input resolution services.
    
    Args:
        registry: Service registry to register resolvers with
    """
    # Use domain port implementations
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
        logger.info("Using composite compile-time resolver")
    
    # Create runtime resolver
    runtime_resolver = StandardRuntimeResolverAdapter()
    
    # Optionally add caching
    enable_runtime_cache = os.getenv("DIAGRAM_RUNTIME_RESOLVER_CACHE", "1") == "1"
    if enable_runtime_cache:
        runtime_resolver = CachingRuntimeResolverAdapter(runtime_resolver)
        logger.info("Runtime resolver caching enabled")
    
    # Create transformation engine
    transform_engine = StandardTransformationEngineAdapter()
    
    # Register all resolution services
    registry.register(COMPILE_TIME_RESOLVER, compile_resolver)
    registry.register(RUNTIME_RESOLVER, runtime_resolver)
    registry.register(TRANSFORMATION_ENGINE, transform_engine)
    logger.info("Registered resolution services")


def wire_diagram_port(registry: ServiceRegistry) -> None:
    """Wire the unified diagram port.
    
    Args:
        registry: Service registry to register diagram port with
    """
    from dipeo.infrastructure.services.diagram import DiagramService
    from dipeo.domain.config import Config
    from pathlib import Path
    
    # Get filesystem adapter (should already be wired)
    from dipeo.application.registry.keys import FILESYSTEM_ADAPTER
    filesystem = registry.resolve(FILESYSTEM_ADAPTER)
    if not filesystem:
        # Fallback to creating one
        from dipeo.infrastructure.shared.adapters import LocalFileSystemAdapter
        filesystem = LocalFileSystemAdapter()
    
    # Determine base path
    config = Config()
    base_path = Path(config.base_dir) / "files"
    
    # Use V2 implementation with new adapters
    
    # Resolve V2 dependencies from registry
    compiler = registry.resolve(DIAGRAM_COMPILER)
    serializer = registry.resolve(DIAGRAM_SERIALIZER)
    
    # Create service with V2 adapters
    diagram_service = DiagramService(
        filesystem=filesystem,
        base_path=base_path,
        converter=serializer,  # V2 serializer implements the port
        compiler=compiler      # V2 compiler implements the port
    )
    
    registry.register(DIAGRAM_PORT, diagram_service)
    logger.info("Registered DiagramService with adapters")


def wire_all_diagram_services(registry: ServiceRegistry) -> None:
    """Wire all diagram-related services.
    
    This is the main entry point for diagram service wiring.
    Uses V2 domain architecture exclusively.
    
    Args:
        registry: Service registry to wire services with
    """
    logger.info("Starting diagram service wiring")
    
    # Wire in dependency order
    wire_diagram_compiler(registry)
    wire_diagram_serializer(registry)
    wire_resolution_services(registry)
    wire_diagram_port(registry)
    
    logger.info("Completed diagram service wiring")


# For backward compatibility, export the main wiring function
wire_diagram_services = wire_all_diagram_services