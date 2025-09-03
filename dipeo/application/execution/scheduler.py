"""Scheduler for managing node execution order with token-based tracking.

Phase 6: This module implements a token-driven scheduler where:
- Tokens are the primary scheduling mechanism
- Status (PENDING/RUNNING/COMPLETED) is maintained for UI visualization only
- Indegree is used solely for initial cold start ordering (e.g., Start nodes first)
- Nodes re-run automatically when new tokens arrive, no manual resets needed
"""

import asyncio
import logging
from collections import defaultdict
from typing import TYPE_CHECKING, Any, Set, Optional

from dipeo.diagram_generated import NodeID, Status
from dipeo.domain.diagram.models.executable_diagram import ExecutableDiagram, ExecutableNode
from dipeo.domain.execution.token_types import EdgeRef, JoinPolicy, ConcurrencyPolicy

if TYPE_CHECKING:
    from dipeo.application.execution.typed_execution_context import TypedExecutionContext
    from dipeo.domain.execution import DomainDynamicOrderCalculator

logger = logging.getLogger(__name__)


class NodeScheduler:
    """Manages node scheduling with indegree tracking and ready queue management.
    
    This scheduler extracts the scheduling complexity from TypedExecutionEngine,
    providing a clean interface for determining which nodes are ready to execute.
    Supports both traditional status-based and token-based scheduling.
    """
    
    def __init__(
        self, 
        diagram: ExecutableDiagram,
        order_calculator: "DomainDynamicOrderCalculator",
        context: Optional["TypedExecutionContext"] = None
    ):
        """Initialize the scheduler with a diagram.
        
        Args:
            diagram: The executable diagram to schedule
            order_calculator: Domain calculator for determining node readiness
            context: Optional execution context for token-based scheduling
        """
        self.diagram = diagram
        self.order_calculator = order_calculator
        self.context = context
        
        # Build dependency tracking structures
        self._indegree: dict[NodeID, int] = {}
        self._dependents: dict[NodeID, set[NodeID]] = defaultdict(set)
        self._ready_queue: asyncio.Queue[NodeID] = asyncio.Queue()
        self._processed_nodes: set[NodeID] = set()
        
        # Track high-priority edges to enforce sequential execution
        self._priority_dependencies: dict[NodeID, set[NodeID]] = defaultdict(set)
        
        # Token-aware scheduling structures
        self._ready_queue_by_epoch: dict[int, asyncio.Queue[NodeID]] = defaultdict(asyncio.Queue)
        self._armed_nodes: dict[tuple[NodeID, int], bool] = {}  # Track if node is armed (pending/running) for epoch
        self._running_nodes: dict[tuple[NodeID, int], bool] = {}  # Track if node is currently running for epoch
        
        # Join policies - default to 'all' for backward compatibility
        self._join_policies: dict[NodeID, JoinPolicy] = {}
        self._concurrency_policies: dict[NodeID, ConcurrencyPolicy] = {}
        
        self._initialize_dependencies()
        self._initialize_policies()
    
    def _is_conditional_edge(self, edge) -> bool:
        """Defensively check if an edge is conditional.
        
        Treats as conditional if either flag is set OR the source_output looks like a branch.
        """
        if getattr(edge, "is_conditional", False):
            return True
        return str(getattr(edge, "source_output", "")).lower() in ("condtrue", "condfalse")
    
    def _initialize_dependencies(self) -> None:
        """Initialize indegree counts for initial cold start ordering.
        
        Phase 6: Indegree is used ONLY for initial queue seeding (e.g., Start nodes first).
        After that, token flow drives all scheduling decisions.
        """
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
        
        # Phase 6: Initial cold start queue - nodes with indegree 0 (typically Start nodes)
        # This is ONLY for initial seeding; after that, tokens drive everything
        for node_id, count in self._indegree.items():
            if count == 0:
                # Seed the initial queue with nodes that have no dependencies
                self._ready_queue.put_nowait(node_id)
    
    def _initialize_policies(self) -> None:
        """Initialize join and concurrency policies for nodes."""
        from dipeo.diagram_generated import NodeType
        all_nodes = self.diagram.get_nodes_by_type(None) or self.diagram.nodes
        for node in all_nodes:
            # Extract join policy from node metadata or use default
            if hasattr(node, 'join_policy'):
                if isinstance(node.join_policy, str):
                    self._join_policies[node.id] = JoinPolicy(policy_type=node.join_policy)
                else:
                    self._join_policies[node.id] = node.join_policy
            else:
                # If condition node has skippable=true, use 'any' policy
                # This allows it to execute as soon as ANY input arrives
                if (hasattr(node, 'type') and node.type == NodeType.CONDITION and 
                    getattr(node, 'skippable', False)):
                    self._join_policies[node.id] = JoinPolicy(policy_type="any")
                else:
                    # Other nodes default to 'all' for backward compatibility
                    self._join_policies[node.id] = JoinPolicy(policy_type="all")
            
            # Extract concurrency policy from node metadata or use default
            if hasattr(node, 'concurrency_policy'):
                if isinstance(node.concurrency_policy, str):
                    self._concurrency_policies[node.id] = ConcurrencyPolicy(mode=node.concurrency_policy)
                else:
                    self._concurrency_policies[node.id] = node.concurrency_policy
            else:
                # Default to singleton for backward compatibility
                self._concurrency_policies[node.id] = ConcurrencyPolicy(mode="singleton")
    
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
    
    # DEPRECATED: reset_node() removed - tokens handle re-execution automatically
    
    # DEPRECATED: get_pending_nodes() removed - use token-based readiness instead
    
    def on_token_published(self, edge: EdgeRef, epoch: int) -> None:
        """Handle token publication event - Phase 2.1 of token migration.
        
        Called when a token is published on an edge. Checks if the target node 
        is ready and enqueues it if so. Maintains status for UI compatibility.
        
        Args:
            edge: The edge on which the token was published
            epoch: The epoch for which the token was published
        """
        if not self.context:
            return  # Skip if not in token mode
        
        target = edge.target_node_id
        
        # Check if the node has new inputs and can be armed
        if self.context.has_new_inputs(target, epoch) and self._can_arm(target, epoch):
            self._arm_and_enqueue(target, epoch)
    
    def _can_arm(self, node_id: NodeID, epoch: int) -> bool:
        """Check if a node can be armed for execution.
        
        Args:
            node_id: The node to check
            epoch: The epoch to check for
            
        Returns:
            True if the node can be armed (not already running/armed)
        """
        key = (node_id, epoch)
        
        # Check concurrency policy
        policy = self._concurrency_policies.get(node_id, ConcurrencyPolicy(mode="singleton"))
        
        # Count current running instances for this node
        running_count = sum(1 for (nid, ep), running in self._running_nodes.items() 
                          if nid == node_id and ep == epoch and running)
        
        # Use the policy's can_arm method
        return policy.can_arm(running_count)
    
    def _arm_and_enqueue(self, node_id: NodeID, epoch: int) -> None:
        """Arm a node and add it to the ready queue.
        
        Phase 6: Sets status for UI visualization only, not for scheduling logic.
        
        Args:
            node_id: The node to arm
            epoch: The epoch to arm for
        """
        key = (node_id, epoch)
        
        # Mark as armed to prevent duplicate enqueuing
        self._armed_nodes[key] = True
        
        # Phase 6: Status updates removed - UI status managed separately
        
        # Add to epoch-specific ready queue
        self._ready_queue_by_epoch[epoch].put_nowait(node_id)
        # Also add to main queue for backward compatibility
        self._ready_queue.put_nowait(node_id)
    
    def mark_node_running(self, node_id: NodeID, epoch: int) -> None:
        """Mark a node as running for concurrency tracking.
        
        Args:
            node_id: The node that started running
            epoch: The epoch it's running for
        """
        key = (node_id, epoch)
        self._running_nodes[key] = True
        # Clear armed state since it's now running
        self._armed_nodes.pop(key, None)
    
    def mark_node_complete(self, node_id: NodeID, epoch: int) -> None:
        """Mark a node as complete for concurrency tracking.
        
        Args:
            node_id: The node that completed
            epoch: The epoch it completed for
        """
        key = (node_id, epoch)
        self._running_nodes.pop(key, None)
        self._armed_nodes.pop(key, None)
    
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
            
            # Phase 6: Expose token-related methods for token-driven scheduling
            def has_new_inputs(self, node_id: NodeID, epoch: int) -> bool:
                """Check if node has new token inputs."""
                if hasattr(self._context, 'has_new_inputs'):
                    return self._context.has_new_inputs(node_id, epoch)
                return False
            
            def current_epoch(self) -> int:
                """Get the current execution epoch."""
                if hasattr(self._context, 'current_epoch'):
                    return self._context.current_epoch()
                return 0
            
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
        all_nodes_list = self.diagram.get_nodes_by_type(None) or self.diagram.nodes
        all_nodes = {node.id for node in all_nodes_list}
        pending_count = len(all_nodes - self._processed_nodes)
        return {
            "total_nodes": len(all_nodes_list),
            "processed_nodes": len(self._processed_nodes),
            "pending_nodes": pending_count,
            "ready_queue_size": self._ready_queue.qsize(),
            "nodes_with_dependencies": sum(1 for c in self._indegree.values() if c > 0)
        }