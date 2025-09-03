"""Protocol for managing execution context during diagram runtime."""

from abc import abstractmethod
from typing import TYPE_CHECKING, Any, Optional, Protocol

from dipeo.diagram_generated import NodeID, NodeState
from dipeo.domain.execution.envelope import Envelope

if TYPE_CHECKING:
    from dipeo.domain.diagram.models.executable_diagram import ExecutableDiagram


class ExecutionContext(Protocol):
    """Manages runtime execution state with token-based flow control.
    
    This protocol defines the minimal contract for execution contexts,
    focusing on token operations as the primary execution mechanism.
    """
    
    # Core References
    diagram: "ExecutableDiagram"
    execution_id: str
    
    # ========== Token Operations (Primary Interface) ==========
    
    @abstractmethod
    def consume_inbound(self, node_id: NodeID, epoch: int | None = None) -> dict[str, Envelope]:
        """Consume all available input tokens for a node.
        
        Args:
            node_id: The node consuming tokens
            epoch: The epoch (defaults to current)
            
        Returns:
            Map of port name to envelope
        """
        ...
    
    @abstractmethod
    def emit_outputs_as_tokens(self, node_id: NodeID, outputs: dict[str, Envelope], epoch: int | None = None) -> None:
        """Emit node outputs as tokens on outgoing edges.
        
        Args:
            node_id: The node emitting outputs
            outputs: Map of output port to envelope  
            epoch: The epoch (defaults to current)
        """
        ...
    
    @abstractmethod
    def has_new_inputs(self, node_id: NodeID, epoch: int | None = None) -> bool:
        """Check if a node has unconsumed tokens ready.
        
        Args:
            node_id: The node to check
            epoch: The epoch (defaults to current)
            
        Returns:
            True if node has new inputs per its join policy
        """
        ...
    
    @abstractmethod
    def current_epoch(self) -> int:
        """Get the current execution epoch."""
        ...
    
    # ========== State Queries (For UI and Conditions) ==========
    
    @abstractmethod
    def get_node_state(self, node_id: NodeID) -> NodeState | None:
        """Get the current state of a node (for UI display)."""
        ...
    
    @abstractmethod
    def get_node_result(self, node_id: NodeID) -> dict[str, Any] | None:
        """Get the execution result of a completed node."""
        ...
    
    @abstractmethod
    def get_node_execution_count(self, node_id: NodeID) -> int:
        """Get the number of times a node has been executed."""
        ...
    
    # ========== State Transitions (For Engine) ==========
    
    @abstractmethod
    def transition_node_to_running(self, node_id: NodeID) -> int:
        """Transition a node to running state. Returns execution count."""
        ...
    
    @abstractmethod
    def transition_node_to_completed(self, node_id: NodeID, output: Any = None, token_usage: dict[str, int] | None = None) -> None:
        """Transition a node to completed state with output."""
        ...
    
    @abstractmethod
    def transition_node_to_failed(self, node_id: NodeID, error: str) -> None:
        """Transition a node to failed state with error message."""
        ...
    
    @abstractmethod
    def transition_node_to_maxiter(self, node_id: NodeID, output: Optional[Envelope] = None) -> None:
        """Transition a node to max iterations state."""
        ...
    
    # ========== Variables (For Expressions and Loop Indices) ==========
    
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


