"""
Adapter to bridge application observers to core ExecutionObserver protocol.

This adapter allows existing application-layer observers to work with the
core execution framework by adapting between the two observer interfaces.
"""

from typing import Dict, Any, Optional, List
from datetime import datetime
from dipeo.models import NodeID, NodeState, NodeType

# Import both observer protocols
from dipeo.core.dynamic.execution_observer import ExecutionObserver as CoreExecutionObserver
from dipeo.application.execution.protocols import ExecutionObserver as ApplicationExecutionObserver


class CoreObserverAdapter(CoreExecutionObserver):
    """Adapts application observers to the core ExecutionObserver protocol.
    
    This adapter wraps application-layer observers and translates between
    the simpler application interface and the more detailed core interface.
    """
    
    def __init__(self, app_observers: List[ApplicationExecutionObserver]):
        """Initialize the adapter with application observers.
        
        Args:
            app_observers: List of application-layer observers to adapt
        """
        self._app_observers = app_observers
        self._start_times: Dict[NodeID, datetime] = {}
    
    async def on_execution_start(
        self,
        execution_id: str,
        diagram_id: Optional[str],
        metadata: Dict[str, Any]
    ) -> None:
        """Called when diagram execution begins.
        
        Delegates to application observers with simplified interface.
        """
        for observer in self._app_observers:
            await observer.on_execution_start(execution_id, diagram_id)
    
    async def on_node_start(
        self,
        execution_id: str,
        node_id: NodeID,
        node_type: NodeType,
        inputs: Dict[str, Any]
    ) -> None:
        """Called when a node begins execution.
        
        Stores start time and delegates to application observers.
        """
        # Store start time for duration calculation
        self._start_times[node_id] = datetime.utcnow()
        
        # Delegate to application observers (without extra params)
        for observer in self._app_observers:
            await observer.on_node_start(execution_id, str(node_id))
    
    async def on_node_complete(
        self,
        execution_id: str,
        node_id: NodeID,
        state: NodeState,
        outputs: Dict[str, Any],
        duration_ms: int
    ) -> None:
        """Called when a node completes execution.
        
        Updates state with timing info and delegates to application observers.
        """
        # Update state with end time if not set
        if not state.ended_at and node_id in self._start_times:
            state.ended_at = datetime.utcnow().isoformat()
        
        # Delegate to application observers
        for observer in self._app_observers:
            await observer.on_node_complete(execution_id, str(node_id), state)
        
        # Clean up start time
        self._start_times.pop(node_id, None)
    
    async def on_node_error(
        self,
        execution_id: str,
        node_id: NodeID,
        error: Exception,
        retry_count: int
    ) -> None:
        """Called when a node encounters an error.
        
        Converts exception to string and delegates to application observers.
        """
        error_str = str(error)
        if retry_count > 0:
            error_str = f"{error_str} (retry {retry_count})"
        
        for observer in self._app_observers:
            await observer.on_node_error(execution_id, str(node_id), error_str)
    
    async def on_execution_complete(
        self,
        execution_id: str,
        success: bool,
        total_duration_ms: int,
        node_count: int
    ) -> None:
        """Called when diagram execution completes.
        
        Delegates to appropriate application observer method based on success.
        """
        if success:
            # Call on_execution_complete for successful execution
            for observer in self._app_observers:
                await observer.on_execution_complete(execution_id)
        else:
            # Call on_execution_error for failed execution
            for observer in self._app_observers:
                if hasattr(observer, 'on_execution_error'):
                    await observer.on_execution_error(
                        execution_id, 
                        "Execution failed"
                    )
    
    async def on_message_sent(
        self,
        execution_id: str,
        from_node: NodeID,
        to_node: NodeID,
        message_type: str,
        payload_size: int
    ) -> None:
        """Called when a message is sent between nodes.
        
        Currently not used by application observers, so this is a no-op.
        """
        # Application observers don't have this method, so we skip it
        pass


class ApplicationObserverAdapter(ApplicationExecutionObserver):
    """Adapts core observers to the application ExecutionObserver protocol.
    
    This reverse adapter allows core-layer observers to be used in places
    that expect application-layer observers.
    """
    
    def __init__(self, core_observer: CoreExecutionObserver):
        """Initialize the adapter with a core observer.
        
        Args:
            core_observer: Core-layer observer to adapt
        """
        self._core_observer = core_observer
        self._execution_metadata: Dict[str, Dict[str, Any]] = {}
        self._node_states: Dict[str, NodeState] = {}
    
    async def on_execution_start(
        self, execution_id: str, diagram_id: Optional[str]
    ) -> None:
        """Called when execution starts.
        
        Adds default metadata and delegates to core observer.
        """
        metadata = {
            "started_at": datetime.utcnow().isoformat(),
            "diagram_id": diagram_id,
        }
        self._execution_metadata[execution_id] = metadata
        
        await self._core_observer.on_execution_start(
            execution_id, diagram_id, metadata
        )
    
    async def on_node_start(self, execution_id: str, node_id: str) -> None:
        """Called when a node starts.
        
        Adds default node type and inputs, delegates to core observer.
        """
        # We don't have node type or inputs, so use defaults
        await self._core_observer.on_node_start(
            execution_id,
            NodeID(node_id),
            NodeType.JOB,  # Default type
            {}  # Empty inputs
        )
    
    async def on_node_complete(
        self, execution_id: str, node_id: str, state: NodeState
    ) -> None:
        """Called when a node completes.
        
        Calculates duration and extracts outputs, delegates to core observer.
        """
        # Store state for later reference
        self._node_states[node_id] = state
        
        # Calculate duration if possible
        duration_ms = 0
        if state.started_at and state.ended_at:
            try:
                start = datetime.fromisoformat(state.started_at.replace('Z', '+00:00'))
                end = datetime.fromisoformat(state.ended_at.replace('Z', '+00:00'))
                duration_ms = int((end - start).total_seconds() * 1000)
            except:
                pass
        
        # Extract outputs from state
        outputs = {}
        if state.output:
            outputs = {"value": state.output.value}
            if state.output.metadata:
                outputs["metadata"] = state.output.metadata
        
        await self._core_observer.on_node_complete(
            execution_id,
            NodeID(node_id),
            state,
            outputs,
            duration_ms
        )
    
    async def on_node_error(
        self, execution_id: str, node_id: str, error: str
    ) -> None:
        """Called when a node errors.
        
        Converts string to exception and delegates to core observer.
        """
        await self._core_observer.on_node_error(
            execution_id,
            NodeID(node_id),
            Exception(error),
            0  # No retry count info
        )
    
    async def on_execution_complete(self, execution_id: str) -> None:
        """Called when execution completes successfully.
        
        Calculates metrics and delegates to core observer.
        """
        # Calculate total duration and node count
        metadata = self._execution_metadata.get(execution_id, {})
        total_duration_ms = 0
        if "started_at" in metadata:
            try:
                start = datetime.fromisoformat(metadata["started_at"])
                duration = datetime.utcnow() - start
                total_duration_ms = int(duration.total_seconds() * 1000)
            except:
                pass
        
        # Count nodes executed for this execution
        node_count = len([k for k in self._node_states.keys() 
                         if k.startswith(f"{execution_id}:")])
        
        await self._core_observer.on_execution_complete(
            execution_id,
            True,  # Success
            total_duration_ms,
            node_count
        )
        
        # Clean up metadata
        self._execution_metadata.pop(execution_id, None)
    
    async def on_execution_error(self, execution_id: str, error: str) -> None:
        """Called when execution fails.
        
        Delegates to core observer's on_execution_complete with failure.
        """
        # Similar to on_execution_complete but with success=False
        metadata = self._execution_metadata.get(execution_id, {})
        total_duration_ms = 0
        if "started_at" in metadata:
            try:
                start = datetime.fromisoformat(metadata["started_at"])
                duration = datetime.utcnow() - start
                total_duration_ms = int(duration.total_seconds() * 1000)
            except:
                pass
        
        node_count = len([k for k in self._node_states.keys() 
                         if k.startswith(f"{execution_id}:")])
        
        await self._core_observer.on_execution_complete(
            execution_id,
            False,  # Failed
            total_duration_ms,
            node_count
        )
        
        # Clean up metadata
        self._execution_metadata.pop(execution_id, None)