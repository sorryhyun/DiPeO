"""Typed execution context with unified state management.

This module provides a concrete implementation of the ExecutionContext protocol
that manages all execution state, coordinates state transitions, and provides
a clean API for both the execution engine and node handlers.
"""

import asyncio
import logging
import threading
import time
from contextlib import contextmanager
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Optional

from dipeo.application.execution.states.execution_state_persistence import ExecutionStatePersistence
from dipeo.application.execution.states.node_readiness_checker import NodeReadinessChecker
from dipeo.core.events import EventEmitter, EventType, ExecutionEvent
from dipeo.core.execution import ExecutionContext as ExecutionContextProtocol
from dipeo.core.execution.execution_tracker import CompletionStatus, ExecutionTracker
from dipeo.core.execution.node_output import NodeOutputProtocol
from dipeo.core.execution.runtime_resolver import RuntimeResolver
from dipeo.diagram_generated import (
    ExecutionState,
    Status,
    NodeID,
    NodeState,
)
from dipeo.domain.diagram.models.executable_diagram import ExecutableDiagram, ExecutableNode

if TYPE_CHECKING:
    from dipeo.application.bootstrap import Container
    from dipeo.application.registry import ServiceRegistry

logger = logging.getLogger(__name__)


@dataclass
class TypedExecutionContext(ExecutionContextProtocol):
    """Unified execution context managing all execution state and operations.
    
    This context provides:
    - Thread-safe state management
    - Node state transitions
    - Input/output resolution
    - Event emission
    - Service access
    - Execution tracking
    """
    
    # Core identifiers
    execution_id: str
    diagram_id: str
    diagram: ExecutableDiagram
    
    # State management (private to enforce encapsulation)
    _node_states: dict[NodeID, NodeState] = field(default_factory=dict)
    _tracker: ExecutionTracker = field(default_factory=ExecutionTracker)
    _readiness_checker: Optional[NodeReadinessChecker] = None
    _state_lock: threading.Lock = field(default_factory=threading.Lock)
    
    # Runtime data
    _variables: dict[str, Any] = field(default_factory=dict)
    _metadata: dict[str, Any] = field(default_factory=dict)
    _current_node_id: Optional[NodeID] = None
    
    # Node metadata storage
    _node_metadata: dict[NodeID, dict[str, Any]] = field(default_factory=dict)
    
    # Dynamic control flow
    _branch_decisions: dict[NodeID, str] = field(default_factory=dict)
    _loop_states: dict[NodeID, bool] = field(default_factory=dict)
    
    # Dependencies
    service_registry: Optional["ServiceRegistry"] = None
    runtime_resolver: Optional[RuntimeResolver] = None
    event_bus: Optional[EventEmitter] = None
    container: Optional["Container"] = None
    
    def __post_init__(self):
        """Initialize readiness checker after dataclass initialization."""
        if self._readiness_checker is None:
            self._readiness_checker = NodeReadinessChecker(self.diagram, self._tracker)
    
    # ========== Node State Queries ==========
    
    def get_node_state(self, node_id: NodeID) -> NodeState | None:
        """Get the current state of a node."""
        with self._state_lock:
            return self._node_states.get(node_id)
    
    def get_node_result(self, node_id: NodeID) -> dict[str, Any] | None:
        """Get the execution result of a completed node."""
        protocol_output = self._tracker.get_last_output(node_id)
        if protocol_output:
            result = {"value": protocol_output.value}
            if hasattr(protocol_output, 'metadata') and protocol_output.metadata:
                result["metadata"] = protocol_output.metadata
            return result
        return None
    
    def get_node_output(self, node_id: NodeID) -> NodeOutputProtocol | None:
        """Get the typed output of a completed node."""
        return self._tracker.get_last_output(node_id)
    
    # ========== Execution Status Queries ==========
    
    def get_completed_nodes(self) -> list[NodeID]:
        """Get all nodes that have completed execution."""
        with self._state_lock:
            return [
                node_id for node_id, state in self._node_states.items()
                if state.status == Status.COMPLETED
            ]
    
    def get_ready_nodes(self) -> list[NodeID]:
        """Get nodes that are ready to execute (all dependencies met)."""
        with self._state_lock:
            return [
                node.id for node in self.diagram.nodes
                if self._readiness_checker.is_node_ready(node, self._node_states)
            ]
    
    def get_running_nodes(self) -> list[NodeID]:
        """Get nodes currently in execution."""
        with self._state_lock:
            return [
                node_id for node_id, state in self._node_states.items()
                if state.status == Status.RUNNING
            ]
    
    def get_failed_nodes(self) -> list[NodeID]:
        """Get nodes that failed during execution."""
        with self._state_lock:
            return [
                node_id for node_id, state in self._node_states.items()
                if state.status == Status.FAILED
            ]
    
    def get_node_execution_count(self, node_id: NodeID) -> int:
        """Get the number of times a node has been executed."""
        return self._tracker.get_execution_count(node_id)
    
    # ========== State Transitions ==========
    
    def transition_node_to_running(self, node_id: NodeID) -> int:
        """Transition a node to running state. Returns execution count."""
        with self._state_lock:
            self._node_states[node_id] = NodeState(status=Status.RUNNING)
            self._tracker.start_execution(node_id)
            return self._tracker.get_execution_count(node_id)
    
    def transition_node_to_completed(self, node_id: NodeID, output: Any = None, token_usage: dict[str, int] | None = None) -> None:
        """Transition a node to completed state with output."""
        with self._state_lock:
            self._node_states[node_id] = NodeState(status=Status.COMPLETED)
            self._tracker.complete_execution(
                node_id, 
                CompletionStatus.SUCCESS, 
                output=output,
                token_usage=token_usage
            )
    
    def transition_node_to_failed(self, node_id: NodeID, error: str) -> None:
        """Transition a node to failed state with error message."""
        with self._state_lock:
            self._node_states[node_id] = NodeState(
                status=Status.FAILED,
                error=error
            )
            self._tracker.complete_execution(
                node_id,
                CompletionStatus.FAILED,
                error=error
            )
    
    def transition_node_to_maxiter(self, node_id: NodeID, output: Optional[NodeOutputProtocol] = None) -> None:
        """Transition a node to max iterations state."""
        with self._state_lock:
            self._node_states[node_id] = NodeState(status=Status.MAXITER_REACHED)
            self._tracker.complete_execution(
                node_id,
                CompletionStatus.MAX_ITER,
                output=output
            )
    
    def transition_node_to_skipped(self, node_id: NodeID) -> None:
        """Transition a node to skipped state."""
        with self._state_lock:
            self._node_states[node_id] = NodeState(status=Status.SKIPPED)
            self._tracker.complete_execution(
                node_id,
                CompletionStatus.SKIPPED
            )
    
    def reset_node(self, node_id: NodeID) -> None:
        """Reset a node to initial state."""
        with self._state_lock:
            self._node_states[node_id] = NodeState(status=Status.PENDING)
    
    # ========== Runtime Context ==========
    
    def get_execution_metadata(self) -> dict[str, Any]:
        """Get global execution metadata."""
        return self._metadata.copy()
    
    def set_execution_metadata(self, key: str, value: Any) -> None:
        """Set a value in global execution metadata."""
        self._metadata[key] = value
    
    def get_node_metadata(self, node_id: NodeID) -> dict[str, Any]:
        """Get metadata for a specific node."""
        return self._node_metadata.get(node_id, {}).copy()
    
    def set_node_metadata(self, node_id: NodeID, key: str, value: Any) -> None:
        """Set metadata for a specific node."""
        if node_id not in self._node_metadata:
            self._node_metadata[node_id] = {}
        self._node_metadata[node_id][key] = value
    
    # ========== Dynamic Control Flow ==========
    
    def mark_branch_taken(self, node_id: NodeID, branch: str) -> None:
        """Mark which branch was taken from a conditional node."""
        self._branch_decisions[node_id] = branch
    
    def get_branch_taken(self, node_id: NodeID) -> str | None:
        """Get which branch was taken from a conditional node."""
        return self._branch_decisions.get(node_id)
    
    def is_loop_active(self, node_id: NodeID) -> bool:
        """Check if a loop node should continue iterating."""
        return self._loop_states.get(node_id, True)
    
    def update_loop_state(self, node_id: NodeID, should_continue: bool) -> None:
        """Update the iteration state of a loop node."""
        self._loop_states[node_id] = should_continue
    
    # ========== Additional Context Methods ==========
    
    def get_variable(self, name: str) -> Any:
        """Get a variable value."""
        return self._variables.get(name)
    
    def set_variable(self, name: str, value: Any) -> None:
        """Set a variable value."""
        self._variables[name] = value
    
    def get_variables(self) -> dict[str, Any]:
        """Get all variables."""
        return self._variables.copy()
    
    @property
    def current_node_id(self) -> NodeID | None:
        """Get the currently executing node ID."""
        return self._current_node_id
    
    @contextmanager
    def executing_node(self, node_id: NodeID):
        """Context manager for node execution."""
        old_node = self._current_node_id
        self._current_node_id = node_id
        try:
            yield
        finally:
            self._current_node_id = old_node
    
    # ========== Execution Queries ==========
    
    def is_execution_complete(self) -> bool:
        """Check if execution is complete."""
        # Check if any endpoint nodes have been reached
        from dipeo.diagram_generated.generated_nodes import NodeType
        for node in self.diagram.nodes:
            if node.type == NodeType.ENDPOINT.value:
                node_state = self.get_node_state(node.id)
                if node_state and node_state.status in [Status.COMPLETED, Status.MAXITER_REACHED]:
                    return True
        
        # Check if any nodes are running
        if any(state.status == Status.RUNNING for state in self._node_states.values()):
            return False
        
        # Check if any nodes are ready
        return len(self.get_ready_nodes()) == 0
    
    def get_ready_executable_nodes(self) -> list[ExecutableNode]:
        """Get executable node objects that are ready to run."""
        ready_ids = self.get_ready_nodes()
        return [
            node for node in self.diagram.nodes
            if node.id in ready_ids
        ]
    
    def calculate_progress(self) -> dict[str, Any]:
        """Calculate execution progress."""
        total = len(self._node_states)
        completed = sum(
            1 for state in self._node_states.values()
            if state.status in [Status.COMPLETED, Status.MAXITER_REACHED]
        )
        
        return {
            "total_nodes": total,
            "completed_nodes": completed,
            "percentage": (completed / total * 100) if total > 0 else 0
        }
    
    # ========== Input Resolution ==========
    
    def resolve_node_inputs(self, node: ExecutableNode) -> dict[str, Any]:
        """Resolve inputs for a node using the runtime resolver."""
        if not self.runtime_resolver:
            return {}
        
        # Get incoming edges
        incoming_edges = [
            edge for edge in self.diagram.edges 
            if edge.target_node_id == node.id
        ]
        
        # Build resolver context (self implements the protocol)
        return self.runtime_resolver.resolve_node_inputs(
            node=node,
            incoming_edges=incoming_edges,
            context=self
        )
    
    # ========== Event Management ==========
    
    async def emit_event(self, event_type: EventType, data: dict[str, Any] | None = None) -> None:
        """Emit an event through the event bus."""
        if not self.event_bus:
            return
        
        event = ExecutionEvent(
            type=event_type,
            execution_id=self.execution_id,
            timestamp=time.time(),
            data=data or {}
        )
        
        await self.event_bus.emit(event)
    
    # ========== Service Access ==========
    
    def get_service(self, service_key: Any) -> Any:
        """Get a service from the registry."""
        if not self.service_registry:
            return None
        
        from dipeo.application.registry import ServiceKey
        if not isinstance(service_key, ServiceKey):
            service_key = ServiceKey(service_key)
        
        return self.service_registry.get(service_key)
    
    def create_sub_container(self, sub_execution_id: str, config_overrides: dict | None = None):
        """Create a sub-container for nested execution."""
        if self.container is None:
            return None
        
        return self.container.create_sub_container(
            parent_execution_id=self.execution_id,
            sub_execution_id=sub_execution_id,
            config_overrides=config_overrides or {}
        )
    
    # ========== State Persistence ==========
    
    def to_execution_state(self) -> ExecutionState:
        """Convert current context to ExecutionState for persistence."""
        # Create the execution state
        exec_state = ExecutionStatePersistence.save_to_state(
            self.execution_id,
            self.diagram_id,
            self.diagram,
            self._node_states,
            self._tracker
        )
        
        # Add variables (ExecutionState has this field)
        exec_state.variables = self._variables
        
        return exec_state
    
    @classmethod
    def from_execution_state(
        cls,
        execution_state: ExecutionState,
        diagram: ExecutableDiagram,
        service_registry: Optional["ServiceRegistry"] = None,
        runtime_resolver: Optional[RuntimeResolver] = None,
        event_bus: Optional[EventEmitter] = None,
        container: Optional["Container"] = None
    ) -> "TypedExecutionContext":
        """Create context from persisted execution state."""
        # Create new context
        context = cls(
            execution_id=str(execution_state.id),
            diagram_id=str(execution_state.diagram_id),
            diagram=diagram,
            service_registry=service_registry,
            runtime_resolver=runtime_resolver,
            event_bus=event_bus,
            container=container
        )
        
        # Load persisted state
        ExecutionStatePersistence.load_from_state(
            execution_state,
            context._node_states,
            context._tracker
        )
        
        # Initialize remaining nodes
        for node in diagram.nodes:
            if node.id not in context._node_states:
                context._node_states[node.id] = NodeState(
                    status=Status.PENDING
                )
        
        # Load variables (metadata is not persisted in ExecutionState)
        context._variables = execution_state.variables or {}
        context._metadata = {}  # Metadata is not persisted
        
        return context
    
    # ========== Handler Support Methods ==========
    
    def get_execution_summary(self) -> dict[str, Any]:
        """Get execution summary from tracker."""
        return self._tracker.get_execution_summary()
    
    def count_nodes_by_status(self, statuses: list[str]) -> int:
        """Count nodes by status."""
        status_enums = [Status[status] for status in statuses]
        with self._state_lock:
            return sum(
                1 for state in self._node_states.values()
                if state.status in status_enums
            )
    
    def has_running_nodes(self) -> bool:
        """Check if any nodes are currently running."""
        return len(self.get_running_nodes()) > 0
    
    def get_node(self, node_id: NodeID) -> Optional[ExecutableNode]:
        """Get node by ID from diagram."""
        return self.diagram.get_node(node_id)
    
    def is_first_execution(self, node_id: NodeID) -> bool:
        """Check if this is the first execution of a node."""
        return self.get_node_execution_count(node_id) <= 1