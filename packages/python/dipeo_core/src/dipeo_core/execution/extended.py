"""Extended execution context with additional functionality for servers."""

from dataclasses import dataclass, field
from typing import Any, Dict

from .types import ExecutionContext


@dataclass
class ExtendedExecutionContext(ExecutionContext):
    """Extended execution context with server-specific functionality.

    This adds token tracking and other features needed by servers
    while maintaining compatibility with the base ExecutionContext.
    """

    # Token usage accumulation
    _token_accumulator: Dict[str, Any] = field(default_factory=dict, init=False)

    def add_token_usage(self, node_id: str, tokens: Any) -> None:
        """Accumulate token usage in memory for later persistence."""
        self._token_accumulator[node_id] = tokens

    def get_total_token_usage(self) -> Any:
        """Calculate total token usage from accumulator."""
        # Avoid circular import by checking token type at runtime
        token_type = type(next(iter(self._token_accumulator.values()), None))
        if not self._token_accumulator or token_type is None:
            # Return a default TokenUsage-like object
            return type(
                "TokenUsage", (), {"input": 0, "output": 0, "total": 0, "cached": None}
            )()

        # Create new instance of same type
        total = token_type(input=0, output=0, total=0)
        for tokens in self._token_accumulator.values():
            total.input += tokens.input
            total.output += tokens.output
            total.total += tokens.total
            if hasattr(tokens, "cached") and tokens.cached:
                total.cached = (total.cached or 0) + tokens.cached
        return total

    def find_edges_from(self, node_id: str) -> list[Dict[str, Any]]:
        """Find all edges originating from a node."""
        return [
            edge
            for edge in self.edges
            if edge.get("source", "").split(":")[0] == node_id
        ]

    def find_edges_to(self, node_id: str) -> list[Dict[str, Any]]:
        """Find all edges targeting a node."""
        return [
            edge
            for edge in self.edges
            if edge.get("target", "").split(":")[0] == node_id
        ]
