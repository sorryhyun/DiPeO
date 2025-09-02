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
        
        # Track high-priority edges to enforce sequential execution
        self._priority_dependencies: dict[NodeID, set[NodeID]] = defaultdict(set)
        
        self._initialize_dependencies()
    
    def _is_conditional_edge(self, edge) -> bool:
        """Defensively check if an edge is conditional.
        
        Treats as conditional if either flag is set OR the source_output looks like a branch.
        """
        if getattr(edge, "is_conditional", False):
            return True
        return str(getattr(edge, "source_output", "")).lower() in ("condtrue", "condfalse")
    
    def _initialize_dependencies(self) -> None:
        """Initialize indegree counts and dependency mappings."""
        # Initialize all nodes with 0 indegree
        all_nodes = self.diagram.get_nodes_by_type(None) or self.diagram.nodes
        for node in all_nodes:
            self._indegree[node.id] = 0
        
        # Track incoming edges for each node
        nodes_with_non_conditional_deps: set[NodeID] = set()
        incoming_by_target: dict[NodeID, list] = defaultdict(list)
        
        # Build dependency graph and priority relationships
        edges_by_source: dict[NodeID, list] = defaultdict(list)
        all_edges = []
        for node in all_nodes:
            for edge in self.diagram.get_outgoing_edges(node.id):
                edges_by_source[edge.source_node_id].append(edge)
                incoming_by_target[edge.target_node_id].append(edge)
                all_edges.append(edge)
        
        # Process all edges for indegree calculation
        for edge in all_edges:
            # Skip conditional edges (like condition branches) - use defensive check
            if self._is_conditional_edge(edge):
                continue
            self._indegree[edge.target_node_id] += 1
            self._dependents[edge.source_node_id].add(edge.target_node_id)
            nodes_with_non_conditional_deps.add(edge.target_node_id)
        
        # Build priority dependencies: nodes with lower priority must wait for higher priority siblings
        for source_id, edges in edges_by_source.items():
            # Sort edges by priority (higher priority first)
            sorted_edges = sorted(edges, key=lambda e: -getattr(e, 'execution_priority', 0))
            
            # Each lower priority edge depends on all higher priority edges from same source
            for i, lower_edge in enumerate(sorted_edges):
                for higher_edge in sorted_edges[:i]:
                    if getattr(higher_edge, 'execution_priority', 0) > getattr(lower_edge, 'execution_priority', 0):
                        # Lower priority target must wait for higher priority target
                        self._priority_dependencies[lower_edge.target_node_id].add(higher_edge.target_node_id)
        
        # Initial ready queue: nodes with indegree 0 AND not waiting for conditional branches
        for node_id, count in self._indegree.items():
            if count == 0:
                # Otherwise, it's truly ready (no dependencies or has non-conditional deps satisfied)
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
            
        # Recalculate indegree for this node using defensive check
        incoming_edges = self.diagram.get_incoming_edges(node_id)
        incoming_count = sum(
            1 for edge in incoming_edges
            if not self._is_conditional_edge(edge)
        )
        self._indegree[node_id] = incoming_count
    
    def get_pending_nodes(self) -> list[NodeID]:
        """Get all nodes that haven't been processed yet.
        
        Returns:
            List of unprocessed node IDs
        """
        all_nodes_list = self.diagram.get_nodes_by_type(None) or self.diagram.nodes
        all_nodes = {node.id for node in all_nodes_list}
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
        
        # Get outputs for completed nodes
        for node_id in context.get_completed_nodes():
            output = context.get_node_output(node_id)
            if output:
                node_outputs[str(node_id)] = output
        
        # Get execution counts for ALL nodes (including reset/pending ones)
        # This is crucial for loop handling where nodes are reset but maintain their count
        all_nodes_for_counts = self.diagram.get_nodes_by_type(None) or self.diagram.nodes
        for node in all_nodes_for_counts:
            count = context.get_node_execution_count(node.id)
            if count > 0:  # Only store non-zero counts for efficiency
                node_exec_counts[str(node.id)] = count
        
        class OrderCalculatorContext:
            """Minimal context wrapper for order calculator."""
            
            def __init__(self, ctx: "TypedExecutionContext", outputs: dict, counts: dict, diagram):
                self._context = ctx
                self._node_outputs = outputs
                self._node_exec_counts = counts
                self.diagram = diagram  # Add diagram for loop detection
            
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
        
        return OrderCalculatorContext(context, node_outputs, node_exec_counts, self.diagram)
    
    def get_execution_stats(self) -> dict[str, Any]:
        """Get statistics about the scheduling state.
        
        Returns:
            Dictionary with scheduling statistics
        """
        return {
            "total_nodes": len(self.diagram.get_nodes_by_type(None) or self.diagram.nodes),
            "processed_nodes": len(self._processed_nodes),
            "pending_nodes": len(self.get_pending_nodes()),
            "ready_queue_size": self._ready_queue.qsize(),
            "nodes_with_dependencies": sum(1 for c in self._indegree.values() if c > 0)
        }