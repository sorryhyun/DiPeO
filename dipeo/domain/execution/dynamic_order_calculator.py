"""Domain-level dynamic order calculator for execution flow.

This calculator determines node execution order based on runtime context,
handling loops, conditionals, and dynamic dependencies.
"""

from typing import Any, Optional
from collections import defaultdict

from dipeo.domain.diagram.models.executable_diagram import ExecutableDiagram, ExecutableNode
from dipeo.core.execution.dynamic_order_calculator import DynamicOrderCalculator as DynamicOrderCalculatorProtocol
from dipeo.core.execution.execution_context import ExecutionContext
from dipeo.diagram_generated import NodeID, NodeState, Status, NodeType


class DomainDynamicOrderCalculator(DynamicOrderCalculatorProtocol):
    """Domain implementation of dynamic order calculation.
    
    This calculator considers:
    - Current node states
    - Conditional branches taken
    - Loop iterations
    - Dynamic dependencies
    - Context-specific rules
    """
    
    def get_ready_nodes(
        self,
        diagram: ExecutableDiagram,
        node_states: dict[NodeID, NodeState],
        context: ExecutionContext
    ) -> list[ExecutableNode]:
        """Get nodes ready for execution based on current context."""
        ready_nodes = []
        
        for node in diagram.nodes:
            if self._is_node_ready(node, diagram, node_states, context):
                ready_nodes.append(node)
        
        # Sort by priority if needed
        return self._prioritize_nodes(ready_nodes, context)
    
    def get_blocked_nodes(
        self,
        diagram: ExecutableDiagram,
        node_states: dict[NodeID, NodeState],
        context: ExecutionContext
    ) -> list[ExecutableNode]:
        """Get nodes that are blocked from execution."""
        blocked = []
        
        for node in diagram.nodes:
            node_state = node_states.get(node.id)
            if not node_state:
                continue
                
            # Node is blocked if it's pending but not ready
            if node_state.status == Status.PENDING:
                if not self._is_node_ready(node, diagram, node_states, context):
                    blocked.append(node)
        
        return blocked
    
    def should_terminate(
        self,
        diagram: ExecutableDiagram,
        node_states: dict[NodeID, NodeState],
        context: ExecutionContext
    ) -> bool:
        """Check if execution should terminate early."""
        # Check for global termination conditions
        if context.get_metadata("terminate_execution"):
            return True
        
        # Check if all endpoints are reached
        endpoint_nodes = [n for n in diagram.nodes if n.type == NodeType.ENDPOINT]
        if endpoint_nodes:
            all_endpoints_complete = all(
                node_states.get(n.id, NodeState(status=Status.PENDING)).status 
                in [Status.COMPLETED, Status.SKIPPED]
                for n in endpoint_nodes
            )
            if all_endpoints_complete:
                return True
        
        return False
    
    def get_next_batch(
        self,
        diagram: ExecutableDiagram,
        node_states: dict[NodeID, NodeState],
        context: ExecutionContext,
        max_parallel: int = 10
    ) -> list[ExecutableNode]:
        """Get next batch of nodes to execute in parallel."""
        ready_nodes = self.get_ready_nodes(diagram, node_states, context)
        
        # Group by parallelization constraints
        batches = self._group_by_constraints(ready_nodes, context)
        
        # Return first batch up to max_parallel
        if batches:
            return batches[0][:max_parallel]
        
        return []
    
    def handle_loop_node(
        self,
        node: ExecutableNode,
        node_states: dict[NodeID, NodeState],
        context: ExecutionContext
    ) -> bool:
        """Handle special logic for loop nodes."""
        # Check if this is a PersonJob node (which can loop)
        if node.type == NodeType.PERSON_JOB:
            exec_count = context.get_node_execution_count(node.id)
            max_iter = getattr(node, 'max_iteration', 1)
            
            # Allow execution if under max iterations
            return exec_count < max_iter
        
        return True
    
    def resolve_conditional_dependencies(
        self,
        diagram: ExecutableDiagram,
        node_states: dict[NodeID, NodeState],
        context: ExecutionContext
    ) -> None:
        """Resolve dependencies based on conditional logic."""
        # Find all condition nodes that have completed
        for node in diagram.nodes:
            if node.type != NodeType.CONDITION:
                continue
                
            node_state = node_states.get(node.id)
            if not node_state or node_state.status != Status.COMPLETED:
                continue
            
            # Get the condition result
            output = context.get_node_output(node.id)
            if not output:
                continue
            
            # Mark appropriate branches based on condition result
            self._mark_conditional_branches(node, output, diagram, node_states, context)
    
    def get_execution_stats(
        self,
        node_states: dict[NodeID, NodeState]
    ) -> dict[str, Any]:
        """Get execution statistics."""
        stats = defaultdict(int)
        
        for state in node_states.values():
            stats[state.status.value] += 1
        
        total = len(node_states)
        completed = stats.get(Status.COMPLETED.value, 0)
        completed += stats.get(Status.MAXITER_REACHED.value, 0)
        
        return {
            "total_nodes": total,
            "completed": completed,
            "pending": stats.get(Status.PENDING.value, 0),
            "running": stats.get(Status.RUNNING.value, 0),
            "failed": stats.get(Status.FAILED.value, 0),
            "skipped": stats.get(Status.SKIPPED.value, 0),
            "progress_percentage": (completed / total * 100) if total > 0 else 0
        }
    
    def _is_node_ready(
        self,
        node: ExecutableNode,
        diagram: ExecutableDiagram,
        node_states: dict[NodeID, NodeState],
        context: ExecutionContext
    ) -> bool:
        """Check if a node is ready for execution."""
        node_state = node_states.get(node.id)
        if not node_state:
            return False
        
        # Skip if not pending
        if node_state.status != Status.PENDING:
            return False
        
        # Check loop constraints
        if not self.handle_loop_node(node, node_states, context):
            return False
        
        # Get incoming edges
        incoming_edges = [e for e in diagram.edges if e.target_node_id == node.id]
        
        # No dependencies - node is ready
        if not incoming_edges:
            return True
        
        # Check dependency satisfaction
        return self._check_dependencies(node, incoming_edges, node_states, context)
    
    def _check_dependencies(
        self,
        node: ExecutableNode,
        incoming_edges: list[Any],
        node_states: dict[NodeID, NodeState],
        context: ExecutionContext
    ) -> bool:
        """Check if node dependencies are satisfied."""
        # For nodes with multiple inputs (potential loops)
        if len(incoming_edges) > 1:
            # Check if this is a loop scenario
            has_loop_edge = any(
                self._is_loop_edge(edge, node, node_states)
                for edge in incoming_edges
            )
            
            if has_loop_edge:
                # For loops, require at least one dependency satisfied
                return any(
                    self._is_dependency_satisfied(edge, node_states)
                    for edge in incoming_edges
                )
        
        # For single input or non-loop cases, require all dependencies
        return all(
            self._is_dependency_satisfied(edge, node_states)
            for edge in incoming_edges
        )
    
    def _is_loop_edge(
        self,
        edge: Any,
        target_node: ExecutableNode,
        node_states: dict[NodeID, NodeState]
    ) -> bool:
        """Check if an edge is part of a loop."""
        # An edge is a loop edge if:
        # 1. It comes from a condition node
        # 2. The target has already executed
        source_state = node_states.get(edge.source_node_id)
        target_exec_count = 0  # We'd need context here for exec count
        
        # Simple heuristic: if source is a condition node
        # In a full implementation, we'd track loop metadata
        return edge.source_output == "condtrue" or edge.source_output == "condfalse"
    
    def _is_dependency_satisfied(
        self,
        edge: Any,
        node_states: dict[NodeID, NodeState]
    ) -> bool:
        """Check if a dependency edge is satisfied."""
        source_state = node_states.get(edge.source_node_id)
        if not source_state:
            return False
        
        # Dependency is satisfied if source is completed or reached max iterations
        return source_state.status in [
            Status.COMPLETED,
            Status.MAXITER_REACHED
        ]
    
    def _prioritize_nodes(
        self,
        nodes: list[ExecutableNode],
        context: ExecutionContext
    ) -> list[ExecutableNode]:
        """Prioritize nodes for execution order."""
        # Simple priority: START nodes first, then others
        def priority(node: ExecutableNode) -> int:
            if node.type == NodeType.START:
                return 0
            elif node.type == NodeType.CONDITION:
                return 1
            elif node.type == NodeType.PERSON_JOB:
                return 2
            else:
                return 3
        
        return sorted(nodes, key=priority)
    
    def _group_by_constraints(
        self,
        nodes: list[ExecutableNode],
        context: ExecutionContext
    ) -> list[list[ExecutableNode]]:
        """Group nodes by parallelization constraints."""
        # Simple implementation: all nodes in one batch
        # In a full implementation, we'd consider:
        # - Resource constraints
        # - Node interdependencies
        # - Execution policies
        return [nodes] if nodes else []
    
    def _mark_conditional_branches(
        self,
        condition_node: ExecutableNode,
        output: Any,
        diagram: ExecutableDiagram,
        node_states: dict[NodeID, NodeState],
        context: ExecutionContext
    ) -> None:
        """Mark conditional branches based on condition result."""
        # Get outgoing edges from condition node
        outgoing_edges = [
            e for e in diagram.edges 
            if e.source_node_id == condition_node.id
        ]
        
        # Determine which branch to take
        condition_result = output.value if hasattr(output, 'value') else output
        
        for edge in outgoing_edges:
            target_state = node_states.get(edge.target_node_id)
            if not target_state:
                continue
            
            # Skip nodes on false branch if condition is true
            if condition_result and edge.source_output == "condfalse":
                if target_state.status == Status.PENDING:
                    node_states[edge.target_node_id] = NodeState(
                        status=Status.SKIPPED
                    )
            # Skip nodes on true branch if condition is false
            elif not condition_result and edge.source_output == "condtrue":
                if target_state.status == Status.PENDING:
                    node_states[edge.target_node_id] = NodeState(
                        status=Status.SKIPPED
                    )