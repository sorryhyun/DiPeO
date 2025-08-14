"""Protocol for managing execution state lifecycle."""

from abc import abstractmethod
from typing import Any, Protocol

from dipeo.diagram_generated import NodeID, NodeState
from dipeo.diagram_generated.domain_models import DiagramID
from dipeo.core.execution.envelope import Envelope
from dipeo.core.execution.execution_context import ExecutionContext


class ExecutionStateManager(Protocol):
    """Manages the lifecycle and persistence of execution state.
    
    This protocol separates state management concerns from execution logic,
    enabling different storage strategies (in-memory, database, distributed).
    """
    
    # State Creation and Retrieval
    
    @abstractmethod
    def create_execution_state(
        self,
        diagram_id: DiagramID,
        initial_inputs: dict[str, Any] | None = None,
        metadata: dict[str, Any] | None = None
    ) -> str:
        """Create a new execution state.
        
        Args:
            diagram_id: ID of the diagram being executed
            initial_inputs: Initial input values
            metadata: Execution metadata
            
        Returns:
            Execution ID
        """
        ...
    
    @abstractmethod
    def get_execution_context(self, execution_id: str) -> ExecutionContext:
        """Get execution context for an execution.
        
        Args:
            execution_id: The execution ID
            
        Returns:
            ExecutionContext implementation
        """
        ...
    
    @abstractmethod
    def save_execution_state(self, execution_id: str) -> None:
        """Persist current execution state.
        
        Args:
            execution_id: The execution ID
        """
        ...
    
    @abstractmethod
    def load_execution_state(self, execution_id: str) -> ExecutionContext | None:
        """Load a previously saved execution state.
        
        Args:
            execution_id: The execution ID
            
        Returns:
            ExecutionContext or None if not found
        """
        ...
    
    # State Queries
    
    @abstractmethod
    def get_execution_status(self, execution_id: str) -> str:
        """Get the overall status of an execution.
        
        Returns one of: 'running', 'completed', 'failed', 'cancelled'
        
        Args:
            execution_id: The execution ID
            
        Returns:
            Execution status
        """
        ...
    
    @abstractmethod
    def get_execution_progress(self, execution_id: str) -> dict[str, Any]:
        """Get progress information for an execution.
        
        Returns metrics like:
        - total_nodes
        - completed_nodes
        - failed_nodes
        - running_nodes
        - completion_percentage
        
        Args:
            execution_id: The execution ID
            
        Returns:
            Progress metrics
        """
        ...
    
    @abstractmethod
    def get_execution_history(
        self,
        execution_id: str,
        node_id: NodeID | None = None
    ) -> list[dict[str, Any]]:
        """Get execution history events.
        
        Args:
            execution_id: The execution ID
            node_id: Optional filter by node
            
        Returns:
            List of history events
        """
        ...
    
    # State Updates
    
    @abstractmethod
    def update_node_state(
        self,
        execution_id: str,
        node_id: NodeID,
        state: NodeState,
        output: Envelope | None = None,
        error: str | None = None
    ) -> None:
        """Update the state of a specific node.
        
        Args:
            execution_id: The execution ID
            node_id: The node to update
            state: New node state
            output: Node output if completed
            error: Error message if failed
        """
        ...
    
    @abstractmethod
    def record_execution_event(
        self,
        execution_id: str,
        event_type: str,
        event_data: dict[str, Any],
        node_id: NodeID | None = None
    ) -> None:
        """Record an execution event.
        
        Args:
            execution_id: The execution ID
            event_type: Type of event
            event_data: Event details
            node_id: Associated node if applicable
        """
        ...
    
    # Lifecycle Management
    
    @abstractmethod
    def mark_execution_completed(
        self,
        execution_id: str,
        final_outputs: dict[str, Any] | None = None
    ) -> None:
        """Mark an execution as completed.
        
        Args:
            execution_id: The execution ID
            final_outputs: Final output values
        """
        ...
    
    @abstractmethod
    def mark_execution_failed(
        self,
        execution_id: str,
        error: str,
        node_id: NodeID | None = None
    ) -> None:
        """Mark an execution as failed.
        
        Args:
            execution_id: The execution ID
            error: Error description
            node_id: Node that caused the failure
        """
        ...
    
    @abstractmethod
    def cancel_execution(self, execution_id: str) -> None:
        """Cancel a running execution.
        
        Args:
            execution_id: The execution ID
        """
        ...
    
    @abstractmethod
    def cleanup_execution(self, execution_id: str) -> None:
        """Clean up resources for an execution.
        
        Args:
            execution_id: The execution ID
        """
        ...
    
    # Checkpointing and Recovery
    
    @abstractmethod
    def create_checkpoint(
        self,
        execution_id: str,
        checkpoint_name: str | None = None
    ) -> str:
        """Create a checkpoint of current execution state.
        
        Args:
            execution_id: The execution ID
            checkpoint_name: Optional checkpoint name
            
        Returns:
            Checkpoint ID
        """
        ...
    
    @abstractmethod
    def restore_checkpoint(
        self,
        execution_id: str,
        checkpoint_id: str
    ) -> ExecutionContext:
        """Restore execution state from a checkpoint.
        
        Args:
            execution_id: The execution ID
            checkpoint_id: The checkpoint to restore
            
        Returns:
            Restored execution context
        """
        ...
    
    @abstractmethod
    def list_checkpoints(self, execution_id: str) -> list[dict[str, Any]]:
        """List available checkpoints for an execution.
        
        Args:
            execution_id: The execution ID
            
        Returns:
            List of checkpoint metadata
        """
        ...