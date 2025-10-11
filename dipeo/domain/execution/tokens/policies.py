"""Token policy evaluation for execution control.

This module provides policy classes that control when nodes are ready to execute
based on available tokens.
"""

from enum import Enum
from typing import Protocol

from dipeo.diagram_generated import NodeID
from dipeo.domain.execution.tokens.token_types import EdgeRef


class JoinPolicyType(Enum):
    """Join policy types for multi-input nodes.

    Join policies determine when a node with multiple inputs is ready to execute:
    - ALL: All incoming edges must have unconsumed tokens
    - ANY: At least one incoming edge has unconsumed tokens
    - FIRST: Ready after first token arrives (same as ANY for single execution)
    - K_OF_N: At least k edges must have tokens (requires k parameter)
    """

    ALL = "all"
    ANY = "any"
    FIRST = "first"
    K_OF_N = "k_of_n"


class TokenAvailabilityChecker(Protocol):
    """Protocol for checking token availability on edges."""

    def has_unconsumed_token(self, edge: EdgeRef, node_id: NodeID, epoch: int) -> bool:
        """Check if an edge has an unconsumed token.

        Args:
            edge: The edge to check
            node_id: The consuming node
            epoch: The epoch to check

        Returns:
            True if there's an unconsumed token on this edge
        """
        ...


class JoinPolicyEvaluator:
    """Evaluates join policies for node readiness.

    This class encapsulates the logic for determining when a node is ready
    to execute based on available tokens and the node's join policy.
    """

    def __init__(self, token_checker: TokenAvailabilityChecker):
        """Initialize evaluator with token availability checker.

        Args:
            token_checker: Object that can check token availability on edges
        """
        self._token_checker = token_checker

    def is_ready(
        self,
        policy_type: JoinPolicyType | str,
        edges: list[EdgeRef],
        node_id: NodeID,
        epoch: int,
        k: int | None = None,
    ) -> bool:
        """Check if a node is ready based on its join policy.

        Args:
            policy_type: The join policy type
            edges: The edges to check (after filtering for relevance)
            node_id: The node to check
            epoch: The epoch to check
            k: Required count for K_OF_N policy

        Returns:
            True if the join policy is satisfied
        """
        if not edges:
            return False

        # Convert string to enum if needed
        if isinstance(policy_type, str):
            try:
                policy_type = JoinPolicyType(policy_type)
            except ValueError:
                # Default to ALL for unknown policy types
                policy_type = JoinPolicyType.ALL

        # Count edges with unconsumed tokens
        edges_with_tokens = [
            edge for edge in edges if self._token_checker.has_unconsumed_token(edge, node_id, epoch)
        ]
        available_count = len(edges_with_tokens)
        total_count = len(edges)

        # Evaluate based on policy type
        if policy_type == JoinPolicyType.ALL:
            return available_count == total_count

        elif policy_type in (JoinPolicyType.ANY, JoinPolicyType.FIRST):
            return available_count > 0

        elif policy_type == JoinPolicyType.K_OF_N:
            if k is None:
                raise ValueError("K_OF_N policy requires k parameter")
            return available_count >= k

        # Default to ALL behavior for safety
        return available_count == total_count


class TokenCounter:
    """Utility for counting and tracking token sequences.

    This class encapsulates token counting logic, separating the bookkeeping
    of token sequences from the core token management responsibilities.
    """

    def __init__(self):
        """Initialize token counter."""
        self._sequences: dict[tuple[EdgeRef, int], int] = {}
        self._last_consumed: dict[tuple[NodeID, EdgeRef, int], int] = {}

    def increment_sequence(self, edge: EdgeRef, epoch: int) -> int:
        """Increment and return the next sequence number for an edge.

        Args:
            edge: The edge to increment
            epoch: The epoch

        Returns:
            The new sequence number (1, 2, 3, ...)
        """
        key = (edge, epoch)
        self._sequences[key] = self._sequences.get(key, 0) + 1
        return self._sequences[key]

    def get_sequence(self, edge: EdgeRef, epoch: int) -> int:
        """Get the current sequence number for an edge.

        Args:
            edge: The edge to check
            epoch: The epoch

        Returns:
            The current sequence number (0 if never published)
        """
        return self._sequences.get((edge, epoch), 0)

    def mark_consumed(self, node_id: NodeID, edge: EdgeRef, epoch: int, seq: int) -> None:
        """Mark a token as consumed.

        Args:
            node_id: The consuming node
            edge: The edge the token came from
            epoch: The epoch
            seq: The sequence number consumed
        """
        key = (node_id, edge, epoch)
        self._last_consumed[key] = seq

    def get_last_consumed(self, node_id: NodeID, edge: EdgeRef, epoch: int) -> int:
        """Get the last consumed sequence number.

        Args:
            node_id: The consuming node
            edge: The edge to check
            epoch: The epoch

        Returns:
            The last consumed sequence number (0 if never consumed)
        """
        return self._last_consumed.get((node_id, edge, epoch), 0)

    def has_unconsumed(self, node_id: NodeID, edge: EdgeRef, epoch: int) -> bool:
        """Check if there are unconsumed tokens.

        Args:
            node_id: The consuming node
            edge: The edge to check
            epoch: The epoch

        Returns:
            True if there are unconsumed tokens
        """
        current_seq = self.get_sequence(edge, epoch)
        last_consumed = self.get_last_consumed(node_id, edge, epoch)
        return current_seq > last_consumed
