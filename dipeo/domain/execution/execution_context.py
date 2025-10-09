"""Protocol for managing execution context during diagram runtime."""

from abc import abstractmethod
from typing import TYPE_CHECKING, Any, Protocol

from dipeo.diagram_generated import NodeID

if TYPE_CHECKING:
    from dipeo.domain.diagram.models.executable_diagram import ExecutableDiagram
    from dipeo.domain.execution.envelope import Envelope
    from dipeo.domain.execution.state_tracker import StateTracker
    from dipeo.domain.execution.token_manager import TokenManager


class ExecutionContext(Protocol):
    """Manages runtime execution state with token-based flow control.

    This protocol defines the minimal contract for execution contexts,
    using specialized managers for state and token operations.
    """

    # Core References
    diagram: "ExecutableDiagram"
    execution_id: str

    # Manager Components
    state: "StateTracker"
    tokens: "TokenManager"

    @abstractmethod
    def current_epoch(self) -> int:
        """Get the current execution epoch."""
        ...

    @abstractmethod
    def get_variable(self, name: str) -> Any:
        """Get a variable value (for conditions and expressions)."""
        ...

    @abstractmethod
    def set_variable(self, name: str, value: Any) -> None:
        """Set a variable value (for loop indices and branch tracking)."""
        ...

    @abstractmethod
    def get_variables(self) -> dict[str, Any]:
        """Get all variables (for expression evaluation)."""
        ...

    @abstractmethod
    def consume_inbound(self, node_id: NodeID) -> dict[str, "Envelope"]:
        """Consume inbound tokens for a node.

        Delegates to TokenManager to atomically consume available tokens
        from incoming edges for the specified node.

        Args:
            node_id: The node consuming tokens

        Returns:
            Dict of port name to envelope
        """
        ...

    @abstractmethod
    def emit_outputs_as_tokens(self, node_id: NodeID, outputs: dict[str, "Envelope"]) -> None:
        """Emit node outputs as tokens on outgoing edges.

        Delegates to TokenManager to publish tokens on all outgoing edges
        from the specified node.

        Args:
            node_id: The node emitting outputs
            outputs: Map of output port to envelope
        """
        ...
