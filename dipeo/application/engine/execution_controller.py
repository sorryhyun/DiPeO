# Unified execution controller for managing execution flow.

import logging
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, List

from dipeo.application.execution.flow_control_service import FlowControlService
from dipeo.models import NodeOutput, NodeType, DomainDiagram, NodeID

if TYPE_CHECKING:
    from ..execution.stateful_execution_typed import TypedStatefulExecution

log = logging.getLogger(__name__)


@dataclass
class ExecutionController:
    """Pure flow control - no state management."""
    
    flow_control_service: FlowControlService
    execution: "TypedStatefulExecution"  # Direct reference, not "adapter"
    iteration_count: int = 0
    max_global_iterations: int = 100
    
    async def initialize_nodes(self, diagram: "DomainDiagram") -> None:
        """Delegate to execution's built-in initialization."""
        # TypedStatefulExecution already initializes nodes in __init__
        pass  # Nothing to do
    
    def get_ready_nodes(self, diagram: "DomainDiagram") -> List[str]:
        """Get ready nodes using typed execution's methods."""
        ready_nodes = self.execution.get_ready_nodes()
        return [node.id for node in ready_nodes]
    
    
    async def mark_node_complete(self, node_id: str, output: NodeOutput) -> None:
        """Mark node as complete."""
        self.execution.mark_node_complete(NodeID(node_id))
        if output:
            self.execution.set_node_output(NodeID(node_id), output.value)

    def should_continue(self) -> bool:
        """Check if execution should continue."""
        if self.iteration_count >= self.max_global_iterations:
            return False
            
        # Use typed execution's is_complete method
        return not self.execution.is_complete()
    
    def increment_iteration(self) -> None:
        """Increment global iteration counter."""
        self.iteration_count += 1