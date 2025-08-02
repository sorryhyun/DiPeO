"""Core compilation interfaces and structures."""

from .diagram_compiler import DiagramCompiler
from .executable_diagram import ExecutableDiagram, ExecutableNode, ExecutableEdgeV2
from .compile_time_context import CompileTimeContext

__all__ = [
    "DiagramCompiler",
    "ExecutableDiagram",
    "ExecutableNode",
    "ExecutableEdgeV2",
    "CompileTimeContext",
]