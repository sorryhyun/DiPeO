"""Domain compilation logic for transforming diagrams into executable form."""

from .compile_time_resolution import (
    CompileTimeResolver,
    Connection,
    TransformRules,
)
from .connection_resolver import ConnectionResolver, ResolvedConnection
from .domain_compiler import (
    CompilationContext,
    CompilationError,
    CompilationPhase,
    CompilationResult,
    DomainDiagramCompiler,
)
from .edge_builder import EdgeBuilder, TransformationMetadata
from .node_factory import NodeFactory

__all__ = [
    "CompilationContext",
    "CompilationError",
    "CompilationPhase",
    "CompilationResult",
    "CompileTimeResolver",
    "Connection",
    "ConnectionResolver",
    "DomainDiagramCompiler",
    "EdgeBuilder",
    "NodeFactory",
    "ResolvedConnection",
    "TransformRules",
    "TransformationMetadata",
]
