"""Token management for execution context.

This module provides focused token operations, separating token flow
management from other execution concerns.
"""

import logging
from collections import defaultdict

from dipeo.config.base_logger import get_module_logger
from dipeo.diagram_generated import NodeID, NodeType
from dipeo.domain.diagram.models.executable_diagram import ExecutableDiagram
from dipeo.domain.execution.messaging.envelope import Envelope
from dipeo.domain.execution.tokens.readiness_evaluator import TokenReadinessEvaluator
from dipeo.domain.execution.tokens.token_types import EdgeRef, Token

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

        # Initialize readiness evaluator
        self._readiness_evaluator = TokenReadinessEvaluator(
            diagram=self.diagram,
            in_edges=self._in_edges,
            edge_seq=self._edge_seq,
            last_consumed=self._last_consumed,
            branch_decisions=self._branch_decisions,
        )

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

        node_exec_count = 0
        if self._execution_tracker:
            node_exec_count = self._execution_tracker.get_node_execution_count(node_id)

        return self._readiness_evaluator.has_new_inputs(
            node_id=node_id,
            epoch=epoch,
            join_policy=join_policy,
            node_exec_count=node_exec_count,
        )

    def get_branch_decision(self, node_id: NodeID) -> str | None:
        return self._branch_decisions.get(node_id)
