"""Unified execution controller for managing execution flow.

This module provides the controller that determines which nodes are ready
to execute based on dependencies, delegating state management to the
ApplicationExecutionState adapter.
"""

import logging
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Optional

from dipeo.domain.services.execution import FlowControlService
from dipeo.models import NodeOutput, NodeType, DomainDiagram

if TYPE_CHECKING:
    from ..execution.adapters.state_adapter import ApplicationExecutionState

log = logging.getLogger(__name__)


@dataclass
class ExecutionController:
    """Unified controller for execution flow."""
    
    flow_control_service: FlowControlService
    state_adapter: Optional["ApplicationExecutionState"] = None
    iteration_count: int = 0
    max_global_iterations: int = 100
    
    async def initialize_nodes(self, diagram: "DomainDiagram") -> None:
        """Initialize node states from diagram."""
        if not self.state_adapter:
            raise ValueError("State adapter not set")
            
        for node in diagram.nodes:
            max_iter = 1
            if node.type in [NodeType.person_job.value, NodeType.job.value]:
                max_iter = (node.data or {}).get("max_iteration", 1)
            
            # Initialize node state through adapter
            await self.state_adapter.update_node_state(
                node_id=node.id,
                node_type=node.type,
                max_iterations=max_iter
            )
    
    def get_ready_nodes(self, diagram: "DomainDiagram") -> list[str]:
        """Get all nodes ready for execution."""
        if not self.state_adapter:
            raise ValueError("State adapter not set")
            
        # Get state from adapter
        node_outputs = self.state_adapter.get_all_node_outputs()
        node_exec_counts = self.state_adapter.get_all_node_exec_counts()
        executed_nodes = self.state_adapter.get_executed_nodes()
        
        ready_nodes = self.flow_control_service.get_ready_nodes(
            diagram=diagram,
            executed_nodes=executed_nodes,
            node_outputs=node_outputs,
            node_exec_counts=node_exec_counts
        )
        
        # Log initial ready nodes
        initial_ready = [node.id for node in ready_nodes]
        if initial_ready:
            log.debug(f"Flow control ready nodes: {initial_ready}")
        
        # Filter by nodes that can still execute
        ready = []
        filtered_out = []
        for node in ready_nodes:
            if self.state_adapter.can_node_execute(node.id):
                ready.append(node.id)
            else:
                filtered_out.append(node.id)
        
        if filtered_out:
            log.debug(f"Nodes filtered out by state adapter: {filtered_out}")
        
        log.debug(f"Ready nodes: {ready}")
        return ready
    
    
    async def mark_executed(self, node_id: str, output: NodeOutput, node_type: str) -> None:
        """Mark node as executed with output."""
        if not self.state_adapter:
            raise ValueError("State adapter not set")
            
        # Get max iterations for the node
        max_iterations = self.state_adapter.get_node_max_iterations(node_id)
        
        # Update state through adapter
        await self.state_adapter.update_node_state(
            node_id=node_id,
            node_type=node_type,
            output=output,
            max_iterations=max_iterations,
            increment_exec_count=True
        )
        
        exec_count = self.state_adapter.get_node_exec_count(node_id)

    def should_continue(self) -> bool:
        """Check if execution should continue."""
        if not self.state_adapter:
            return False
            
        if self.iteration_count >= self.max_global_iterations:
            return False
            
        # Check if any endpoint has been executed
        if self.state_adapter.is_endpoint_executed():
            return False
            
        # Check if any nodes can still execute
        for node_id in self.state_adapter.execution_state.node_states:
            if self.state_adapter.can_node_execute(node_id):
                return True
                
        return False
    
    def increment_iteration(self) -> None:
        """Increment global iteration counter."""
        self.iteration_count += 1