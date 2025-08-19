"""Base classes for the input resolution pipeline."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Protocol

from dipeo.diagram_generated import NodeID, NodeType
from dipeo.domain.execution.execution_context import ExecutionContext
from dipeo.domain.execution.envelope import Envelope
from dipeo.domain.diagram.models.executable_diagram import (
    ExecutableEdgeV2,
    ExecutableNode,
    ExecutableDiagram
)


@dataclass
class PipelineContext:
    """Context passed through the pipeline stages.
    
    This accumulates data as it flows through the pipeline stages,
    allowing each stage to access previous results and add new data.
    """
    node: ExecutableNode
    context: ExecutionContext
    diagram: ExecutableDiagram
    
    # Data accumulated through pipeline
    incoming_edges: list[ExecutableEdgeV2] = field(default_factory=list)
    filtered_edges: list[ExecutableEdgeV2] = field(default_factory=list)
    # Use edge ID as key to avoid hashability issues with edges containing dicts
    edge_values: dict[str, Any] = field(default_factory=dict)
    special_inputs: dict[str, Any] = field(default_factory=dict)
    transformed_values: dict[str, Any] = field(default_factory=dict)
    final_inputs: dict[str, Any] = field(default_factory=dict)
    
    # Metadata for decision making
    has_special_inputs: bool = False
    node_strategy: Any = None
    
    def get_edge_value(self, edge: ExecutableEdgeV2) -> Any:
        """Get the value associated with an edge."""
        # Create a unique key for the edge
        edge_key = self._get_edge_key(edge)
        return self.edge_values.get(edge_key)
    
    def set_edge_value(self, edge: ExecutableEdgeV2, value: Any) -> None:
        """Set the value for an edge."""
        # Create a unique key for the edge
        edge_key = self._get_edge_key(edge)
        self.edge_values[edge_key] = value
    
    def _get_edge_key(self, edge: ExecutableEdgeV2) -> str:
        """Create a unique key for an edge."""
        # Use combination of source and target to create unique key
        source = str(edge.source_node_id)
        target = str(edge.target_node_id)
        source_output = edge.source_output or "default"
        target_input = edge.target_input or "default"
        return f"{source}:{source_output}->{target}:{target_input}"


class PipelineStage(ABC):
    """Base class for pipeline stages.
    
    Each stage focuses on a single responsibility in the input
    resolution process.
    """
    
    @abstractmethod
    async def process(self, ctx: PipelineContext) -> PipelineContext:
        """Process the pipeline context.
        
        Args:
            ctx: The pipeline context with accumulated data
            
        Returns:
            The modified context (can be the same object)
        """
        pass
    
    @property
    def name(self) -> str:
        """Get the name of this stage."""
        return self.__class__.__name__