"""Token management for execution context.

This module provides focused token operations, separating token flow
management from other execution concerns.
"""

import logging
from collections import defaultdict
from typing import Any, Optional

from dipeo.diagram_generated import NodeID, NodeType
from dipeo.domain.diagram.models.executable_diagram import ExecutableDiagram
from dipeo.domain.execution.envelope import Envelope
from dipeo.domain.execution.token_types import EdgeRef, Token

logger = logging.getLogger(__name__)


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
        
        # Current epoch
        self._epoch: int = 0
        
        # Token storage: (edge, epoch, seq) -> envelope
        self._edge_seq: dict[tuple[EdgeRef, int], int] = defaultdict(int)
        self._edge_tokens: dict[tuple[EdgeRef, int, int], Envelope] = {}
        self._last_consumed: dict[tuple[NodeID, EdgeRef, int], int] = defaultdict(int)
        
        # Edge maps for efficient lookups
        self._in_edges: dict[NodeID, list[EdgeRef]] = {}
        self._out_edges: dict[NodeID, list[EdgeRef]] = {}
        
        # Branch decisions for condition nodes
        self._branch_decisions: dict[NodeID, str] = {}
        
        # Initialize edge maps
        self._build_edge_maps()
    
    def _build_edge_maps(self) -> None:
        """Build incoming and outgoing edge maps from diagram."""
        for edge in self.diagram.edges:
            edge_ref = EdgeRef(
                source_node_id=edge.source_node_id,
                source_output=edge.source_output,
                target_node_id=edge.target_node_id
            )
            
            # Add to outgoing edges
            if edge.source_node_id not in self._out_edges:
                self._out_edges[edge.source_node_id] = []
            self._out_edges[edge.source_node_id].append(edge_ref)
            
            # Add to incoming edges
            if edge.target_node_id not in self._in_edges:
                self._in_edges[edge.target_node_id] = []
            self._in_edges[edge.target_node_id].append(edge_ref)
    
    # ========== Epoch Management ==========
    
    def current_epoch(self) -> int:
        """Get the current execution epoch."""
        return self._epoch
    
    def begin_epoch(self) -> int:
        """Start a new epoch (for loop entry).
        
        Returns:
            The new epoch number
        """
        self._epoch += 1
        logger.info(f"[TOKEN] Beginning new epoch: {self._epoch}")
        return self._epoch
    
    # ========== Token Publishing ==========
    
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
        
        # Increment sequence number for this edge/epoch
        seq_key = (edge, epoch)
        self._edge_seq[seq_key] += 1
        seq = self._edge_seq[seq_key]
        
        # Create and store the token
        token = Token(
            epoch=epoch,
            seq=seq,
            content=payload
        )
        
        # Store the envelope for later consumption
        self._edge_tokens[(edge, epoch, seq)] = payload
        
        logger.debug(
            f"[TOKEN] Published token on {edge.source_node_id}->{edge.target_node_id} "
            f"(epoch={epoch}, seq={seq})"
        )
        
        return token
    
    def emit_outputs(self, node_id: NodeID, outputs: dict[str, Envelope], epoch: int | None = None) -> None:
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
        
        # Check if this is a condition node and track branch decision
        node = self.diagram.get_node(node_id)
        is_condition = node and hasattr(node, 'type') and node.type == NodeType.CONDITION
        
        if is_condition:
            # Track which branch was taken based on available outputs
            if "condtrue" in outputs:
                self._branch_decisions[node_id] = "condtrue"
            elif "condfalse" in outputs:
                self._branch_decisions[node_id] = "condfalse"

        # Debug logging
        logger.debug(f"[TOKEN] emit_outputs: node_id={node_id}, outputs keys={list(outputs.keys())}")
        
        # Emit tokens on outgoing edges
        for edge in self._out_edges.get(node_id, []):
            # Match output port to edge source_output
            # For edges from condition nodes, source_output will be "condtrue" or "condfalse"
            out_key = edge.source_output or "default"

            payload = outputs.get(out_key)
            
            if payload is None:
                # No output for this port - edge won't get a token
                continue
            
            self.publish_token(edge, payload, epoch=epoch)
    
    def _extract_branch_decision(self, output: Envelope) -> str | None:
        """Extract branch decision from condition output."""
        if hasattr(output, 'body'):
            body = output.body
            if isinstance(body, dict) and "result" in body:
                return "condtrue" if bool(body["result"]) else "condfalse"
            elif isinstance(body, bool):
                return "condtrue" if body else "condfalse"
        return None
    
    # ========== Token Consumption ==========
    
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
            
            # Only consume NEW tokens (seq > last_consumed)
            if seq <= last_consumed:
                continue
            
            # Mark as consumed
            self._last_consumed[(node_id, edge, epoch)] = seq
            
            # Get the payload
            payload = self._edge_tokens.get((edge, epoch, seq))
            if payload is not None:
                # Use source_output as the port key, default to "default"
                key = edge.source_output or "default"
                inputs[key] = payload
        
        return inputs
    
    # ========== Token Readiness ==========
    
    def has_new_inputs(self, node_id: NodeID, epoch: int | None = None, join_policy: str = "all") -> bool:
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
            # Source nodes are always ready
            return True
        
        # Check if this node has already executed (for handling START edges)
        node_exec_count = 0
        if self._execution_tracker:
            node_exec_count = self._execution_tracker.get_node_execution_count(node_id)

        # First filter out edges we should ignore completely
        relevant_edges = []
        for edge in edges:
            source_node = self.diagram.get_node(edge.source_node_id)
            
            # Skip edges from START nodes only if THIS node has already executed
            # (i.e., it already consumed the START token in a previous iteration)
            if source_node and hasattr(source_node, 'type') and source_node.type == NodeType.START:
                if node_exec_count > 0:
                    # This node already executed, so it already consumed START's token
                    # Don't require it again
                    continue
            
            relevant_edges.append(edge)
        
        # Now categorize the relevant edges
        active_edges = []
        skippable_edges = []

        for edge in relevant_edges:
            source_node = self.diagram.get_node(edge.source_node_id)

            # Check if edge is from a skippable condition
            # Skippable conditions can only be skipped if the target has alternative paths
            if source_node and hasattr(source_node, 'type') and source_node.type == NodeType.CONDITION:
                is_skippable = getattr(source_node, 'skippable', False)

                if is_skippable:
                    # Count unique sources for this node to determine if skippable
                    # Use relevant_edges instead of all edges to exclude ignored START edges
                    unique_sources = set(e.source_node_id for e in relevant_edges)

                    if len(unique_sources) > 1:
                        # This node has multiple sources - condition edge can be skippable
                        skippable_edges.append(edge)
                        continue
                    else:
                        # This is the only source - cannot be skipped even if marked skippable
                        logger.debug(f"[TOKEN] Node {node_id}: Treating skippable condition edge as required (only source)")

            active_edges.append(edge)
        
        # If only skippable edges remain after filtering, they become required
        # This prevents deadlock when skippable conditions are the only dependencies
        logger.debug(f"[TOKEN] Node {node_id}: active_edges={len(active_edges)}, skippable_edges={len(skippable_edges)}")
        if not active_edges and skippable_edges:
            active_edges = skippable_edges
            skippable_edges = []
        
        # Filter out inactive conditional branches
        required_edges = []

        for edge in active_edges:

            # For conditional branches, only include the active branch
            if edge.source_output in ["condtrue", "condfalse"]:
                branch_decision = self._branch_decisions.get(edge.source_node_id)

                # If we know the branch decision, filter out the inactive branch
                if branch_decision and branch_decision != edge.source_output:
                    continue
                else:
                    logger.debug(f"[TOKEN] Node {node_id}: Including active/matching branch {edge.source_output} from {edge.source_node_id}")
            
            logger.debug(f"[TOKEN] Node {node_id}: Adding edge to required_edges")
            required_edges.append(edge)
        
        # Apply join policy
        if join_policy == "all":
            # ALL: Require new tokens on all required edges
            logger.debug(f"[TOKEN] Node {node_id}: Checking {len(required_edges)} required edges with ALL policy")
            for edge in required_edges:
                seq = self._edge_seq.get((edge, epoch), 0)
                last_consumed = self._last_consumed.get((node_id, edge, epoch), 0)
                if seq <= last_consumed:
                    logger.debug(f"[TOKEN] RESULT: Node {node_id} has_new_inputs=False (missing token)")
                    return False
            result = len(required_edges) > 0
            return result
            
        elif join_policy == "any":
            # ANY: Require new token on at least one edge
            for edge in required_edges:
                seq = self._edge_seq.get((edge, epoch), 0)
                last_consumed = self._last_consumed.get((node_id, edge, epoch), 0)
                if seq > last_consumed:
                    return True
            return False
        
        # Default to ALL
        result = all(
            self._edge_seq.get((edge, epoch), 0) > self._last_consumed.get((node_id, edge, epoch), 0)
            for edge in required_edges
        ) if required_edges else False
        return result
    
    # ========== Utility Methods ==========
    
    def get_branch_decision(self, node_id: NodeID) -> str | None:
        """Get which branch was taken from a condition node."""
        return self._branch_decisions.get(node_id)