"""State Store port interface."""

from typing import Any, Dict, List, Optional, Protocol, runtime_checkable


@runtime_checkable
class StateStorePort(Protocol):
    """Port for execution state persistence.
    
    This interface defines the contract for storing and retrieving
    execution state, node outputs, and execution history.
    """

    async def create_execution(
        self, execution_id: str, diagram_id: Optional[str] = None
    ) -> None:
        """Create a new execution record.
        
        Args:
            execution_id: Unique execution identifier
            diagram_id: Optional diagram identifier
        """
        ...

    async def get_execution(self, execution_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve execution state by ID.
        
        Args:
            execution_id: Execution to retrieve
            
        Returns:
            Execution state data or None if not found
        """
        ...

    async def update_status(
        self, execution_id: str, status: Any, error: Optional[str] = None
    ) -> None:
        """Update execution status.
        
        Args:
            execution_id: Execution to update
            status: New status (ExecutionStatus enum value)
            error: Optional error message
        """
        ...

    async def update_node_status(
        self, execution_id: str, node_id: str, status: Any, error: Optional[str] = None
    ) -> None:
        """Update node execution status.
        
        Args:
            execution_id: Parent execution ID
            node_id: Node to update
            status: New node status (NodeExecutionStatus enum value)
            error: Optional error message
        """
        ...

    async def update_node_output(
        self,
        execution_id: str,
        node_id: str,
        output: Any,
        token_usage: Optional[Any] = None,
    ) -> None:
        """Store node output and token usage.
        
        Args:
            execution_id: Parent execution ID
            node_id: Node that produced the output
            output: NodeOutput object
            token_usage: Optional TokenUsage object
        """
        ...

    async def list_executions(
        self, limit: int = 10, offset: int = 0
    ) -> List[Dict[str, Any]]:
        """List recent executions.
        
        Args:
            limit: Maximum number of executions to return
            offset: Number of executions to skip
            
        Returns:
            List of execution summaries
        """
        ...

    async def delete_execution(self, execution_id: str) -> None:
        """Delete an execution and all associated data.
        
        Args:
            execution_id: Execution to delete
        """
        ...