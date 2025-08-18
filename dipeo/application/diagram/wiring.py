"""Wiring module for diagram bounded context."""

import logging
from typing import TYPE_CHECKING

from dipeo.application.registry.service_registry import ServiceRegistry, ServiceKey

if TYPE_CHECKING:
    from dipeo.domain.diagram.compilation import DiagramCompiler
    from dipeo.domain.diagram.serialization import DiagramStorageSerializer
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
    
    # Import existing diagram wiring functions
    from dipeo.application.wiring.diagram_wiring import (
        wire_diagram_compiler,
        wire_diagram_serializer,
        wire_resolution_services,
        wire_diagram_port,
    )
    
    # Wire core diagram services using existing functions
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
    from dipeo.application.registry.registry_tokens import (
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