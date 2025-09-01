"""Scheduler for managing node execution order with indegree tracking.

This module implements a dedicated scheduler that tracks node dependencies 
and maintains a ready queue for efficient execution ordering.
"""

import asyncio
import logging
from collections import defaultdict
from typing import TYPE_CHECKING, Any, Set

from dipeo.diagram_generated import NodeID, Status
from dipeo.domain.diagram.models.executable_diagram import ExecutableDiagram, ExecutableNode

if TYPE_CHECKING:
    from dipeo.application.execution.typed_execution_context import TypedExecutionContext
    from dipeo.domain.execution import DomainDynamicOrderCalculator

logger = logging.getLogger(__name__)


class NodeScheduler:
    """Manages node scheduling with indegree tracking and ready queue management.
    
    This scheduler extracts the scheduling complexity from TypedExecutionEngine,
    providing a clean interface for determining which nodes are ready to execute.
    """
    
    def __init__(
        self, 
        diagram: ExecutableDiagram,
        order_calculator: "DomainDynamicOrderCalculator"
    ):
        """Initialize the scheduler with a diagram.
        
        Args:
            diagram: The executable diagram to schedule
            order_calculator: Domain calculator for determining node readiness
        """
        self.diagram = diagram
        self.order_calculator = order_calculator
        
        # Build dependency tracking structures
        self._indegree: dict[NodeID, int] = {}
        self._dependents: dict[NodeID, set[NodeID]] = defaultdict(set)
        self._ready_queue: asyncio.Queue[NodeID] = asyncio.Queue()
        self._processed_nodes: set[NodeID] = set()
        
        self._initialize_dependencies()
    
    def _initialize_dependencies(self) -> None:
        """Initialize indegree counts and dependency mappings."""
        # Initialize all nodes with 0 indegree
        for node in self.diagram.nodes:
            self._indegree[node.id] = 0
        
        # Build dependency graph
        for edge in self.diagram.edges:
            # Skip conditional edges (like condition branches)
            if edge.is_conditional:
                continue
            
            self._indegree[edge.target_node_id] += 1
            self._dependents[edge.source_node_id].add(edge.target_node_id)
        
        # Queue nodes with no dependencies
        for node_id, count in self._indegree.items():
            if count == 0:
                self._ready_queue.put_nowait(node_id)
    
    async def get_ready_nodes(self, context: "TypedExecutionContext") -> list[ExecutableNode]:
        """Get nodes that are ready to execute.
        
        This method uses the order calculator to determine readiness,
        taking into account condition branches, loops, and other domain logic.
        
        Args:
            context: The current execution context
            
        Returns:
            List of nodes ready to execute
        """
        # Build context wrapper for order calculator
        calc_context = self._create_calculator_context(context)
        
        # Use domain order calculator to get truly ready nodes
        ready_nodes = self.order_calculator.get_ready_nodes(
            diagram=self.diagram,
            context=calc_context  # type: ignore
        )
        
        return ready_nodes
    
    def mark_node_completed(self, node_id: NodeID, context: "TypedExecutionContext") -> Set[NodeID]:
        """Mark a node as completed and update dependencies.
        
        Args:
            node_id: The node that completed
            context: The current execution context
            
        Returns:
            Set of node IDs that became ready after this completion
        """
        if node_id in self._processed_nodes:
            return set()
        
        self._processed_nodes.add(node_id)
        newly_ready = set()
        
        # Decrement indegree for all dependents
        for dependent_id in self._dependents.get(node_id, set()):
            self._indegree[dependent_id] -= 1
            
            # If indegree reaches 0, node is potentially ready
            # (still needs domain validation via order calculator)
            if self._indegree[dependent_id] == 0:
                newly_ready.add(dependent_id)
                self._ready_queue.put_nowait(dependent_id)
        
        return newly_ready
    
    def reset_node(self, node_id: NodeID) -> None:
        """Reset a node for re-execution (used for loops).
        
        Args:
            node_id: The node to reset
        """
        if node_id in self._processed_nodes:
            self._processed_nodes.remove(node_id)
            
        # Recalculate indegree for this node
        incoming_count = sum(
            1 for edge in self.diagram.edges 
            if edge.target_node_id == node_id and not edge.is_conditional
        )
        self._indegree[node_id] = incoming_count
    
    def get_pending_nodes(self) -> list[NodeID]:
        """Get all nodes that haven't been processed yet.
        
        Returns:
            List of unprocessed node IDs
        """
        all_nodes = {node.id for node in self.diagram.nodes}
        return list(all_nodes - self._processed_nodes)
    
    def _create_calculator_context(self, context: "TypedExecutionContext") -> Any:
        """Create a context wrapper for the order calculator.
        
        Args:
            context: The execution context
            
        Returns:
            Context wrapper for order calculator
        """
        node_outputs = {}
        node_exec_counts = {}
        
        for node_id in context.get_completed_nodes():
            output = context.get_node_output(node_id)
            if output:
                node_outputs[str(node_id)] = output
            node_exec_counts[str(node_id)] = context.get_node_execution_count(node_id)
        
        class OrderCalculatorContext:
            """Minimal context wrapper for order calculator."""
            
            def __init__(self, ctx: "TypedExecutionContext", outputs: dict, counts: dict):
                self._context = ctx
                self._node_outputs = outputs
                self._node_exec_counts = counts
            
            def get_metadata(self, key: str) -> Any:
                return self._context.get_execution_metadata().get(key)
            
            def get_variable(self, name: str) -> Any:
                return self._context.get_variable(name)
            
            def get_node_output(self, node_id: str | NodeID) -> Any:
                return self._node_outputs.get(str(node_id))
            
            def get_node_execution_count(self, node_id: str | NodeID) -> int:
                return self._node_exec_counts.get(str(node_id), 0)
            
            def is_first_execution(self, node_id: str | NodeID) -> bool:
                return self.get_node_execution_count(node_id) <= 1
            
            def get_node_state(self, node_id: str | NodeID) -> Any:
                return self._context.get_node_state(node_id)
            
            @property
            def current_node_id(self) -> NodeID | None:
                return self._context.current_node_id
            
            @property
            def execution_id(self) -> str:
                return self._context.execution_id
            
            @property
            def diagram_id(self) -> str:
                return self._context.diagram_id
        
        return OrderCalculatorContext(context, node_outputs, node_exec_counts)
    
    def get_execution_stats(self) -> dict[str, Any]:
        """Get statistics about the scheduling state.
        
        Returns:
            Dictionary with scheduling statistics
        """
        return {
            "total_nodes": len(self.diagram.nodes),
            "processed_nodes": len(self._processed_nodes),
            "pending_nodes": len(self.get_pending_nodes()),
            "ready_queue_size": self._ready_queue.qsize(),
            "nodes_with_dependencies": sum(1 for c in self._indegree.values() if c > 0)
        }