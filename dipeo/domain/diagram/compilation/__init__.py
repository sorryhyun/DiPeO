"""Domain compilation logic for transforming diagrams into executable form."""

from .connection_resolver import ConnectionResolver, ResolvedConnection
from .edge_builder import EdgeBuilder, TransformationMetadata
from .node_factory import NodeFactory
from .domain_compiler import (
    DomainDiagramCompiler,
    CompilationResult,
    CompilationError,
    CompilationPhase,
    CompilationContext,
)
from .compile_time_resolution import (
    Connection,
    TransformRules,
    CompileTimeResolver,
)

__all__ = [
    "NodeFactory",
    "EdgeBuilder",
    "ConnectionResolver",
    "ResolvedConnection",
    "TransformationMetadata",
    "DomainDiagramCompiler",
    "CompilationResult",
    "CompilationError",
    "CompilationPhase",
    "CompilationContext",
    # Compile-time resolution
    "Connection",
    "TransformRules",
    "CompileTimeResolver",
]