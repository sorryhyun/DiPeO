"""Protocol for observing and monitoring runtime execution events."""

from typing import Protocol, Dict, Any, Optional, List
from abc import abstractmethod
from datetime import datetime
from dipeo.models import NodeID, NodeState, NodeType


class ExecutionObserver(Protocol):
    """Observes execution events for monitoring and debugging."""
    
    @abstractmethod
    async def on_execution_start(
        self,
        execution_id: str,
        diagram_id: Optional[str],
        metadata: Dict[str, Any]
    ) -> None:
        """Called when diagram execution begins.
        
        Args:
            execution_id: The unique execution identifier
            diagram_id: Optional diagram identifier
            metadata: Execution metadata (options, timestamp, etc.)
        """
        ...
    
    @abstractmethod
    async def on_node_start(
        self,
        execution_id: str,
        node_id: NodeID,
        node_type: NodeType,
        inputs: Dict[str, Any]
    ) -> None:
        """Called when a node begins execution.
        
        Args:
            execution_id: The execution identifier
            node_id: The node that is starting
            node_type: The type of the node
            inputs: The inputs provided to the node
        """
        ...
    
    @abstractmethod
    async def on_node_complete(
        self,
        execution_id: str,
        node_id: NodeID,
        state: NodeState,
        outputs: Dict[str, Any],
        duration_ms: int
    ) -> None:
        """Called when a node completes execution.
        
        Args:
            execution_id: The execution identifier
            node_id: The node that completed
            state: The final state of the node
            outputs: The outputs produced by the node
            duration_ms: Execution duration in milliseconds
        """
        ...
    
    @abstractmethod
    async def on_node_error(
        self,
        execution_id: str,
        node_id: NodeID,
        error: Exception,
        retry_count: int
    ) -> None:
        """Called when a node encounters an error.
        
        Args:
            execution_id: The execution identifier
            node_id: The node that errored
            error: The exception that occurred
            retry_count: Number of retries attempted
        """
        ...
    
    @abstractmethod
    async def on_execution_complete(
        self,
        execution_id: str,
        success: bool,
        total_duration_ms: int,
        node_count: int
    ) -> None:
        """Called when diagram execution completes.
        
        Args:
            execution_id: The execution identifier
            success: Whether execution completed successfully
            total_duration_ms: Total execution time in milliseconds
            node_count: Number of nodes executed
        """
        ...
    
    @abstractmethod
    async def on_message_sent(
        self,
        execution_id: str,
        from_node: NodeID,
        to_node: NodeID,
        message_type: str,
        payload_size: int
    ) -> None:
        """Called when a message is sent between nodes.
        
        Args:
            execution_id: The execution identifier
            from_node: The sending node
            to_node: The receiving node
            message_type: Type of message
            payload_size: Size of the message payload in bytes
        """
        ...


class ExecutionMetrics(Protocol):
    """Collects and provides execution metrics."""
    
    @abstractmethod
    def record_node_execution(
        self,
        node_id: NodeID,
        node_type: NodeType,
        duration_ms: int,
        success: bool
    ) -> None:
        """Record metrics for a node execution.
        
        Args:
            node_id: The node that was executed
            node_type: The type of the node
            duration_ms: Execution duration in milliseconds
            success: Whether execution succeeded
        """
        ...
    
    @abstractmethod
    def get_node_metrics(self, node_id: NodeID) -> Dict[str, Any]:
        """Get execution metrics for a specific node.
        
        Args:
            node_id: The node to get metrics for
            
        Returns:
            Dictionary containing node metrics
        """
        ...
    
    @abstractmethod
    def get_execution_summary(self, execution_id: str) -> Dict[str, Any]:
        """Get summary metrics for an entire execution.
        
        Args:
            execution_id: The execution to summarize
            
        Returns:
            Dictionary containing execution summary
        """
        ...
    
    @abstractmethod
    def get_performance_stats(
        self,
        time_window_minutes: int = 60
    ) -> Dict[str, Any]:
        """Get performance statistics over a time window.
        
        Args:
            time_window_minutes: Time window to analyze
            
        Returns:
            Dictionary containing performance statistics
        """
        ...