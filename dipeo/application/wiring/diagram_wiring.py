"""Application wiring for diagram compilation and conversion services.

This module provides wiring for diagram-related services with feature flag support,
enabling gradual migration from core/ports to domain ports.
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


def is_diagram_v2_enabled(service_name: str) -> bool:
    """Check if V2 is enabled for a specific diagram service.
    
    Args:
        service_name: Name of the service (e.g., 'compiler', 'serializer')
        
    Returns:
        True if V2 is enabled for the service
    """
    # Check specific service flag first
    specific_flag = os.getenv(f"DIAGRAM_{service_name.upper()}_V2", "").lower()
    if specific_flag in ["1", "true", "yes", "on"]:
        return True
    if specific_flag in ["0", "false", "no", "off"]:
        return False
    
    # Check diagram-wide flag
    diagram_flag = os.getenv("DIAGRAM_PORT_V2", "").lower()
    if diagram_flag in ["1", "true", "yes", "on"]:
        return True
    if diagram_flag in ["0", "false", "no", "off"]:
        return False
    
    # Check global flag
    global_flag = os.getenv("DIPEO_PORT_V2", "0").lower()
    return global_flag in ["1", "true", "yes", "on"]


def wire_diagram_compiler(registry: ServiceRegistry) -> None:
    """Wire diagram compiler based on feature flags.
    
    Args:
        registry: Service registry to register compiler with
    """
    if is_diagram_v2_enabled("compiler"):
        # Use V2 domain port implementation
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
        logger.info(f"Registered V2 diagram compiler (interface_based={use_interface_based})")
    else:
        # Use V1 core port implementation - use DomainDiagramCompiler directly
        from dipeo.domain.diagram.compilation import DomainDiagramCompiler
        
        compiler = DomainDiagramCompiler()
        
        # Register using token for compatibility
        registry.register(DIAGRAM_COMPILER, compiler)
        logger.info("Registered V1 diagram compiler (DomainDiagramCompiler)")


def wire_diagram_serializer(registry: ServiceRegistry) -> None:
    """Wire diagram serializer based on feature flags.
    
    Args:
        registry: Service registry to register serializer with
    """
    if is_diagram_v2_enabled("serializer"):
        # Use V2 domain port implementation
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
        logger.info("Registered V2 diagram serializer")
    else:
        # Use V1 core port implementation - use DiagramConverterService directly
        from dipeo.infrastructure.services.diagram import DiagramConverterService
        
        converter = DiagramConverterService()
        # Register using token for compatibility
        registry.register(DIAGRAM_SERIALIZER, converter)
        logger.info("Registered V1 diagram converter (DiagramConverterService)")


def wire_resolution_services(registry: ServiceRegistry) -> None:
    """Wire input resolution services based on feature flags.
    
    Args:
        registry: Service registry to register resolvers with
    """
    if is_diagram_v2_enabled("resolution"):
        # Use V2 domain port implementations
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
        logger.info("Registered V2 resolution services")
    else:
        # Use V1 implementations - create dummy implementations for now
        # since the actual resolution classes may not exist yet
        logger.info("V1 resolution services not implemented, skipping registration")


def wire_diagram_port(registry: ServiceRegistry) -> None:
    """Wire the unified diagram port based on feature flags.
    
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
    
    if is_diagram_v2_enabled("port"):
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
        logger.info("Registered DiagramService with V2 adapters")
    else:
        # Use V1 implementation with old services
        
        # Create service with V1 services (will use defaults internally)
        diagram_service = DiagramService(
            filesystem=filesystem,
            base_path=base_path,
            converter=None,  # Will default to DiagramConverterService
            compiler=None    # Will default to CompilationService
        )
        
        registry.register(DIAGRAM_PORT, diagram_service)
        logger.info("Registered DiagramService with V1 services")


def wire_all_diagram_services(registry: ServiceRegistry) -> None:
    """Wire all diagram-related services.
    
    This is the main entry point for diagram service wiring.
    
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