"""Token management for execution context.

This module provides focused token operations, separating token flow
management from other execution concerns.
"""

import logging
from collections import defaultdict

from dipeo.config.base_logger import get_module_logger
from dipeo.diagram_generated import NodeID, NodeType
from dipeo.domain.diagram.models.executable_diagram import ExecutableDiagram
from dipeo.domain.execution.envelope import Envelope
from dipeo.domain.execution.token_types import EdgeRef, Token

logger = get_module_logger(__name__)


class TokenManager:
    """Manages token flow through the execution graph.

    Responsibilities:
    - Token publishing and consumption
    - Edge tracking and mapping
    - Epoch management
    - Join policy evaluation
    """

    def __init__(self, diagram: ExecutableDiagram, execution_tracker=None):
        """Initialize token manager with diagram structure.

        Args:
            diagram: The executable diagram to manage tokens for
            execution_tracker: Optional tracker to check node execution counts
        """
        self.diagram = diagram
        self._execution_tracker = execution_tracker

        self._epoch: int = 0

        self._edge_seq: dict[tuple[EdgeRef, int], int] = defaultdict(int)
        self._edge_tokens: dict[tuple[EdgeRef, int, int], Envelope] = {}
        self._last_consumed: dict[tuple[NodeID, EdgeRef, int], int] = defaultdict(int)

        self._in_edges: dict[NodeID, list[EdgeRef]] = {}
        self._out_edges: dict[NodeID, list[EdgeRef]] = {}

        self._branch_decisions: dict[NodeID, str] = {}

        self._build_edge_maps()

    def _build_edge_maps(self) -> None:
        for edge in self.diagram.edges:
            edge_ref = EdgeRef(
                source_node_id=edge.source_node_id,
                source_output=edge.source_output,
                target_node_id=edge.target_node_id,
                target_input=edge.target_input,
            )

            if edge.source_node_id not in self._out_edges:
                self._out_edges[edge.source_node_id] = []
            self._out_edges[edge.source_node_id].append(edge_ref)

            if edge.target_node_id not in self._in_edges:
                self._in_edges[edge.target_node_id] = []
            self._in_edges[edge.target_node_id].append(edge_ref)

    def current_epoch(self) -> int:
        return self._epoch

    def begin_epoch(self) -> int:
        """Start a new epoch (for loop entry).

        Returns:
            The new epoch number
        """
        self._epoch += 1
        return self._epoch

    def publish_token(self, edge: EdgeRef, payload: Envelope, epoch: int | None = None) -> Token:
        """Publish a token on an edge.

        Args:
            edge: The edge to publish on
            payload: The envelope to send
            epoch: The epoch (defaults to current)

        Returns:
            The published token
        """
        if epoch is None:
            epoch = self._epoch

        seq_key = (edge, epoch)
        self._edge_seq[seq_key] += 1
        seq = self._edge_seq[seq_key]

        token = Token(epoch=epoch, seq=seq, content=payload)

        self._edge_tokens[(edge, epoch, seq)] = payload

        return token

    def emit_outputs(
        self, node_id: NodeID, outputs: dict[str, Envelope], epoch: int | None = None
    ) -> None:
        """Emit node outputs as tokens on outgoing edges.

        Matches output ports to edge source_output for routing.
        For condition nodes, outputs should be on "condtrue" or "condfalse" ports.

        Args:
            node_id: The node emitting outputs
            outputs: Map of output port to envelope
            epoch: The epoch (defaults to current)
        """
        if epoch is None:
            epoch = self._epoch

        node = self.diagram.get_node(node_id)
        is_condition = node and hasattr(node, "type") and node.type == NodeType.CONDITION

        if is_condition:
            if "condtrue" in outputs:
                self._branch_decisions[node_id] = "condtrue"
            elif "condfalse" in outputs:
                self._branch_decisions[node_id] = "condfalse"

        out_edges = self._out_edges.get(node_id, [])

        for edge in out_edges:
            out_key = edge.source_output or "default"

            payload = outputs.get(out_key)

            if payload is None:
                continue

            self.publish_token(edge, payload, epoch=epoch)

    def _extract_branch_decision(self, output: Envelope) -> str | None:
        if hasattr(output, "body"):
            body = output.body
            if isinstance(body, dict) and "result" in body:
                return "condtrue" if bool(body["result"]) else "condfalse"
            elif isinstance(body, bool):
                return "condtrue" if body else "condfalse"
        return None

    def consume_inbound(self, node_id: NodeID, epoch: int | None = None) -> dict[str, Envelope]:
        """Atomically consume inbound tokens for a node.

        Args:
            node_id: The node consuming tokens
            epoch: The epoch (defaults to current)

        Returns:
            Map of port name to envelope
        """
        if epoch is None:
            epoch = self._epoch

        inputs: dict[str, Envelope] = {}

        for edge in self._in_edges.get(node_id, []):
            seq = self._edge_seq.get((edge, epoch), 0)
            last_consumed = self._last_consumed.get((node_id, edge, epoch), 0)

            if seq <= last_consumed:
                continue

            self._last_consumed[(node_id, edge, epoch)] = seq

            payload = self._edge_tokens.get((edge, epoch, seq))
            if payload is not None:
                key = edge.target_input or "default"
                inputs[key] = payload

        return inputs

    def has_new_inputs(
        self, node_id: NodeID, epoch: int | None = None, join_policy: str = "all"
    ) -> bool:
        """Check if a node has new inputs to process.

        Args:
            node_id: The node to check
            epoch: The epoch (defaults to current)
            join_policy: The join policy type ("all", "any", etc.)

        Returns:
            True if the node has unconsumed tokens per its join policy
        """
        if epoch is None:
            epoch = self._epoch

        edges = self._in_edges.get(node_id, [])
        if not edges:
            return True

        node_exec_count = 0
        if self._execution_tracker:
            node_exec_count = self._execution_tracker.get_node_execution_count(node_id)

        relevant_edges = []
        for edge in edges:
            source_node = self.diagram.get_node(edge.source_node_id)

            if source_node and hasattr(source_node, "type") and source_node.type == NodeType.START:
                if node_exec_count > 0:
                    continue

            relevant_edges.append(edge)

        active_edges = []
        skippable_edges = []

        for edge in relevant_edges:
            source_node = self.diagram.get_node(edge.source_node_id)

            if (
                source_node
                and hasattr(source_node, "type")
                and source_node.type == NodeType.CONDITION
            ):
                is_skippable = getattr(source_node, "skippable", False)

                if is_skippable:
                    unique_sources = set(e.source_node_id for e in relevant_edges)

                    if len(unique_sources) > 1:
                        skippable_edges.append(edge)
                        continue
            active_edges.append(edge)

        if not active_edges and skippable_edges:
            active_edges = skippable_edges
            skippable_edges = []

        required_edges = []

        for edge in active_edges:
            if edge.source_output in ["condtrue", "condfalse"]:
                branch_decision = self._branch_decisions.get(edge.source_node_id)

                if branch_decision and branch_decision != edge.source_output:
                    continue
            required_edges.append(edge)

        if join_policy == "all":
            for edge in required_edges:
                seq = self._edge_seq.get((edge, epoch), 0)
                last_consumed = self._last_consumed.get((node_id, edge, epoch), 0)
                if seq <= last_consumed:
                    return False
            return len(required_edges) > 0

        elif join_policy == "any":
            for edge in required_edges:
                seq = self._edge_seq.get((edge, epoch), 0)
                last_consumed = self._last_consumed.get((node_id, edge, epoch), 0)
                if seq > last_consumed:
                    return True
            return False

        return (
            all(
                self._edge_seq.get((edge, epoch), 0)
                > self._last_consumed.get((node_id, edge, epoch), 0)
                for edge in required_edges
            )
            if required_edges
            else False
        )

    def get_branch_decision(self, node_id: NodeID) -> str | None:
        return self._branch_decisions.get(node_id)
