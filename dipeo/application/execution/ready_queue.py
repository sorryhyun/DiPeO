"""Ready queue management for node scheduling with epoch tracking."""

import asyncio
from collections import defaultdict
from typing import TYPE_CHECKING

from dipeo.config.base_logger import get_module_logger
from dipeo.diagram_generated import NodeID
from dipeo.domain.execution.token_types import ConcurrencyPolicy, EdgeRef

if TYPE_CHECKING:
    from dipeo.application.execution.typed_execution_context import TypedExecutionContext

logger = get_module_logger(__name__)


class ReadyQueue:
    """Manages ready queue with epoch-based tracking and concurrency policies."""

    def __init__(self, context: "TypedExecutionContext | None" = None):
        self.context = context
        self._ready_queue: asyncio.Queue[NodeID] = asyncio.Queue()
        self._ready_queue_by_epoch: dict[int, asyncio.Queue[NodeID]] = defaultdict(asyncio.Queue)
        self._armed_nodes: dict[tuple[NodeID, int], bool] = {}
        self._running_nodes: dict[tuple[NodeID, int], bool] = {}
        self._concurrency_policies: dict[NodeID, ConcurrencyPolicy] = {}

    def set_concurrency_policy(self, node_id: NodeID, policy: ConcurrencyPolicy) -> None:
        """Set the concurrency policy for a node."""
        self._concurrency_policies[node_id] = policy

    def add_initial_ready_node(self, node_id: NodeID) -> None:
        """Add a node to the initial ready queue (used during initialization)."""
        self._ready_queue.put_nowait(node_id)

    def on_token_published(self, edge: EdgeRef, epoch: int) -> None:
        """Handle token publication event."""
        if not self.context:
            logger.debug(
                f"[TOKEN] Token published but no context: {edge.source_node_id} -> {edge.target_node_id}"
            )
            return

        target = edge.target_node_id
        has_inputs = self.context.has_new_inputs(target, epoch)
        can_arm = self._can_arm(target, epoch)

        if has_inputs and can_arm:
            self._arm_and_enqueue(target, epoch)

    def _can_arm(self, node_id: NodeID, epoch: int) -> bool:
        """Check if a node can be armed for execution at this epoch."""
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
        """Arm a node and add it to the ready queue."""
        key = (node_id, epoch)
        self._armed_nodes[key] = True
        self._ready_queue_by_epoch[epoch].put_nowait(node_id)
        self._ready_queue.put_nowait(node_id)

    def mark_node_running(self, node_id: NodeID, epoch: int) -> None:
        """Mark a node as currently running."""
        key = (node_id, epoch)
        self._running_nodes[key] = True
        self._armed_nodes.pop(key, None)

    def mark_node_complete(self, node_id: NodeID, epoch: int) -> None:
        """Mark a node as complete and remove from tracking."""
        key = (node_id, epoch)
        self._running_nodes.pop(key, None)
        self._armed_nodes.pop(key, None)

    def get_queue_size(self) -> int:
        """Get the current size of the ready queue."""
        return self._ready_queue.qsize()

    def get_epoch_queue_size(self, epoch: int) -> int:
        """Get the size of the ready queue for a specific epoch."""
        return self._ready_queue_by_epoch[epoch].qsize()
