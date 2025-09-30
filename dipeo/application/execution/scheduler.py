"""Scheduler for managing node execution order with token-based tracking."""

import asyncio
import logging

from dipeo.config.base_logger import get_module_logger
from collections import defaultdict
from typing import TYPE_CHECKING, Any, Optional

from dipeo.diagram_generated import NodeID, NodeType, Status
from dipeo.domain.diagram.models.executable_diagram import ExecutableDiagram, ExecutableNode
from dipeo.domain.execution.token_types import ConcurrencyPolicy, EdgeRef, JoinPolicy

if TYPE_CHECKING:
    from dipeo.application.execution.typed_execution_context import TypedExecutionContext

logger = get_module_logger(__name__)

class NodeScheduler:
    """Manages node scheduling with indegree tracking and ready queue management."""

    def __init__(
        self,
        diagram: ExecutableDiagram,
        context: Optional["TypedExecutionContext"] = None,
    ):
        self.diagram = diagram
        self.context = context

        self._indegree: dict[NodeID, int] = {}
        self._dependents: dict[NodeID, set[NodeID]] = defaultdict(set)
        self._ready_queue: asyncio.Queue[NodeID] = asyncio.Queue()
        self._processed_nodes: set[NodeID] = set()
        self._priority_dependencies: dict[NodeID, set[NodeID]] = defaultdict(set)
        self._ready_queue_by_epoch: dict[int, asyncio.Queue[NodeID]] = defaultdict(asyncio.Queue)
        self._armed_nodes: dict[tuple[NodeID, int], bool] = {}
        self._running_nodes: dict[tuple[NodeID, int], bool] = {}
        self._join_policies: dict[NodeID, JoinPolicy] = {}
        self._concurrency_policies: dict[NodeID, ConcurrencyPolicy] = {}

        self._initialize_dependencies()
        self._initialize_policies()

    def _is_conditional_edge(self, edge) -> bool:
        if getattr(edge, "is_conditional", False):
            return True
        return str(getattr(edge, "source_output", "")).lower() in ("condtrue", "condfalse")

    def _initialize_dependencies(self) -> None:
        all_nodes = self.diagram.get_nodes_by_type(None) or self.diagram.nodes
        for node in all_nodes:
            self._indegree[node.id] = 0

        nodes_with_non_conditional_deps: set[NodeID] = set()
        incoming_by_target: dict[NodeID, list] = defaultdict(list)
        edges_by_source: dict[NodeID, list] = defaultdict(list)
        all_edges = []
        for node in all_nodes:
            for edge in self.diagram.get_outgoing_edges(node.id):
                edges_by_source[edge.source_node_id].append(edge)
                incoming_by_target[edge.target_node_id].append(edge)
                all_edges.append(edge)

        for edge in all_edges:
            source_node = next((n for n in all_nodes if n.id == edge.source_node_id), None)
            if (
                source_node
                and hasattr(source_node, "type")
                and source_node.type == NodeType.CONDITION
                and getattr(source_node, "skippable", False)
            ):
                target_incoming_edges = incoming_by_target.get(edge.target_node_id, [])
                unique_sources = set(e.source_node_id for e in target_incoming_edges)

                if len(unique_sources) > 1:
                    logger.debug(
                        f"Skipping edge from skippable condition {edge.source_node_id} -> {edge.target_node_id} (target has {len(unique_sources)} sources)"
                    )
                    continue
                else:
                    logger.debug(
                        f"Not skipping edge from skippable condition {edge.source_node_id} -> {edge.target_node_id} (only source)"
                    )

            if self._is_conditional_edge(edge):
                continue

            self._indegree[edge.target_node_id] += 1
            self._dependents[edge.source_node_id].add(edge.target_node_id)
            nodes_with_non_conditional_deps.add(edge.target_node_id)

        for _source_id, edges in edges_by_source.items():
            sorted_edges = sorted(edges, key=lambda e: -getattr(e, "execution_priority", 0))

            for i, lower_edge in enumerate(sorted_edges):
                for higher_edge in sorted_edges[:i]:
                    if getattr(higher_edge, "execution_priority", 0) > getattr(
                        lower_edge, "execution_priority", 0
                    ):
                        self._priority_dependencies[lower_edge.target_node_id].add(
                            higher_edge.target_node_id
                        )

        for node_id, count in self._indegree.items():
            if count == 0:
                self._ready_queue.put_nowait(node_id)

    def _initialize_policies(self) -> None:
        from dipeo.diagram_generated import NodeType

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
                    self._concurrency_policies[node.id] = ConcurrencyPolicy(
                        mode=node.concurrency_policy
                    )
                else:
                    self._concurrency_policies[node.id] = node.concurrency_policy
            else:
                self._concurrency_policies[node.id] = ConcurrencyPolicy(mode="singleton")

    async def get_ready_nodes(self, context: "TypedExecutionContext") -> list[ExecutableNode]:
        ready_nodes = []
        all_nodes = self.diagram.get_nodes_by_type(None) or self.diagram.nodes

        for node in all_nodes:
            if self._is_node_ready(node, context):
                ready_nodes.append(node)

        return self._prioritize_nodes(ready_nodes)

    def mark_node_completed(self, node_id: NodeID, context: "TypedExecutionContext") -> set[NodeID]:
        if node_id in self._processed_nodes:
            return set()

        self._processed_nodes.add(node_id)
        newly_ready = set()

        for dependent_id in self._dependents.get(node_id, set()):
            self._indegree[dependent_id] -= 1
            if self._indegree[dependent_id] == 0:
                newly_ready.add(dependent_id)
                self._ready_queue.put_nowait(dependent_id)

        return newly_ready

    def on_token_published(self, edge: EdgeRef, epoch: int) -> None:
        if not self.context:
            return

        target = edge.target_node_id
        has_inputs = self.context.has_new_inputs(target, epoch)
        can_arm = self._can_arm(target, epoch)

        if has_inputs and can_arm:
            self._arm_and_enqueue(target, epoch)

    def _can_arm(self, node_id: NodeID, epoch: int) -> bool:
        key = (node_id, epoch)

        if self._armed_nodes.get(key, False):
            return False

        policy = self._concurrency_policies.get(node_id, ConcurrencyPolicy(mode="singleton"))
        running_count = sum(
            1
            for (nid, ep), running in self._running_nodes.items()
            if nid == node_id and ep == epoch and running
        )

        return policy.can_arm(running_count)

    def _arm_and_enqueue(self, node_id: NodeID, epoch: int) -> None:
        key = (node_id, epoch)
        self._armed_nodes[key] = True
        self._ready_queue_by_epoch[epoch].put_nowait(node_id)
        self._ready_queue.put_nowait(node_id)

    def mark_node_running(self, node_id: NodeID, epoch: int) -> None:
        key = (node_id, epoch)
        self._running_nodes[key] = True
        self._armed_nodes.pop(key, None)

    def mark_node_complete(self, node_id: NodeID, epoch: int) -> None:
        key = (node_id, epoch)
        self._running_nodes.pop(key, None)
        self._armed_nodes.pop(key, None)

    def _is_node_ready(
        self,
        node: ExecutableNode,
        context: "TypedExecutionContext",
    ) -> bool:
        if node.type == NodeType.START and not self.diagram.get_incoming_edges(node.id):
            return context.state.get_node_execution_count(node.id) == 0

        if hasattr(context, "has_new_inputs") and hasattr(context, "current_epoch"):
            epoch = context.current_epoch()
            incoming_edges = self.diagram.get_incoming_edges(node.id)

            if not incoming_edges:
                return True

            has_tokens = context.has_new_inputs(node.id, epoch)
            if has_tokens:
                if not self._handle_loop_node(node, context):
                    return False
                return not self._has_pending_higher_priority_siblings(node, context)
            else:
                return False

        logger.warning(
            f"Node {node.id} readiness check without token context - this should not happen in Phase 6"
        )
        return False

    def _handle_loop_node(self, node: ExecutableNode, context: "TypedExecutionContext") -> bool:
        if node.type == NodeType.PERSON_JOB:
            exec_count = context.state.get_node_execution_count(node.id)
            max_iter = getattr(node, "max_iteration", 1)
            return exec_count < max_iter
        return True

    def _has_pending_higher_priority_siblings(
        self, node: ExecutableNode, context: "TypedExecutionContext"
    ) -> bool:
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
