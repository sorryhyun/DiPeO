"""
Refactored execution runtime showing how to reduce monolithic design.

This is an example of how ExecutionRuntime could be refactored using:
1. Extracted components for specific responsibilities
2. Simplified async handling without wrapper duplication
3. Clear separation of concerns
"""

import logging
import threading
from typing import TYPE_CHECKING, Any, Optional, Union

from dipeo.core.dynamic.execution_context import ExecutionContext
from dipeo.core.execution.execution_tracker import ExecutionTracker
from dipeo.core.execution.node_output import NodeOutputProtocol
from dipeo.models import (
    ExecutionState,
    NodeExecutionStatus,
    NodeID,
    NodeState,
)

from dipeo.application.execution.states.node_readiness_checker import NodeReadinessChecker
from dipeo.application.execution.states.state_transition_manager import StateTransitionManager
from dipeo.application.execution.states.execution_state_persistence import ExecutionStatePersistence

if TYPE_CHECKING:
    from dipeo.application.unified_service_registry import UnifiedServiceRegistry, ServiceKey
    from dipeo.core.static.executable_diagram import ExecutableDiagram, ExecutableNode

logger = logging.getLogger(__name__)


class ExecutionRuntime(ExecutionContext):
    """Simplified execution runtime using extracted components.
    
    Key improvements:
    1. Delegates node readiness checking to NodeReadinessChecker
    2. Delegates state transitions to StateTransitionManager
    3. Delegates persistence to ExecutionStatePersistence
    4. Removes async/sync wrapper duplication
    5. Cleaner, more focused interface
    """
    
    def __init__(
        self,
        diagram: "ExecutableDiagram",
        execution_state: ExecutionState,
        service_registry: "UnifiedServiceRegistry",
    ):
        self.diagram = diagram
        self._execution_id = execution_state.id
        self._diagram_id = execution_state.diagram_id
        self._service_registry = service_registry
        
        # Core state
        self._node_states: dict[NodeID, NodeState] = {}
        self._variables: dict[str, Any] = {}
        self._current_node_id: list[Optional[NodeID]] = [None]  # Mutable reference
        self.metadata: dict[str, Any] = {}  # Metadata for execution context
        
        # Components
        self._tracker = ExecutionTracker()
        self._state_lock = threading.Lock()
        
        # Initialize extracted components
        self._readiness_checker = NodeReadinessChecker(diagram, self._tracker)
        self._transition_manager = StateTransitionManager(
            diagram, self._tracker, self._state_lock
        )
        
        # Load state
        ExecutionStatePersistence.load_from_state(
            execution_state, 
            self._node_states, 
            self._tracker, 
            self._variables
        )
        
        # Initialize missing node states
        self._initialize_node_states()
    
    def _initialize_node_states(self) -> None:
        """Initialize states for any nodes not already tracked."""
        for node in self.diagram.nodes:
            if node.id not in self._node_states:
                self._node_states[node.id] = NodeState(
                    status=NodeExecutionStatus.PENDING,
                    node_id=node.id
                )
    
    # ========== Simplified Node Readiness ==========
    
    def get_ready_nodes(self) -> list["ExecutableNode"]:
        """Get all nodes that are ready to execute."""
        return [
            node for node in self.diagram.nodes
            if self._readiness_checker.is_node_ready(node, self._node_states)
        ]
    
    def is_complete(self) -> bool:
        """Check if execution is complete."""
        # Any nodes still running?
        if any(state.status == NodeExecutionStatus.RUNNING for state in self._node_states.values()):
            return False
        
        # Any nodes ready to run?
        return len(self.get_ready_nodes()) == 0
    
    # ========== Simplified State Transitions (No Wrappers!) ==========
    
    def transition_node_to_running(self, node_id: NodeID) -> int:
        """Transition a node to running state."""
        return self._transition_manager.transition_to_running(
            node_id, self._node_states, self._current_node_id
        )
    
    def transition_node_to_completed(
        self, 
        node_id: NodeID, 
        output: Any = None,
        token_usage: dict[str, int] = None
    ) -> None:
        """Transition a node to completed state."""
        self._transition_manager.transition_to_completed(
            node_id, self._node_states, self._current_node_id, output, token_usage
        )
    
    def transition_node_to_failed(self, node_id: NodeID, error: str) -> None:
        """Transition a node to failed state."""
        self._transition_manager.transition_to_failed(
            node_id, self._node_states, self._current_node_id, error
        )
    
    def transition_node_to_maxiter(self, node_id: NodeID, output: Optional[NodeOutputProtocol] = None) -> None:
        """Transition a node to max iterations reached state."""
        self._transition_manager.transition_to_maxiter(node_id, self._node_states, output)
    
    def transition_node_to_skipped(self, node_id: NodeID) -> None:
        """Transition a node to skipped state."""
        self._transition_manager.transition_to_skipped(node_id, self._node_states)
    
    def reset_node(self, node_id: NodeID) -> None:
        """Reset a node to pending state."""
        self._transition_manager.reset_node(node_id, self._node_states)
    
    # ========== ExecutionContext Protocol Implementation ==========
    
    def get_node_state(self, node_id: NodeID) -> Optional[NodeState]:
        """Get the execution state of a node."""
        return self._node_states.get(node_id)
    
    def set_node_state(self, node_id: NodeID, state: NodeState) -> None:
        """Set the execution state of a node."""
        self._node_states[node_id] = state
    
    def get_node_result(self, node_id: NodeID) -> Optional[dict[str, Any]]:
        """Get the execution result of a completed node."""
        protocol_output = self._tracker.get_last_output(node_id)
        if protocol_output:
            result = {"value": protocol_output.value}
            if hasattr(protocol_output, 'metadata') and protocol_output.metadata:
                result["metadata"] = protocol_output.metadata
            return result
        return None
    
    def get_completed_nodes(self) -> list[NodeID]:
        """Get list of all completed node IDs."""
        return [
            node_id for node_id, state in self._node_states.items()
            if state.status == NodeExecutionStatus.COMPLETED
        ]
    
    def get_variable(self, key: str) -> Any:
        """Get a variable from the execution context."""
        return self._variables.get(key)
    
    def set_variable(self, key: str, value: Any) -> None:
        """Set a variable in the execution context."""
        with self._state_lock:
            self._variables[key] = value
    
    def get_node_execution_count(self, node_id: NodeID) -> int:
        """Get the execution count for a node."""
        return self._tracker.get_execution_count(node_id)
    
    # ========== Service Access ==========
    
    def get_service(self, service_key: Union[str, "ServiceKey"]) -> Any:
        """Get a service from the registry."""
        from dipeo.application.unified_service_registry import ServiceKey
        
        if isinstance(service_key, ServiceKey):
            return self._service_registry.get(service_key.name)
        return self._service_registry.get(service_key)
    
    @property
    def service_registry(self) -> "UnifiedServiceRegistry":
        """Get the service registry."""
        return self._service_registry
    
    # ========== Input Resolution ==========
    
    def resolve_inputs(self, node: "ExecutableNode") -> dict[str, Any]:
        """Resolve all inputs for a node."""
        from dipeo.application.execution.input.typed_input_resolution import (
            TypedInputResolutionService,
        )
        from dipeo.core.static.generated_nodes import PersonJobNode
        
        # Create typed input resolution service
        typed_input_service = TypedInputResolutionService()
        
        # Get memory config if applicable
        node_memory_config = None
        if isinstance(node, PersonJobNode) and node.memory_config:
            node_memory_config = node.memory_config
        
        # Collect protocol outputs
        node_outputs_dict = {}
        for n in self.diagram.nodes:
            protocol_output = self._tracker.get_last_output(n.id)
            if protocol_output:
                node_outputs_dict[str(n.id)] = protocol_output
        
        # Resolve inputs
        return typed_input_service.resolve_inputs_for_node(
            node_id=str(node.id),
            node_type=node.type,
            diagram=self.diagram,
            node_outputs=node_outputs_dict,
            node_exec_counts={
                str(node_id): self._tracker.get_execution_count(node_id) 
                for node_id in self._node_states.keys()
            },
            node_memory_config=node_memory_config
        )
    
    # ========== Persistence ==========
    
    def to_execution_state(self) -> ExecutionState:
        """Convert runtime state to ExecutionState for persistence."""
        return ExecutionStatePersistence.save_to_state(
            self._execution_id,
            self._diagram_id,
            self.diagram,
            self._node_states,
            self._tracker,
            self._variables
        )
    
    # ========== Convenience Methods ==========
    
    def get_node(self, node_id: NodeID) -> Optional["ExecutableNode"]:
        """Get a node by ID from the diagram."""
        return self.diagram.get_node(node_id)
    
    def get_node_output(self, node_id: str) -> Any:
        """Get the output value of a node."""
        protocol_output = self._tracker.get_last_output(NodeID(node_id))
        return protocol_output.value if protocol_output else None
    
    def get_execution_summary(self) -> dict[str, Any]:
        """Get execution summary from the tracker."""
        return self._tracker.get_execution_summary()
    
    def has_running_nodes(self) -> bool:
        """Check if any nodes are currently running."""
        return any(
            state.status == NodeExecutionStatus.RUNNING 
            for state in self._node_states.values()
        )
    
    def count_nodes_by_status(self, statuses: list[str]) -> int:
        """Count nodes that have any of the given statuses."""
        status_enums = [NodeExecutionStatus[status] for status in statuses]
        return sum(
            1 for state in self._node_states.values()
            if state.status in status_enums
        )
    
    def update_node_state_without_tracker(self, node_id: NodeID, output: Any) -> None:
        """Update node state and store output without calling tracker.
        
        This is used when the tracker has already been updated elsewhere 
        (e.g., by ModernNodeExecutor).
        """
        state = self._node_states.get(node_id)
        if state and output:
            # Convert output to dict format if needed
            if hasattr(output, 'to_dict'):
                output_dict = output.to_dict()
            elif hasattr(output, 'value'):
                output_dict = {"value": output.value}
                if hasattr(output, 'metadata'):
                    output_dict["metadata"] = output.metadata
            else:
                output_dict = {"value": output}
            
            # Store the output in the node state if it has a place for it
            if hasattr(state, 'output'):
                state.output = output_dict
    
    @property
    def current_node_id(self) -> Optional[NodeID]:
        """Get the currently executing node ID."""
        return self._current_node_id[0]
    
    @property
    def diagram_id(self) -> str:
        """Get diagram ID."""
        return str(self._diagram_id) if self._diagram_id else ""
    
    @property
    def execution_id(self) -> str:
        """Get execution ID."""
        return str(self._execution_id)