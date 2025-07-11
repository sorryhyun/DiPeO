"""
Unified execution coordinator that merges state management functionality.

This module combines the functionality of ExecutionStateManager and ExecutionStateMachine
into a single coordinator that implements the core ExecutionCoordinator protocol.
It provides both high-level execution tracking and domain-level state transitions.
"""

import logging
from typing import Dict, Any, Optional, Set, List, TYPE_CHECKING
from datetime import datetime

from dipeo.models import (
    NodeID,
    NodeState, 
    NodeExecutionStatus,
    ExecutionState,
    ExecutionStatus,
    ExecutionID,
    NodeOutput,
    TokenUsage,
)
from dipeo.core.dynamic.execution_context import ExecutionCoordinator, ExecutionContext

if TYPE_CHECKING:
    from dipeo.container import Container
    from dipeo.application.unified_service_registry import UnifiedServiceRegistry

logger = logging.getLogger(__name__)


class UnifiedExecutionCoordinator(ExecutionCoordinator):
    """Unified coordinator for execution state management.
    
    This class merges the functionality of ExecutionStateManager (high-level tracking)
    and ExecutionStateMachine (domain state transitions) into a single cohesive
    implementation that follows the ExecutionCoordinator protocol.
    """
    
    def __init__(
        self, 
        container: Optional["Container"] = None,
        service_registry: Optional["UnifiedServiceRegistry"] = None
    ):
        """Initialize the execution coordinator.
        
        Args:
            container: Optional DI container for service access
            service_registry: Optional service registry for handler access
        """
        self._container = container
        self._service_registry = service_registry
        
        # Execution tracking (from ExecutionStateManager)
        self._executions: Dict[str, ExecutionContext] = {}
        self._execution_states: Dict[str, ExecutionState] = {}
        
        # Node execution tracking
        self._node_results: Dict[str, Dict[NodeID, Any]] = {}
        self._execution_errors: Dict[str, Dict[NodeID, Exception]] = {}
        
    # ExecutionCoordinator Protocol Implementation
    
    async def start_execution(
        self,
        diagram_id: str,
        options: Dict[str, Any]
    ) -> ExecutionContext:
        """Start a new diagram execution.
        
        Creates a new execution context and initializes the execution state.
        """
        from dipeo.application.execution.context import UnifiedExecutionContext
        import uuid
        
        # Generate execution ID
        execution_id = options.get("execution_id", str(uuid.uuid4()))
        
        # Create initial execution state
        execution_state = ExecutionState(
            id=ExecutionID(execution_id),
            status=ExecutionStatus.PENDING,
            diagram_id=diagram_id,
            started_at=datetime.utcnow().isoformat(),
            node_states={},
            node_outputs={},
            token_usage=TokenUsage(input=0, output=0),
            variables={},
            is_active=False
        )
        
        # Transition to running
        self._transition_to_running(execution_state)
        
        # Create execution context
        context = UnifiedExecutionContext(
            execution_state=execution_state,
            service_registry=self._service_registry,
            container=self._container
        )
        
        # Store references
        self._executions[execution_id] = context
        self._execution_states[execution_id] = execution_state
        self._node_results[execution_id] = {}
        self._execution_errors[execution_id] = {}
        
        logger.info(f"Started execution {execution_id} for diagram {diagram_id}")
        return context
    
    async def execute_node(
        self,
        node_id: NodeID,
        context: ExecutionContext
    ) -> Dict[str, Any]:
        """Execute a specific node within the context.
        
        This method would typically delegate to node handlers, but here
        we focus on state management aspects.
        """
        execution_id = context.get_execution_id()
        execution_state = self._execution_states.get(execution_id)
        
        if not execution_state:
            raise ValueError(f"No execution state found for {execution_id}")
        
        # Initialize node state if needed
        if str(node_id) not in execution_state.node_states:
            self._initialize_node_state(
                execution_state, 
                str(node_id),
                node_type=str(context.get_node_state(node_id).status if context.get_node_state(node_id) else "job")
            )
        
        # Mark node as running
        node_state = execution_state.node_states[str(node_id)]
        node_state.status = NodeExecutionStatus.RUNNING
        node_state.started_at = datetime.utcnow().isoformat()
        
        # Update context
        context.set_current_node(node_id)
        context.set_node_state(node_id, node_state)
        
        # In a real implementation, this would delegate to node handlers
        # For now, return empty result
        return {"status": "executed"}
    
    async def complete_execution(
        self,
        context: ExecutionContext,
        success: bool,
        error: Optional[Exception] = None
    ) -> None:
        """Mark an execution as complete."""
        execution_id = context.get_execution_id()
        execution_state = self._execution_states.get(execution_id)
        
        if not execution_state:
            raise ValueError(f"No execution state found for {execution_id}")
        
        if success:
            self._transition_to_completed(execution_state)
        else:
            self._transition_to_failed(
                execution_state, 
                str(error) if error else "Execution failed"
            )
        
        # Clean up tracking
        if execution_id in self._executions:
            del self._executions[execution_id]
        
        logger.info(f"Completed execution {execution_id} - Success: {success}")
    
    def can_execute_node(
        self,
        node_id: NodeID,
        context: ExecutionContext
    ) -> bool:
        """Check if a node is ready to execute based on dependencies."""
        execution_id = context.get_execution_id()
        execution_state = self._execution_states.get(execution_id)
        
        if not execution_state:
            return False
        
        return self._can_node_execute(execution_state, str(node_id))
    
    # State Management Methods (from ExecutionStateMachine)
    
    def _transition_to_running(self, state: ExecutionState) -> None:
        """Transition execution to running status."""
        if state.status != ExecutionStatus.PENDING:
            raise ValueError(f"Cannot transition to RUNNING from {state.status}")
        state.status = ExecutionStatus.RUNNING
        state.started_at = datetime.utcnow().isoformat()
        state.is_active = True
    
    def _transition_to_completed(self, state: ExecutionState) -> None:
        """Transition execution to completed status."""
        # If already completed, just return without error
        if state.status == ExecutionStatus.COMPLETED:
            return
        if state.status != ExecutionStatus.RUNNING:
            raise ValueError(f"Cannot transition to COMPLETED from {state.status}")
        state.status = ExecutionStatus.COMPLETED
        state.ended_at = datetime.utcnow().isoformat()
        state.is_active = False
        
        # Calculate duration
        if state.started_at:
            start = datetime.fromisoformat(state.started_at.replace('Z', '+00:00'))
            end = datetime.utcnow()
            state.duration_seconds = (end - start).total_seconds()
    
    def _transition_to_failed(self, state: ExecutionState, error: str) -> None:
        """Transition execution to failed status."""
        # If already in a terminal state, don't try to transition
        if state.status in [ExecutionStatus.FAILED, ExecutionStatus.COMPLETED, ExecutionStatus.ABORTED]:
            return
        if state.status not in [ExecutionStatus.PENDING, ExecutionStatus.RUNNING]:
            raise ValueError(f"Cannot transition to FAILED from {state.status}")
        state.status = ExecutionStatus.FAILED
        state.ended_at = datetime.utcnow().isoformat()
        state.is_active = False
        state.error = error
    
    def _initialize_node_state(
        self,
        execution_state: ExecutionState,
        node_id: str,
        node_type: str,
        max_iterations: int = 1
    ) -> NodeState:
        """Initialize a new node state."""
        node_state = NodeState(
            status=NodeExecutionStatus.PENDING,
            started_at=datetime.utcnow().isoformat(),
            metadata={
                "exec_count": 0,
                "max_iterations": max_iterations,
                "node_type": node_type
            }
        )
        execution_state.node_states[node_id] = node_state
        return node_state
    
    def _can_node_execute(self, execution_state: ExecutionState, node_id: str) -> bool:
        """Check if a node can execute."""
        node_state = execution_state.node_states.get(node_id)
        if not node_state:
            return True  # New nodes can execute
        
        # Check if completed or failed
        if node_state.status in [NodeExecutionStatus.COMPLETED, NodeExecutionStatus.FAILED]:
            logger.debug(f"Node {node_id} cannot execute - status is {node_state.status}")
            return False
        
        # Check iteration count
        if node_state.metadata:
            exec_count = node_state.metadata.get("exec_count", 0)
            max_iterations = node_state.metadata.get("max_iterations", 1)
            can_execute = exec_count < max_iterations
            logger.debug(f"Node {node_id} iteration check: exec_count={exec_count}, max_iterations={max_iterations}, can_execute={can_execute}")
            return can_execute
        
        return True
    
    # Public State Transition Methods (ExecutionStateMachine compatibility)
    
    def transition_to_running(self, state: ExecutionState) -> None:
        """Public method to transition execution to running status."""
        return self._transition_to_running(state)
    
    def transition_to_completed(self, state: ExecutionState) -> None:
        """Public method to transition execution to completed status."""
        return self._transition_to_completed(state)
    
    def transition_to_failed(self, state: ExecutionState, error: str) -> None:
        """Public method to transition execution to failed status."""
        return self._transition_to_failed(state, error)
    
    def initialize_node_state(
        self,
        execution_state: ExecutionState,
        node_id: str,
        node_type: str,
        max_iterations: int = 1
    ) -> NodeState:
        """Public method to initialize a new node state."""
        return self._initialize_node_state(execution_state, node_id, node_type, max_iterations)
    
    def get_node_exec_count(self, execution_state: ExecutionState, node_id: str) -> int:
        """Get the execution count for a node."""
        node_state = execution_state.node_states.get(node_id)
        if not node_state or not node_state.metadata:
            return 0
        return node_state.metadata.get("exec_count", 0)
    
    def can_node_execute(self, execution_state: ExecutionState, node_id: str) -> bool:
        """Check if a node can execute."""
        return self._can_node_execute(execution_state, node_id)
    
    def get_node_exec_count(self, execution_state: ExecutionState, node_id: str) -> int:
        """Get execution count for a node."""
        node_state = execution_state.node_states.get(node_id)
        if not node_state or not node_state.metadata:
            return 0
        return node_state.metadata.get("exec_count", 0)
    
    def get_executed_nodes(self, execution_state: ExecutionState) -> Set[str]:
        """Get set of executed node IDs."""
        executed = set()
        for node_id, state in execution_state.node_states.items():
            if state.status in [NodeExecutionStatus.COMPLETED, NodeExecutionStatus.RUNNING]:
                executed.add(node_id)
        return executed
    
    def is_endpoint_executed(self, execution_state: ExecutionState) -> bool:
        """Check if any endpoint node has been executed."""
        for node_id, state in execution_state.node_states.items():
            if (state.metadata and 
                state.metadata.get("node_type") == "endpoint" and
                state.status == NodeExecutionStatus.COMPLETED):
                return True
        return False
    
    def execute_node_state(
        self,
        execution_state: ExecutionState,
        node_id: str,
        output: Optional[NodeOutput] = None
    ) -> None:
        """Mark a node as executed and update its state.
        
        This method provides compatibility with ExecutionStateMachine interface.
        """
        node_state = execution_state.node_states.get(node_id)
        if not node_state:
            raise ValueError(f"Node {node_id} not found in execution state")
        
        if not node_state.metadata:
            raise ValueError(f"Node {node_id} has no metadata")
        
        # Increment execution count
        exec_count = node_state.metadata.get("exec_count", 0)
        node_state.metadata["exec_count"] = exec_count + 1
        
        # Update status based on iterations
        max_iterations = node_state.metadata.get("max_iterations", 1)
        logger.debug(f"Node {node_id} execution: exec_count={node_state.metadata['exec_count']}, max_iterations={max_iterations}")
        if node_state.metadata["exec_count"] >= max_iterations:
            node_state.status = NodeExecutionStatus.COMPLETED
            node_state.ended_at = datetime.utcnow().isoformat()
            logger.debug(f"Node {node_id} marked as COMPLETED")
        else:
            node_state.status = NodeExecutionStatus.RUNNING
            logger.debug(f"Node {node_id} marked as RUNNING")
        
        # Update output
        if output:
            execution_state.node_outputs[node_id] = output
            node_state.output = output
    
    # High-level State Tracking Methods (from ExecutionStateManager)
    
    def mark_node_complete(
        self, 
        execution_id: str, 
        node_id: NodeID, 
        result: Any,
        output: Optional[NodeOutput] = None
    ) -> None:
        """Mark a node as completed and store its result."""
        logger.debug(f"mark_node_complete called for node {node_id}")
        execution_state = self._execution_states.get(execution_id)
        if not execution_state:
            raise ValueError(f"No execution state found for {execution_id}")
        
        node_state = execution_state.node_states.get(str(node_id))
        if not node_state:
            raise ValueError(f"Node {node_id} not found in execution state")
        
        # Update node state
        if node_state.metadata:
            exec_count = node_state.metadata.get("exec_count", 0)
            node_state.metadata["exec_count"] = exec_count + 1
            
            max_iterations = node_state.metadata.get("max_iterations", 1)
            if node_state.metadata["exec_count"] >= max_iterations:
                node_state.status = NodeExecutionStatus.COMPLETED
                node_state.ended_at = datetime.utcnow().isoformat()
            else:
                node_state.status = NodeExecutionStatus.RUNNING
        
        # Store result and output
        if execution_id not in self._node_results:
            self._node_results[execution_id] = {}
        self._node_results[execution_id][node_id] = result
        
        if output:
            execution_state.node_outputs[str(node_id)] = output
            node_state.output = output
        
        # Update context if available
        context = self._executions.get(execution_id)
        if context:
            context.set_node_state(node_id, node_state)
            context.set_node_result(node_id, {"value": result})
        
        logger.info(f"Node {node_id} marked as complete in execution {execution_id}")
    
    def mark_node_error(
        self, 
        execution_id: str, 
        node_id: NodeID, 
        error: Exception
    ) -> None:
        """Mark a node as having encountered an error."""
        execution_state = self._execution_states.get(execution_id)
        if not execution_state:
            raise ValueError(f"No execution state found for {execution_id}")
        
        node_state = execution_state.node_states.get(str(node_id))
        if not node_state:
            node_state = self._initialize_node_state(
                execution_state, str(node_id), "unknown"
            )
        
        # Update node state
        node_state.status = NodeExecutionStatus.FAILED
        node_state.ended_at = datetime.utcnow().isoformat()
        node_state.error = str(error)
        
        # Store error
        if execution_id not in self._execution_errors:
            self._execution_errors[execution_id] = {}
        self._execution_errors[execution_id][node_id] = error
        
        # Update context if available
        context = self._executions.get(execution_id)
        if context:
            context.set_node_state(node_id, node_state)
        
        logger.error(f"Node {node_id} encountered error in execution {execution_id}: {error}")
    
    def get_execution_progress(self, execution_id: str) -> Dict[str, Any]:
        """Get the current execution progress."""
        execution_state = self._execution_states.get(execution_id)
        if not execution_state:
            return {"error": "Execution not found"}
        
        completed_nodes = []
        for node_id, node_state in execution_state.node_states.items():
            if node_state.status == NodeExecutionStatus.COMPLETED:
                completed_nodes.append(node_id)
        
        errors = self._execution_errors.get(execution_id, {})
        
        return {
            "execution_id": execution_id,
            "status": execution_state.status.value,
            "completed_count": len(completed_nodes),
            "completed_nodes": completed_nodes,
            "has_errors": len(errors) > 0,
            "error_count": len(errors),
            "start_time": execution_state.started_at,
            "end_time": execution_state.ended_at,
            "duration_seconds": execution_state.duration_seconds,
            "is_active": execution_state.is_active
        }
    
    def get_node_execution_count(self, execution_id: str, node_id: NodeID) -> int:
        """Get execution count for a specific node."""
        execution_state = self._execution_states.get(execution_id)
        if not execution_state:
            return 0
        
        node_state = execution_state.node_states.get(str(node_id))
        if not node_state or not node_state.metadata:
            return 0
        
        return node_state.metadata.get("exec_count", 0)
    
    def get_executed_nodes(self, execution_state: ExecutionState) -> Set[str]:
        """Get set of executed node IDs for an execution."""
        if not execution_state:
            return set()
        
        executed = set()
        for node_id, node_state in execution_state.node_states.items():
            if node_state.metadata and node_state.metadata.get("exec_count", 0) > 0:
                executed.add(node_id)
        return executed
    
    def is_endpoint_executed(self, execution_state: ExecutionState) -> bool:
        """Check if any endpoint node has been executed."""
        if not execution_state:
            return False
        
        for node_id, node_state in execution_state.node_states.items():
            if node_state.metadata and node_state.metadata.get("node_type") == "endpoint":
                if node_state.metadata.get("exec_count", 0) > 0:
                    return True
        return False