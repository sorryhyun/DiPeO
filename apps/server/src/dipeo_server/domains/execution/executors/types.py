"""Core type definitions and protocols for the unified executor system."""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Protocol, Type

from dipeo_domain import NodeDefinition as GeneratedNodeDefinition
from pydantic import BaseModel


# Use NodeOutput from generated models for all executor results
class NodeHandler(Protocol):
    """Protocol for node handlers."""

    async def __call__(
        self,
        props: BaseModel,
        context: "RuntimeCtx",
        inputs: Dict[str, Any],
        services: Dict[str, Any],
    ) -> Any:
        """Execute the node handler with validated properties and injected services."""
        ...


# runtime handler references which can't be serialized
@dataclass
class RuntimeNodeDefinition:
    """Runtime definition of a node type with handler references."""

    type: str
    schema: Type[BaseModel]
    handler: NodeHandler
    requires_services: List[str] = field(default_factory=list)
    description: str = ""


# Services are now injected separately via service factory
@dataclass
class RuntimeCtx:
    """Runtime execution context for handlers - pure data container."""

    edges: List[Dict[str, Any]]
    results: Dict[str, Dict[str, Any]]
    current_node_id: str
    execution_id: str
    exec_cnt: Dict[str, int] = field(default_factory=dict)  # Node execution counts
    outputs: Dict[str, Any] = field(default_factory=dict)  # Node outputs
    persons: Dict[str, Any] = field(default_factory=dict)  # Person configurations
    api_keys: Dict[str, str] = field(default_factory=dict)  # API keys

    def get_node_execution_count(self, node_id: str) -> int:
        """Get execution count for a specific node."""
        return self.exec_cnt.get(node_id, 0)

    def increment_node_execution_count(self, node_id: str) -> None:
        """Increment execution count for a specific node."""
        self.exec_cnt[node_id] = self.exec_cnt.get(node_id, 0) + 1


# Create a custom serializable context since generated ExecutionContext has different fields
@dataclass
class SerializableExecutionContext:
    """Serializable version of RuntimeCtx for API/persistence."""

    edges: List[Dict[str, Any]]
    results: Dict[str, Dict[str, Any]]
    current_node_id: str
    execution_id: str
    exec_cnt: Dict[str, int] = field(default_factory=dict)
    outputs: Dict[str, Any] = field(default_factory=dict)
    persons: Dict[str, Any] = field(default_factory=dict)
    api_keys: Dict[str, str] = field(default_factory=dict)


# Serializable types for API/persistence
SerializableNodeDefinition = GeneratedNodeDefinition


# Conversion functions
def to_serializable_context(runtime_ctx: RuntimeCtx) -> SerializableExecutionContext:
    """Convert runtime execution context to serializable format.

    Excludes service references and methods that can't be serialized.
    """
    return SerializableExecutionContext(
        edges=runtime_ctx.edges,
        results=runtime_ctx.results,
        current_node_id=runtime_ctx.current_node_id,
        execution_id=runtime_ctx.execution_id,
        exec_cnt=runtime_ctx.exec_cnt,
        outputs=runtime_ctx.outputs,
        persons=runtime_ctx.persons,
        api_keys=runtime_ctx.api_keys,
    )


def from_serializable_context(
    serializable_ctx: SerializableExecutionContext,
) -> RuntimeCtx:
    """Create runtime execution context from serializable format.

    Services are no longer part of the context - they are injected
    separately via the service factory pattern.
    """
    return RuntimeCtx(
        edges=serializable_ctx.edges,
        results=serializable_ctx.results,
        current_node_id=serializable_ctx.current_node_id,
        execution_id=serializable_ctx.execution_id,
        exec_cnt=serializable_ctx.exec_cnt,
        outputs=serializable_ctx.outputs,
        persons=serializable_ctx.persons,
        api_keys=serializable_ctx.api_keys,
    )
