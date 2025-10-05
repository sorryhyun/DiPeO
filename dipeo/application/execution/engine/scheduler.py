"""Scheduler for managing node execution order with token-based tracking."""

from typing import TYPE_CHECKING, Any, Optional

from dipeo.application.execution.engine.dependency_tracker import DependencyTracker
from dipeo.application.execution.engine.ready_queue import ReadyQueue
from dipeo.config.base_logger import get_module_logger
from dipeo.diagram_generated import NodeID, NodeType, Status
from dipeo.domain.diagram.models.executable_diagram import ExecutableDiagram, ExecutableNode
from dipeo.domain.execution.token_types import ConcurrencyPolicy, EdgeRef, JoinPolicy

if TYPE_CHECKING:
    from dipeo.application.execution.engine.context import TypedExecutionContext

logger = get_module_logger(__name__)


class NodeScheduler:
    """Manages node scheduling with dependency tracking and ready queue management."""

    def __init__(
        self,
        diagram: ExecutableDiagram,
        context: Optional["TypedExecutionContext"] = None,
    ):
        self.diagram = diagram
        self.context = context

        self._dependency_tracker = DependencyTracker(diagram)
        self._ready_queue = ReadyQueue(context)
        self._join_policies: dict[NodeID, JoinPolicy] = {}

        self._initialize_policies()
        self._initialize_ready_queue()

    def _initialize_policies(self) -> None:
        """Initialize join and concurrency policies for all nodes."""
        all_nodes = self.diagram.get_nodes_by_type(None) or self.diagram.nodes
        for node in all_nodes:
            if hasattr(node, "join_policy") and node.join_policy is not None:
                if isinstance(node.join_policy, str):
                    self._join_policies[node.id] = JoinPolicy(policy_type=node.join_policy)
                else:
                    self._join_policies[node.id] = node.join_policy
            else:
                if hasattr(node, "type") and node.type == NodeType.CONDITION:
                    self._join_policies[node.id] = JoinPolicy(policy_type="any")
                else:
                    self._join_policies[node.id] = JoinPolicy(policy_type="all")

            if hasattr(node, "concurrency_policy"):
                if isinstance(node.concurrency_policy, str):
                    policy = ConcurrencyPolicy(mode=node.concurrency_policy)
                else:
                    policy = node.concurrency_policy
            else:
                policy = ConcurrencyPolicy(mode="singleton")

            self._ready_queue.set_concurrency_policy(node.id, policy)

    def _initialize_ready_queue(self) -> None:
        """Initialize ready queue with nodes that have zero indegree."""
        initial_ready = self._dependency_tracker.get_initial_ready_nodes()
        for node_id in initial_ready:
            self._ready_queue.add_initial_ready_node(node_id)

    async def get_ready_nodes(self, context: "TypedExecutionContext") -> list[ExecutableNode]:
        """Get all nodes that are ready to execute."""
        from dipeo.infrastructure.timing import time_phase

        ready_nodes = []
        all_nodes = self.diagram.get_nodes_by_type(None) or self.diagram.nodes
        epoch = context.current_epoch()

        with time_phase(str(context.execution_id), "system", "edge_map_building"):
            incoming_edges_map = {
                node.id: self.diagram.get_incoming_edges(node.id) for node in all_nodes
            }

        with time_phase(str(context.execution_id), "system", "readiness_checking"):
            for node in all_nodes:
                is_ready = self._is_node_ready_optimized(node, context, incoming_edges_map)
                if is_ready:
                    ready_nodes.append(node)

        with time_phase(str(context.execution_id), "system", "node_prioritization"):
            return self._prioritize_nodes(ready_nodes)

    def mark_node_completed(self, node_id: NodeID, context: "TypedExecutionContext") -> set[NodeID]:
        """Mark a node as completed and return newly ready nodes."""
        newly_ready = self._dependency_tracker.mark_node_completed(node_id)
        for ready_id in newly_ready:
            self._ready_queue.add_initial_ready_node(ready_id)
        return newly_ready

    def on_token_published(self, edge: EdgeRef, epoch: int) -> None:
        """Handle token publication event."""
        self._ready_queue.on_token_published(edge, epoch)

    def mark_node_running(self, node_id: NodeID, epoch: int) -> None:
        """Mark a node as currently running."""
        self._ready_queue.mark_node_running(node_id, epoch)

    def mark_node_complete(self, node_id: NodeID, epoch: int) -> None:
        """Mark a node execution as complete."""
        self._ready_queue.mark_node_complete(node_id, epoch)

    def _is_node_ready(
        self,
        node: ExecutableNode,
        context: "TypedExecutionContext",
    ) -> bool:
        """Check if a node is ready to execute (legacy method)."""
        if node.type == NodeType.START and not self.diagram.get_incoming_edges(node.id):
            return context.state.get_node_execution_count(node.id) == 0

        if hasattr(context, "has_new_inputs") and hasattr(context, "current_epoch"):
            epoch = context.current_epoch()
            incoming_edges = self.diagram.get_incoming_edges(node.id)

            if not incoming_edges:
                return True

            has_tokens = context.has_new_inputs(node.id, epoch)

            if has_tokens:
                loop_ok = self._handle_loop_node(node, context)
                if not loop_ok:
                    return False

                has_priority_pending = self._has_pending_higher_priority_siblings(node, context)
                return not has_priority_pending
            else:
                return False

        logger.warning(
            f"Node {node.id} readiness check without token context - this should not happen in Phase 6"
        )
        return False

    def _is_node_ready_optimized(
        self,
        node: ExecutableNode,
        context: "TypedExecutionContext",
        incoming_edges_map: dict,
    ) -> bool:
        """Check if a node is ready to execute with optimized edge lookups."""
        incoming_edges = incoming_edges_map.get(node.id, [])

        if node.type == NodeType.START and not incoming_edges:
            return context.state.get_node_execution_count(node.id) == 0

        if hasattr(context, "has_new_inputs") and hasattr(context, "current_epoch"):
            epoch = context.current_epoch()

            if not incoming_edges:
                return True

            has_tokens = context.has_new_inputs(node.id, epoch)

            if has_tokens:
                loop_ok = self._handle_loop_node(node, context)
                if not loop_ok:
                    return False

                has_priority_pending = self._has_pending_higher_priority_siblings(node, context)
                return not has_priority_pending
            else:
                return False

        logger.warning(
            f"Node {node.id} readiness check without token context - this should not happen in Phase 6"
        )
        return False

    def _handle_loop_node(self, node: ExecutableNode, context: "TypedExecutionContext") -> bool:
        """Check if a loop node can execute again."""
        if node.type == NodeType.PERSON_JOB:
            exec_count = context.state.get_node_execution_count(node.id)
            max_iter = getattr(node, "max_iteration", 1)
            return exec_count < max_iter
        return True

    def _has_pending_higher_priority_siblings(
        self, node: ExecutableNode, context: "TypedExecutionContext"
    ) -> bool:
        """Check if higher-priority sibling nodes are still pending."""
        incoming_edges = self.diagram.get_incoming_edges(node.id)
        if not incoming_edges:
            return False

        for incoming_edge in incoming_edges:
            source_node_id = incoming_edge.source_node_id
            my_priority = getattr(incoming_edge, "execution_priority", 0)
            sibling_edges = self.diagram.get_outgoing_edges(source_node_id)

            for sibling_edge in sibling_edges:
                if sibling_edge.target_node_id == node.id:
                    continue

                sibling_priority = getattr(sibling_edge, "execution_priority", 0)
                if sibling_priority > my_priority:
                    sibling_state = context.state.get_node_state(sibling_edge.target_node_id)
                    if not sibling_state or sibling_state.status not in [
                        Status.COMPLETED,
                        Status.FAILED,
                        Status.SKIPPED,
                        Status.MAXITER_REACHED,
                    ]:
                        return True

        return False

    def _prioritize_nodes(self, nodes: list[ExecutableNode]) -> list[ExecutableNode]:
        """Sort nodes by priority (START → CONDITION → PERSON_JOB → others)."""

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
        """Get execution statistics."""
        dep_stats = self._dependency_tracker.get_stats()
        return {
            **dep_stats,
            "ready_queue_size": self._ready_queue.get_queue_size(),
        }
