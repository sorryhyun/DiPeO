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
from typing import TYPE_CHECKING, Any, Optional

from dipeo.diagram_generated import NodeID, NodeType, Status
from dipeo.domain.diagram.models.executable_diagram import ExecutableDiagram, ExecutableNode
from dipeo.domain.execution.token_types import ConcurrencyPolicy, EdgeRef, JoinPolicy

if TYPE_CHECKING:
    from dipeo.application.execution.typed_execution_context import TypedExecutionContext

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
        context: Optional["TypedExecutionContext"] = None,
    ):
        """Initialize the scheduler with a diagram.

        Args:
            diagram: The executable diagram to schedule
            context: Optional execution context for token-based scheduling
        """
        self.diagram = diagram
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
        self._armed_nodes: dict[
            tuple[NodeID, int], bool
        ] = {}  # Track if node is armed (pending/running) for epoch
        self._running_nodes: dict[
            tuple[NodeID, int], bool
        ] = {}  # Track if node is currently running for epoch

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
            # Check if this edge is from a skippable condition node
            source_node = next((n for n in all_nodes if n.id == edge.source_node_id), None)
            if (
                source_node
                and hasattr(source_node, "type")
                and source_node.type == NodeType.CONDITION
                and getattr(source_node, "skippable", False)
            ):
                # Only skip edges from skippable conditions if the target has alternative paths
                # (more than 1 incoming edge from different sources)
                target_incoming_edges = incoming_by_target.get(edge.target_node_id, [])
                unique_sources = set(e.source_node_id for e in target_incoming_edges)

                if len(unique_sources) > 1:
                    # Target has multiple sources - can skip this skippable condition edge
                    logger.debug(
                        f"Skipping edge from skippable condition {edge.source_node_id} -> {edge.target_node_id} (target has {len(unique_sources)} sources)"
                    )
                    continue
                else:
                    # Target only has this source - cannot skip even if skippable
                    logger.debug(
                        f"Not skipping edge from skippable condition {edge.source_node_id} -> {edge.target_node_id} (only source)"
                    )

            # For non-skippable conditions, still skip conditional edges
            if self._is_conditional_edge(edge):
                continue

            self._indegree[edge.target_node_id] += 1
            self._dependents[edge.source_node_id].add(edge.target_node_id)
            nodes_with_non_conditional_deps.add(edge.target_node_id)

        # Build priority dependencies: nodes with lower priority must wait for higher priority siblings
        for _source_id, edges in edges_by_source.items():
            # Sort edges by priority (higher priority first)
            sorted_edges = sorted(edges, key=lambda e: -getattr(e, "execution_priority", 0))

            # Each lower priority edge depends on all higher priority edges from same source
            for i, lower_edge in enumerate(sorted_edges):
                for higher_edge in sorted_edges[:i]:
                    if getattr(higher_edge, "execution_priority", 0) > getattr(
                        lower_edge, "execution_priority", 0
                    ):
                        # Lower priority target must wait for higher priority target
                        self._priority_dependencies[lower_edge.target_node_id].add(
                            higher_edge.target_node_id
                        )

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
            # First, check if node has a compiled join_policy field
            if hasattr(node, "join_policy") and node.join_policy is not None:
                # Use the compiled policy from the node
                if isinstance(node.join_policy, str):
                    self._join_policies[node.id] = JoinPolicy(policy_type=node.join_policy)
                else:
                    self._join_policies[node.id] = node.join_policy
            else:
                # Fallback: Type-derived defaults for backward compatibility
                # Condition nodes are OR-joins ("any"), others are AND-joins ("all")
                if hasattr(node, "type") and node.type == NodeType.CONDITION:
                    self._join_policies[node.id] = JoinPolicy(policy_type="any")
                else:
                    self._join_policies[node.id] = JoinPolicy(policy_type="all")

            # Extract concurrency policy from node metadata or use default
            if hasattr(node, "concurrency_policy"):
                if isinstance(node.concurrency_policy, str):
                    self._concurrency_policies[node.id] = ConcurrencyPolicy(
                        mode=node.concurrency_policy
                    )
                else:
                    self._concurrency_policies[node.id] = node.concurrency_policy
            else:
                # Default to singleton for backward compatibility
                self._concurrency_policies[node.id] = ConcurrencyPolicy(mode="singleton")

    async def get_ready_nodes(self, context: "TypedExecutionContext") -> list[ExecutableNode]:
        """Get nodes that are ready to execute.

        This method determines node readiness based on tokens,
        taking into account condition branches, loops, and other domain logic.

        Args:
            context: The current execution context

        Returns:
            List of nodes ready to execute
        """
        ready_nodes = []
        all_nodes = self.diagram.get_nodes_by_type(None) or self.diagram.nodes

        for node in all_nodes:
            if self._is_node_ready(node, context):
                ready_nodes.append(node)

        # Sort by priority
        return self._prioritize_nodes(ready_nodes)

    def mark_node_completed(self, node_id: NodeID, context: "TypedExecutionContext") -> set[NodeID]:
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
        has_inputs = self.context.has_new_inputs(target, epoch)
        can_arm = self._can_arm(target, epoch)

        if has_inputs and can_arm:
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

        # Check if already armed (pending execution)
        if self._armed_nodes.get(key, False):
            return False  # Already armed, waiting to execute

        # Check concurrency policy
        policy = self._concurrency_policies.get(node_id, ConcurrencyPolicy(mode="singleton"))

        # Count current running instances for this node
        running_count = sum(
            1
            for (nid, ep), running in self._running_nodes.items()
            if nid == node_id and ep == epoch and running
        )

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

    def _is_node_ready(
        self,
        node: ExecutableNode,
        context: "TypedExecutionContext",
    ) -> bool:
        """Check if a node is ready for execution - Phase 6 token-driven version.

        Tokens are the primary scheduling mechanism. Status is kept for UI only.
        A node is ready when it has new token inputs and dependencies are satisfied.
        """
        # START nodes should only execute once per epoch
        if node.type == NodeType.START and not self.diagram.get_incoming_edges(node.id):
            # Run once per epoch; rely on execution count (tracker), not UI status
            return context.state.get_node_execution_count(node.id) == 0

        # Token-based readiness check (Phase 6 - tokens are primary)
        if hasattr(context, "has_new_inputs") and hasattr(context, "current_epoch"):
            epoch = context.current_epoch()

            # Check if node has tokens from dependencies
            incoming_edges = self.diagram.get_incoming_edges(node.id)
            if not incoming_edges:
                # Source nodes are always ready
                return True

            # has_new_inputs already handles skippable conditions correctly
            # by excluding them from join policy requirements
            has_tokens = context.has_new_inputs(node.id, epoch)

            # Standard readiness check
            if has_tokens:
                # Node has tokens - check other constraints
                if not self._handle_loop_node(node, context):
                    return False
                return not self._has_pending_higher_priority_siblings(node, context)
            else:
                # No tokens = not ready
                return False

        # Fallback for systems without token support (should not happen in Phase 6)
        logger.warning(
            f"Node {node.id} readiness check without token context - this should not happen in Phase 6"
        )
        return False

    def _handle_loop_node(self, node: ExecutableNode, context: "TypedExecutionContext") -> bool:
        """Handle special logic for loop nodes."""
        # Check if this is a PersonJob node (which can loop)
        if node.type == NodeType.PERSON_JOB:
            exec_count = context.state.get_node_execution_count(node.id)
            max_iter = getattr(node, "max_iteration", 1)

            # Allow execution if under max iterations
            return exec_count < max_iter

        return True

    def _has_pending_higher_priority_siblings(
        self, node: ExecutableNode, context: "TypedExecutionContext"
    ) -> bool:
        """Check if node has higher priority siblings that haven't executed yet.

        Phase 6: Uses completion status rather than PENDING to determine if siblings have run.
        Returns True if this node should wait for higher priority siblings to complete.
        """
        # Find all edges pointing to this node
        incoming_edges = self.diagram.get_incoming_edges(node.id)
        if not incoming_edges:
            return False

        # For each incoming edge, check siblings from the same source
        for incoming_edge in incoming_edges:
            source_node_id = incoming_edge.source_node_id
            my_priority = getattr(incoming_edge, "execution_priority", 0)

            # Find all sibling edges (edges from same source)
            sibling_edges = self.diagram.get_outgoing_edges(source_node_id)

            # Check if any higher priority siblings haven't completed yet
            for sibling_edge in sibling_edges:
                if sibling_edge.target_node_id == node.id:
                    continue  # Skip self

                sibling_priority = getattr(sibling_edge, "execution_priority", 0)

                # If sibling has higher priority and hasn't completed, we must wait
                if sibling_priority > my_priority:
                    sibling_state = context.state.get_node_state(sibling_edge.target_node_id)
                    # Phase 6: Check if sibling has NOT completed (rather than checking PENDING)
                    if not sibling_state or sibling_state.status not in [
                        Status.COMPLETED,
                        Status.FAILED,
                        Status.SKIPPED,
                        Status.MAXITER_REACHED,
                    ]:
                        return True

        return False

    def _prioritize_nodes(self, nodes: list[ExecutableNode]) -> list[ExecutableNode]:
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
            "nodes_with_dependencies": sum(1 for c in self._indegree.values() if c > 0),
        }
