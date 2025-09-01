"""Domain-level dynamic order calculator for execution flow.

This calculator determines node execution order based on runtime context,
handling loops, conditionals, and dynamic dependencies.
"""

from typing import Any, Optional
from collections import defaultdict
import logging

from dipeo.domain.diagram.models.executable_diagram import ExecutableDiagram, ExecutableNode
from .execution_context import ExecutionContext
from dipeo.diagram_generated import NodeID, NodeState, Status, NodeType
from dipeo.diagram_generated.generated_nodes import ConditionNode

logger = logging.getLogger(__name__)


class DomainDynamicOrderCalculator:
    """Domain implementation of dynamic order calculation.
    
    This calculator considers:
    - Current node states
    - Conditional branches taken
    - Loop iterations
    - Dynamic dependencies
    - Context-specific rules
    """
    
    def __init__(self):
        """Initialize the dynamic order calculator with a reachability cache."""
        self._reachability_cache: dict[tuple[int, str, str], bool] = {}
    
    def _has_path(self, diagram: ExecutableDiagram, src_id: str, dst_id: str) -> bool:
        """Check if there's a path from src_id to dst_id in the diagram.
        
        Uses BFS to detect if dst_id is reachable from src_id.
        Results are cached for performance.
        
        Args:
            diagram: The executable diagram
            src_id: Source node ID
            dst_id: Destination node ID
            
        Returns:
            True if there's a path from src to dst, False otherwise
        """
        # Use object id for caching to avoid needing diagram.id
        key = (id(diagram), src_id, dst_id)
        if key in self._reachability_cache:
            return self._reachability_cache[key]
        
        # Build adjacency list
        adj = defaultdict(list)
        for edge in diagram.edges:
            adj[edge.source_node_id].append(edge.target_node_id)
        
        # BFS to find path
        seen = set()
        stack = [src_id]
        found = False
        
        while stack:
            node = stack.pop()
            if node == dst_id:
                found = True
                break
            if node in seen:
                continue
            seen.add(node)
            stack.extend(adj.get(node, []))
        
        self._reachability_cache[key] = found
        return found
    
    def _get_node_states_from_context(
        self,
        diagram: ExecutableDiagram,
        context: ExecutionContext
    ) -> dict[NodeID, NodeState]:
        """Extract node states from execution context."""
        # Use the new get_all_node_states method for clean access
        if hasattr(context, 'get_all_node_states'):
            all_states = context.get_all_node_states()
            node_states = {}
            for node in diagram.nodes:
                node_states[node.id] = all_states.get(node.id, NodeState(status=Status.PENDING))
            return node_states
        
        # Fallback for individual state queries (should not be needed with updated protocol)
        node_states = {}
        for node in diagram.nodes:
            state = context.get_node_state(node.id)
            if state:
                node_states[node.id] = state
            else:
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
        return self._check_dependencies(node, incoming_edges, node_states, context, diagram)
    
    def _check_dependencies(
        self,
        node: ExecutableNode,
        incoming_edges: list[Any],
        node_states: dict[NodeID, NodeState],
        context: ExecutionContext,
        diagram: ExecutableDiagram
    ) -> bool:
        """Check if node dependencies are satisfied.
        
        Rules:
        1. Condition nodes: Execute when ANY dependency is satisfied
        2. Other nodes: Execute when ALL active dependencies are satisfied
           with special handling for loop-back edges:
           - First execution: ignore loop-back edges (do-while semantics)
           - Subsequent executions: require active loop-back branch
        """
        # Rule 1: Condition nodes execute when ANY dependency is satisfied
        if node.type == NodeType.CONDITION:
            return any(
                self._is_dependency_satisfied(edge, node_states, context)
                for edge in incoming_edges
            )
        
        # Get execution count for loop handling
        exec_count = context.get_node_execution_count(node.id)
        # Rule 2: Other nodes need ALL active dependencies satisfied
        # Separate edges into conditional and non-conditional
        conditional_edges = []
        non_conditional_edges = []
        
        for edge in incoming_edges:
            if edge.source_output in ["condtrue", "condfalse"]:
                conditional_edges.append(edge)
            else:
                non_conditional_edges.append(edge)
        
        # Check non-conditional dependencies - ALL must be satisfied
        for edge in non_conditional_edges:
            if not self._is_dependency_satisfied(edge, node_states, context):
                logger.debug(f"Node {node.id}: Non-conditional dependency from {edge.source_node_id} not satisfied")
                return False
        
        # For conditional edges, classify into loop-back vs forward
        if conditional_edges:
            loop_back_edges = []
            forward_cond_edges = []
            
            for edge in conditional_edges:
                # An edge is a loop-back if target can reach the source (forms a cycle)
                if self._has_path(diagram, node.id, edge.source_node_id):
                    loop_back_edges.append(edge)
                else:
                    forward_cond_edges.append(edge)

            # Check forward conditional edges - these must always be satisfied
            if forward_cond_edges:
                edges_by_condition = defaultdict(list)
                for edge in forward_cond_edges:
                    edges_by_condition[edge.source_node_id].append(edge)
                
                for condition_node_id, edges in edges_by_condition.items():
                    source_state = node_states.get(condition_node_id)
                    
                    # If condition node hasn't executed yet, node is not ready
                    if not source_state or source_state.status == Status.PENDING:
                        return False
                    
                    # Check if we're on the active branch
                    if not any(self._is_dependency_satisfied(edge, node_states, context) 
                              for edge in edges):
                        return False
            
            # Check loop-back edges - special handling based on execution count
            if loop_back_edges:
                if exec_count == 0:
                    # First execution: ignore loop-back edges (do-while semantics)
                    logger.debug(f"Node {node.id}: First execution (count={exec_count}), ignoring {len(loop_back_edges)} loop-back edges")
                else:
                    # Subsequent executions: require active loop-back branch
                    edges_by_condition = defaultdict(list)
                    for edge in loop_back_edges:
                        edges_by_condition[edge.source_node_id].append(edge)
                    
                    for condition_node_id, edges in edges_by_condition.items():
                        source_state = node_states.get(condition_node_id)
                        
                        # If condition hasn't re-run in this iteration, can't continue loop
                        if not source_state or source_state.status == Status.PENDING:
                            logger.debug(f"Node {node.id}: Loop condition {condition_node_id} not ready for iteration {exec_count}")
                            return False
                        
                        # Check if loop-back branch is active
                        if not any(self._is_dependency_satisfied(edge, node_states, context) 
                                  for edge in edges):
                            logger.debug(f"Node {node.id}: Loop-back from {condition_node_id} not active")
                            return False
        
        # All dependencies satisfied
        return True
    
    def _check_dependencies_fallback(
        self,
        node: ExecutableNode,
        conditional_edges: list[Any],
        node_states: dict[NodeID, NodeState],
        context: ExecutionContext
    ) -> bool:
        """Fallback dependency checking when diagram is not available."""
        # Use the original logic when we can't determine loop-backs
        edges_by_condition = {}
        for edge in conditional_edges:
            if edge.source_node_id not in edges_by_condition:
                edges_by_condition[edge.source_node_id] = []
            edges_by_condition[edge.source_node_id].append(edge)
        
        for condition_node_id, edges in edges_by_condition.items():
            source_state = node_states.get(condition_node_id)
            
            if not source_state or source_state.status == Status.PENDING:
                return False
            
            if not any(self._is_dependency_satisfied(edge, node_states, context) 
                      for edge in edges):
                return False
        
        return True
    
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
                # (A) Preferred: read from global variables
                active_branch = None
                if hasattr(context, "get_variable"):
                    active_branch = context.get_variable(f"branch[{edge.source_node_id}]")
                
                # (B) Fallback: check the output envelope
                if not active_branch:
                    output = context.get_node_output(edge.source_node_id)
                    from dipeo.domain.execution.envelope import Envelope
                    if isinstance(output, Envelope):
                        # Check the body for result
                        if isinstance(output.body, dict) and "result" in output.body:
                            active_branch = "condtrue" if bool(output.body["result"]) else "condfalse"
                    elif hasattr(output, 'value') and isinstance(output.value, bool):
                        # Handle boolean outputs
                        active_branch = "condtrue" if output.value else "condfalse"
                
                if not active_branch:
                    # Default safe branch
                    active_branch = "condfalse"
                
                # Only satisfied if this edge is on the active branch
                return edge.source_output == active_branch
            # If no context, can't verify branch - consider not satisfied
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