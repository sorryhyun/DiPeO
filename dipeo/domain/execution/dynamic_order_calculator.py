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
from dipeo.diagram_generated.generated_nodes import ConditionNode


class DomainDynamicOrderCalculator(DynamicOrderCalculatorProtocol):
    """Domain implementation of dynamic order calculation.
    
    This calculator considers:
    - Current node states
    - Conditional branches taken
    - Loop iterations
    - Dynamic dependencies
    - Context-specific rules
    """
    
    def _get_node_states_from_context(
        self,
        diagram: ExecutableDiagram,
        context: ExecutionContext
    ) -> dict[NodeID, NodeState]:
        """Extract node states from execution context."""
        node_states = {}
        for node in diagram.nodes:
            # Try different ways to get node state from context
            if hasattr(context, 'get_node_state'):
                state = context.get_node_state(node.id)
                if state:
                    node_states[node.id] = state
                else:
                    node_states[node.id] = NodeState(status=Status.PENDING)
            elif hasattr(context, '_node_states'):
                node_states[node.id] = context._node_states.get(node.id, NodeState(status=Status.PENDING))
            else:
                # Fallback to pending if context doesn't provide state
                node_states[node.id] = NodeState(status=Status.PENDING)
        return node_states
    
    def get_ready_nodes(
        self,
        diagram: ExecutableDiagram,
        context: ExecutionContext
    ) -> list[ExecutableNode]:
        """Get nodes ready for execution based on current context."""
        node_states = self._get_node_states_from_context(diagram, context)
        ready_nodes = []
        
        for node in diagram.nodes:
            if self._is_node_ready(node, diagram, node_states, context):
                ready_nodes.append(node)
        
        # Sort by priority if needed
        return self._prioritize_nodes(ready_nodes, context)
    
    def get_blocked_nodes(
        self,
        diagram: ExecutableDiagram,
        context: ExecutionContext
    ) -> list[tuple[NodeID, str]]:
        """Get nodes that are blocked from execution."""
        node_states = self._get_node_states_from_context(diagram, context)
        blocked = []
        
        for node in diagram.nodes:
            node_state = node_states.get(node.id)
            if not node_state:
                continue
                
            # Node is blocked if it's pending but not ready
            if node_state.status == Status.PENDING:
                if not self._is_node_ready(node, diagram, node_states, context):
                    blocked.append((node.id, "Failed dependencies"))
        
        return blocked
    
    def should_terminate(
        self,
        diagram: ExecutableDiagram,
        context: ExecutionContext
    ) -> bool:
        """Check if execution should terminate early."""
        node_states = self._get_node_states_from_context(diagram, context)
        
        # Check for global termination conditions
        if hasattr(context, 'get_metadata') and context.get_metadata("terminate_execution"):
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
        context: ExecutionContext,
        max_parallel: int = 10
    ) -> list[ExecutableNode]:
        """Get next batch of nodes to execute in parallel."""
        ready_nodes = self.get_ready_nodes(diagram, context)
        
        # Group by parallelization constraints
        batches = self._group_by_constraints(ready_nodes, context)
        
        # Return first batch up to max_parallel
        if batches:
            return batches[0][:max_parallel]
        
        return []
    
    def handle_loop_node(
        self,
        node: ExecutableNode,
        diagram: ExecutableDiagram,
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
        node: ExecutableNode,
        diagram: ExecutableDiagram,
        context: ExecutionContext
    ) -> bool:
        """Check if conditional dependencies for a node are satisfied."""
        node_states = self._get_node_states_from_context(diagram, context)
        
        # Get incoming edges for this node
        incoming_edges = [e for e in diagram.edges if e.target_node_id == node.id]
        
        # Check if all conditional dependencies are satisfied
        for edge in incoming_edges:
            # If edge is from a condition node, check if branch is active
            if edge.source_output in ["condtrue", "condfalse"]:
                if not self._is_dependency_satisfied(edge, node_states, context):
                    return False
        
        return True
    
    def _resolve_all_conditional_dependencies(
        self,
        diagram: ExecutableDiagram,
        node_states: dict[NodeID, NodeState],
        context: ExecutionContext
    ) -> None:
        """Internal: Resolve dependencies based on conditional logic."""
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
        diagram: ExecutableDiagram,
        context: ExecutionContext
    ) -> dict[str, Any]:
        """Get execution statistics."""
        node_states = self._get_node_states_from_context(diagram, context)
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
        if not self.handle_loop_node(node, diagram, context):
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
            # Check if any edge is from a condition node (potential loop edge)
            has_conditional_edge = any(
                edge.source_output in ["condtrue", "condfalse"]
                for edge in incoming_edges
            )
            
            if has_conditional_edge:
                # Get the node's execution count
                target_exec_count = context.get_node_execution_count(node.id) if context else 0
                
                if target_exec_count == 0:
                    # First execution: only require non-conditional edges to be satisfied
                    # This allows nodes to start when their initial inputs are ready,
                    # without waiting for loop conditions that haven't been evaluated yet
                    non_conditional_edges = [
                        edge for edge in incoming_edges 
                        if edge.source_output not in ["condtrue", "condfalse"]
                    ]
                    if non_conditional_edges:
                        return all(
                            self._is_dependency_satisfied(edge, node_states, context)
                            for edge in non_conditional_edges
                        )
                else:
                    # Subsequent executions: require at least one dependency (loop logic)
                    return any(
                        self._is_dependency_satisfied(edge, node_states, context)
                        for edge in incoming_edges
                    )
        
        # For single input or non-loop cases, require all dependencies
        return all(
            self._is_dependency_satisfied(edge, node_states, context)
            for edge in incoming_edges
        )
    
    def _is_loop_edge(
        self,
        edge: Any,
        target_node: ExecutableNode,
        node_states: dict[NodeID, NodeState],
        context: ExecutionContext
    ) -> bool:
        """Check if an edge is part of a loop."""
        # An edge is a loop edge if:
        # 1. It comes from a condition node
        # 2. The target has already executed
        source_state = node_states.get(edge.source_node_id)
        target_exec_count = context.get_node_execution_count(target_node.id) if context else 0
        
        # Edge is a loop edge if it's from a condition node and target has executed
        if edge.source_output in ["condtrue", "condfalse"]:
            return target_exec_count > 0
        
        return False
    
    def _is_dependency_satisfied(
        self,
        edge: Any,
        node_states: dict[NodeID, NodeState],
        context: ExecutionContext = None
    ) -> bool:
        """Check if a dependency edge is satisfied."""
        source_state = node_states.get(edge.source_node_id)
        if not source_state:
            return False
        
        # Check if source is completed or reached max iterations
        if source_state.status not in [Status.COMPLETED, Status.MAXITER_REACHED]:
            return False
        
        # For edges from condition nodes, check if the branch is active
        if edge.source_output in ["condtrue", "condfalse"]:
            if context:
                output = context.get_node_output(edge.source_node_id)
                # Check for Envelope with condition result
                from dipeo.core.execution.envelope import Envelope
                if isinstance(output, Envelope) and output.content_type == "condition_result":
                    # Use active_branch from metadata
                    active_branch = output.meta.get("active_branch", "condfalse")
                    # Only satisfied if this edge is on the active branch
                    return edge.source_output == active_branch
                elif hasattr(output, 'value') and isinstance(output.value, bool):
                    # Handle boolean outputs
                    active_branch = "condtrue" if output.value else "condfalse"
                    return edge.source_output == active_branch
            # If no context or output, can't verify branch - consider not satisfied
            return False
        
        # For non-condition edges, source completion is enough
        return True
    
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