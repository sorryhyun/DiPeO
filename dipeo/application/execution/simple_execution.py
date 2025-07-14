"""
Simplified stateful execution that follows the actual design requirements.
"""

import logging
from typing import TYPE_CHECKING, Any
from dipeo.core.static.executable_diagram import ExecutableDiagram, ExecutableNode
from dipeo.core.static.generated_nodes import (
    ConditionNode,
    EndpointNode,
    PersonJobNode,
    StartNode,
)
from dipeo.models import ExecutionState, NodeExecutionStatus, NodeID, NodeState

if TYPE_CHECKING:
    from dipeo.application.execution import UnifiedExecutionContext

logger = logging.getLogger(__name__)


class SimpleExecution:
    """Simple execution state management without over-engineering."""
    
    def __init__(self, diagram: ExecutableDiagram, context: "UnifiedExecutionContext"):
        self.diagram = diagram
        self.context = context
        
        # Initialize node states if not already present
        for node in diagram.nodes:
            if not context.get_node_state(node.id):
                context.set_node_state(
                    node.id,
                    NodeState(
                        status=NodeExecutionStatus.PENDING,
                        node_id=node.id
                    )
                )
    
    @property
    def diagram_id(self) -> str:
        """Get diagram ID for compatibility."""
        return getattr(self.state, 'diagram_id', '')
    
    @property
    def execution_id(self) -> str:
        """Get execution ID for compatibility."""
        return getattr(self.state, 'execution_id', '')
    
    @property
    def state(self) -> ExecutionState:
        """Get execution state from context for compatibility."""
        return self.context.execution_state
    
    @property
    def exec_counts(self) -> dict[str, int]:
        """Get execution counts from context for compatibility."""
        return self.context._exec_counts
    
    @property
    def executed_nodes(self) -> set[str]:
        """Get set of executed node IDs for compatibility."""
        return set(self.context.executed_nodes)
    
    def get_completed_nodes(self) -> list[NodeID]:
        """Get list of completed node IDs."""
        return self.context.get_completed_nodes()
    
    def get_ready_nodes(self) -> list[ExecutableNode]:
        """Get nodes that are ready to execute."""
        ready = []
        
        for node in self.diagram.nodes:
            if self._is_node_ready(node):
                ready.append(node)
        
        logger.debug(f"get_ready_nodes: Found {len(ready)} ready nodes: {[n.id for n in ready]}")
        return ready
    
    def _is_node_ready(self, node: ExecutableNode) -> bool:
        """Check if a node is ready to execute."""
        # Not pending? Not ready
        node_state = self.context.get_node_state(node.id)
        if not node_state or node_state.status != NodeExecutionStatus.PENDING:
            logger.debug(f"Node {node.id} not ready: status={node_state.status if node_state else 'None'}")
            return False
        
        # Start nodes are always ready when pending
        if isinstance(node, StartNode):
            logger.debug(f"Node {node.id} is ready: StartNode")
            return True
        
        # Check dependencies
        incoming_edges = self.diagram.get_incoming_edges(node.id)
        
        # Special handling for PersonJobNodes
        if isinstance(node, PersonJobNode):
            exec_count = self.context.get_node_execution_count(node.id)
            logger.debug(f"Node {node.id} is PersonJobNode: exec_count={exec_count}, max_iteration={node.max_iteration}")
            
            # Reached max iterations? Not ready
            if exec_count >= node.max_iteration:
                logger.debug(f"Node {node.id} not ready: reached max iterations")
                return False
            
            # First execution? Only check 'first' inputs or non-loop edges
            if exec_count == 0:
                first_edges = [e for e in incoming_edges if e.target_input == "first"]
                logger.debug(f"Node {node.id} edges: total={len(incoming_edges)}, first={len(first_edges)}")
                logger.debug(f"Node {node.id} incoming edges: {[(e.source_node_id, e.target_input) for e in incoming_edges]}")
                if first_edges:
                    incoming_edges = first_edges
                    logger.debug(f"Node {node.id} first execution: using {len(incoming_edges)} 'first' input edges")
                else:
                    # No 'first' edges found - filter out edges from condition nodes (loop edges)
                    non_loop_edges = []
                    for edge in incoming_edges:
                        source_node = next((n for n in self.diagram.nodes if n.id == edge.source_node_id), None)
                        if source_node and not isinstance(source_node, ConditionNode):
                            non_loop_edges.append(edge)
                    if non_loop_edges:
                        incoming_edges = non_loop_edges
                        logger.debug(f"Node {node.id} first execution: using {len(incoming_edges)} non-loop edges")
                    else:
                        logger.debug(f"Node {node.id} first execution: no 'first' or non-loop edges found, using all {len(incoming_edges)} edges")
        
        # All dependencies must be completed
        for edge in incoming_edges:
            dep_state = self.context.get_node_state(edge.source_node_id)
            if not dep_state or dep_state.status != NodeExecutionStatus.COMPLETED:
                return False
            
            # For condition nodes, check if this branch is active
            source_node = next((n for n in self.diagram.nodes if n.id == edge.source_node_id), None)
            if isinstance(source_node, ConditionNode):
                condition_output = self.context.node_outputs.get(str(source_node.id))
                if condition_output is None:
                    return False
                
                # Check which branch was taken based on the output
                # The condition node outputs either {"condtrue": data} or {"condfalse": data}
                condition_value = None
                if isinstance(condition_output.value, dict):
                    if "condtrue" in condition_output.value:
                        condition_value = True
                    elif "condfalse" in condition_output.value:
                        condition_value = False
                    else:
                        # Fallback: check metadata for condition_result
                        if condition_output.metadata and "condition_result" in condition_output.metadata:
                            condition_value = condition_output.metadata["condition_result"]
                
                if condition_value is None:
                    logger.debug(f"Node {node.id} not ready: condition output from {source_node.id} has no clear result")
                    return False
                
                # Check if this edge matches the condition result
                # The branch is determined by the source_output (condtrue/condfalse)
                branch = edge.source_output
                
                if branch == "condtrue" and not condition_value:
                    logger.debug(f"Node {node.id} not ready: edge from {source_node.id} is condtrue but condition is false")
                    return False
                if branch == "condfalse" and condition_value:
                    logger.debug(f"Node {node.id} not ready: edge from {source_node.id} is condfalse but condition is true")
                    return False
        
        return True
    
    def mark_node_running(self, node_id: NodeID) -> None:
        """Mark a node as running."""
        node_state = self.context.get_node_state(node_id) or NodeState(status=NodeExecutionStatus.PENDING)
        node_state.status = NodeExecutionStatus.RUNNING
        self.context.set_node_state(node_id, node_state)
        self.context.increment_execution_count(node_id)
        logger.debug(f"Node {node_id} marked as RUNNING, exec_count={self.context.get_node_execution_count(node_id)}")
    
    def mark_node_complete(self, node_id: NodeID, output: Any = None) -> None:
        """Mark a node as completed with optional output."""
        logger.debug(f"Node {node_id} marked as COMPLETED")
        self.context.complete_node(node_id, output)
        
        # Check if any downstream nodes should be reset
        self._reset_downstream_nodes_if_needed(node_id)
    
    def mark_node_failed(self, node_id: NodeID, error: str) -> None:
        """Mark a node as failed."""
        logger.debug(f"Node {node_id} marked as FAILED: {error}")
        node_state = self.context.get_node_state(node_id) or NodeState(status=NodeExecutionStatus.PENDING)
        node_state.status = NodeExecutionStatus.FAILED
        node_state.error = error
        self.context.set_node_state(node_id, node_state)
    
    def set_node_state(self, node_id: NodeID, status: NodeExecutionStatus) -> None:
        """Set node state directly."""
        node_state = self.context.get_node_state(node_id) or NodeState(status=NodeExecutionStatus.PENDING)
        node_state.status = status
        self.context.set_node_state(node_id, node_state)
    
    def set_node_output(self, node_id: NodeID, output: Any) -> None:
        """Set node output directly."""
        if output is not None:
            from dipeo.models import NodeOutput
            # Ensure it's a NodeOutput instance
            if not isinstance(output, NodeOutput):
                output = NodeOutput(node_id=node_id, value=output)
            self.context._execution_state.node_outputs[str(node_id)] = output
    
    def get_node_state(self, node_id: NodeID) -> NodeState | None:
        """Get node state."""
        return self.context.get_node_state(node_id)
    
    def get_node_execution_count(self, node_id: NodeID) -> int:
        """Get execution count for a node."""
        return self.context.get_node_execution_count(node_id)
    
    def is_complete(self) -> bool:
        """Check if execution is complete."""
        # Any pending nodes that could still run?
        for node in self.diagram.nodes:
            if self._is_node_ready(node):
                return False
        
        # Any nodes still running?
        for node in self.diagram.nodes:
            node_state = self.context.get_node_state(node.id)
            if node_state and node_state.status == NodeExecutionStatus.RUNNING:
                return False
        
        return True
    
    def get_node(self, node_id: NodeID) -> ExecutableNode | None:
        """Get a node by ID."""
        return next((n for n in self.diagram.nodes if n.id == node_id), None)
    
    def _reset_downstream_nodes_if_needed(self, node_id: NodeID) -> None:
        """Reset downstream nodes that were already executed if they're part of a loop."""
        # Find all edges from this node
        outgoing_edges = [e for e in self.diagram.edges if e.source_node_id == node_id]
        logger.debug(f"Checking {len(outgoing_edges)} downstream nodes from {node_id} for reset")
        
        # Track nodes we've reset to handle cascading resets
        nodes_to_reset = []
        
        for edge in outgoing_edges:
            target_node = self.get_node(edge.target_node_id)
            if not target_node:
                continue
            
            # Check if target was already executed
            target_state = self.context.get_node_state(target_node.id)
            if not target_state or target_state.status != NodeExecutionStatus.COMPLETED:
                continue
            
            # This is a potential loop - target was already executed
            logger.debug(f"Node {target_node.id} is downstream and already completed - checking if can reset")
            can_reset = True
            
            # Don't reset one-time nodes
            if isinstance(target_node, (StartNode, EndpointNode)):
                can_reset = False
                logger.debug(f"Node {target_node.id} cannot reset: one-time node")
            
            # For PersonJobNodes, check max_iteration
            if isinstance(target_node, PersonJobNode):
                exec_count = self.context.get_node_execution_count(target_node.id)
                if exec_count >= target_node.max_iteration:
                    can_reset = False
                    logger.debug(f"Node {target_node.id} cannot reset: reached max iterations ({exec_count}/{target_node.max_iteration})")
            
            # ConditionNodes should be allowed to reset for loops
            if isinstance(target_node, ConditionNode):
                logger.debug(f"Node {target_node.id} is a ConditionNode - allowing reset")
            
            if can_reset:
                nodes_to_reset.append(target_node.id)
        
        # Reset nodes and cascade to their downstream nodes
        for node_id_to_reset in nodes_to_reset:
            logger.debug(f"Resetting node {node_id_to_reset} to PENDING for loop execution")
            self.context.reset_node(node_id_to_reset)
            # Recursively reset downstream nodes
            self._reset_downstream_nodes_if_needed(node_id_to_reset)