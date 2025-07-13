"""
Unified execution context implementing the core ExecutionContext protocol.

This provides a protocol-compliant implementation that bridges the application layer
with the core protocols, replacing the existing ApplicationExecutionContext with a
cleaner, more maintainable version.
"""

from typing import Dict, Any, Optional, List, TYPE_CHECKING
from dipeo.models import NodeID, NodeState, ExecutionState, NodeOutput, NodeExecutionStatus
from dipeo.core.dynamic.execution_context import ExecutionContext

if TYPE_CHECKING:
    from dipeo.container import Container
    from dipeo.application.unified_service_registry import UnifiedServiceRegistry


class UnifiedExecutionContext(ExecutionContext):
    """Protocol-compliant execution context implementation.
    
    This context manages the runtime state during diagram execution,
    providing full implementation of the core ExecutionContext protocol.
    """
    
    def __init__(
        self,
        execution_state: ExecutionState,
        service_registry: Optional["UnifiedServiceRegistry"] = None,
        container: Optional["Container"] = None,
        current_node_id: str = "",
        executed_nodes: Optional[List[str]] = None,
        exec_counts: Optional[Dict[str, int]] = None,
    ):
        """Initialize the unified execution context.
        
        This constructor is compatible with the existing ApplicationExecutionContext
        interface to ease migration.
        
        Args:
            execution_state: The execution state
            service_registry: Optional service registry (for compatibility)
            container: Optional DI container with all services
            current_node_id: ID of the currently executing node
            executed_nodes: List of node IDs that have been executed
            exec_counts: Dictionary of node execution counts
        """
        self._execution_id = execution_state.id
        self._execution_state = execution_state  # Store for compatibility
        self._service_registry: Optional["UnifiedServiceRegistry"] = service_registry
        self._container = container
        self._current_node: Optional[NodeID] = NodeID(current_node_id) if current_node_id else None
        self._executed_nodes = executed_nodes or []
        self._exec_counts = exec_counts or {}
        
        # Initialize state tracking
        self._node_states: Dict[NodeID, NodeState] = {}
        self._node_results: Dict[NodeID, Dict[str, Any]] = {}
        self._global_context: Dict[str, Any] = {}
        
        # Populate from execution state
        self._populate_from_state(execution_state)
    
    def _populate_from_state(self, state: ExecutionState) -> None:
        """Populate context from an existing execution state.
        
        Args:
            state: The execution state to populate from
        """
        if state.node_states:
            for node_id, node_state in state.node_states.items():
                self._node_states[NodeID(node_id)] = node_state
        
        if state.node_outputs:
            for node_id, output in state.node_outputs.items():
                # Convert NodeOutput to result dict
                result = {"value": output.value}
                if output.metadata:
                    result["metadata"] = output.metadata
                self._node_results[NodeID(node_id)] = result
        
        if state.variables:
            self._global_context.update(state.variables)
    
    # ExecutionContext Protocol Implementation
    
    def get_execution_id(self) -> str:
        """Get the unique identifier for this execution."""
        return self._execution_id
    
    def get_current_node(self) -> Optional[NodeID]:
        """Get the currently executing node."""
        return self._current_node
    
    def set_current_node(self, node_id: NodeID) -> None:
        """Set the currently executing node."""
        self._current_node = node_id
    
    def get_node_state(self, node_id: NodeID) -> Optional[NodeState]:
        """Get the execution state of a specific node."""
        return self._node_states.get(node_id)
    
    def set_node_state(self, node_id: NodeID, state: NodeState) -> None:
        """Set the execution state of a node."""
        self._node_states[node_id] = state
    
    def get_node_result(self, node_id: NodeID) -> Optional[Dict[str, Any]]:
        """Get the execution result of a completed node."""
        return self._node_results.get(node_id)
    
    def set_node_result(self, node_id: NodeID, result: Dict[str, Any]) -> None:
        """Store the result of a node execution."""
        self._node_results[node_id] = result
    
    def get_global_context(self) -> Dict[str, Any]:
        """Get the global execution context shared across all nodes."""
        return self._global_context.copy()
    
    def update_global_context(self, updates: Dict[str, Any]) -> None:
        """Update the global execution context."""
        self._global_context.update(updates)
    
    def get_completed_nodes(self) -> List[NodeID]:
        """Get list of all completed node IDs."""
        completed = []
        for node_id, state in self._node_states.items():
            if state.status == NodeExecutionStatus.COMPLETED:
                completed.append(node_id)
        return completed
    
    def is_node_complete(self, node_id: NodeID) -> bool:
        """Check if a node has completed execution."""
        state = self._node_states.get(node_id)
        return state is not None and state.status == NodeExecutionStatus.COMPLETED
    
    # Additional methods for compatibility with existing code
    
    def get_node_output(self, node_id: str) -> Any:
        """Get the output of a specific node.
        
        Compatible with ApplicationExecutionContext interface.
        """
        result = self.get_node_result(NodeID(node_id))
        if result:
            return result.get("value")
        
        # Check in execution state node outputs
        state = self.get_node_state(NodeID(node_id))
        if state and state.output:
            return state.output.value
        return None
    
    def get_variable(self, key: str) -> Any:
        """Get a variable from the execution context.
        
        Compatible with ApplicationExecutionContext interface.
        """
        return self._global_context.get(key)
    
    def get_service(self, service_name: str) -> Any:
        """Get a service by name.
        
        Compatible with ApplicationExecutionContext interface.
        """
        if self._service_registry:
            return self._service_registry.get(service_name)
        elif self._container:
            # Map service names to container paths
            service_mapping = {
                # Infrastructure services
                'llm_service': lambda: self._container.infra.llm_service(),
                'api_key_service': lambda: self._container.domain.api_key_service(),
                'file_service': lambda: self._container.infra.file_service(),
                'notion_service': lambda: self._container.infra.notion_service(),
                'api_integration_service': lambda: self._container.infra.api_service(),
                'diagram_loader': lambda: self._container.infra.diagram_loader(),
                
                # Domain services
                'conversation_service': lambda: self._container.domain.conversation_service(),
                'diagram_storage_service': lambda: self._container.domain.diagram_storage_domain_service(),
                'text_processing_service': lambda: self._container.domain.text_processing_service(),
                'db_operations_service': lambda: self._container.domain.db_operations_service(),
                'execution_flow_service': lambda: self._container.domain.flow_control_service(),
                'input_resolution_service': lambda: self._container.domain.input_resolution_service(),
            }
            
            service_factory = service_mapping.get(service_name)
            if service_factory:
                try:
                    return service_factory()
                except Exception:
                    return None
        return None
    
    def get_node_execution_count(self, node_id: str) -> int:
        """Get the execution count for a specific node.
        
        Compatible with ApplicationExecutionContext interface.
        """
        # First check the execution state for the most up-to-date count
        if hasattr(self, '_execution_state') and self._execution_state:
            node_state = self._execution_state.node_states.get(node_id)
            if node_state:
                # Use extra fields instead of metadata
                return getattr(node_state, "exec_count", 0)
        # Fall back to cached exec counts
        return self._exec_counts.get(node_id, 0)
    
    @property
    def current_node_id(self) -> str:
        """Get the ID of the currently executing node.
        
        Compatible with ApplicationExecutionContext interface.
        """
        return str(self._current_node) if self._current_node else ""
    
    @property
    def executed_nodes(self) -> List[str]:
        """Get the list of node IDs that have been executed.
        
        Compatible with ApplicationExecutionContext interface.
        """
        return self._executed_nodes
    
    @property
    def diagram_id(self) -> str:
        """Get the current diagram ID.
        
        Compatible with ApplicationExecutionContext interface.
        """
        # Need to store execution state reference
        if hasattr(self, '_execution_state'):
            return self._execution_state.diagram_id or ""
        return ""
    
    @property
    def execution_state(self) -> ExecutionState:
        """Get the underlying execution state (read-only).
        
        Compatible with ApplicationExecutionContext interface.
        """
        # Need to store execution state reference
        if hasattr(self, '_execution_state'):
            return self._execution_state
        # Build execution state from current data
        return self.to_execution_state("")
    
    @property
    def node_outputs(self) -> Dict[str, NodeOutput]:
        """Get all node outputs from the execution state."""
        if hasattr(self, '_execution_state') and self._execution_state:
            return self._execution_state.node_outputs.copy()
        return {}
    
    @property
    def container(self) -> Optional["Container"]:
        """Get the underlying container for direct access."""
        return self._container
    
    def get_service_registry(self) -> "ServiceRegistryProtocol":
        """Get a service registry from the container.
        
        This creates a UnifiedServiceRegistry that accesses services
        through the container, providing compatibility with existing code.
        """
        from dipeo.application.unified_service_registry import UnifiedServiceRegistry
        
        # Create a registry that delegates to the container
        registry = UnifiedServiceRegistry()
        
        # Register core services
        registry.register("llm_service", self._container.infra.llm_service())
        registry.register("api_key_service", self._container.domain.api_key_service())
        registry.register("file_service", self._container.infra.file_service())
        registry.register("conversation_service", self._container.domain.conversation_service())
        registry.register("notion_service", self._container.infra.notion_service())
        registry.register("api_integration_service", self._container.infra.api_service())
        
        return registry
    
    def create_node_view(self, node_id: str) -> "UnifiedExecutionContext":
        """Create a view of the context for a specific node.
        
        This creates a new context instance that shares the same state
        but has a different current node. Compatible with ApplicationExecutionContext.
        """
        view = UnifiedExecutionContext(
            execution_state=self._execution_state,
            service_registry=self._service_registry,
            container=self._container,
            current_node_id=node_id,
            executed_nodes=self._executed_nodes,
            exec_counts=self._exec_counts,
        )
        
        # Share state references
        view._node_states = self._node_states
        view._node_results = self._node_results
        view._global_context = self._global_context
        
        return view
    
    def to_execution_state(self, diagram_id: str) -> ExecutionState:
        """Convert this context to an ExecutionState for persistence.
        
        Args:
            diagram_id: The ID of the diagram being executed
            
        Returns:
            An ExecutionState instance with current context data
        """
        from dipeo.models import ExecutionID, ExecutionStatus, TokenUsage
        from datetime import datetime
        
        # Convert results back to NodeOutput format
        node_outputs = {}
        for node_id, result in self._node_results.items():
            output = NodeOutput(
                value=result.get("value"),
                metadata=result.get("metadata"),
                node_id=node_id
            )
            node_outputs[str(node_id)] = output
        
        # Calculate aggregate token usage
        total_input = 0
        total_output = 0
        for state in self._node_states.values():
            if state.token_usage:
                total_input += state.token_usage.input
                total_output += state.token_usage.output
        
        # Determine overall status
        has_failed = any(s.status == NodeExecutionStatus.FAILED for s in self._node_states.values())
        has_running = any(s.status == NodeExecutionStatus.RUNNING for s in self._node_states.values())
        
        if has_failed:
            status = ExecutionStatus.FAILED
        elif has_running:
            status = ExecutionStatus.RUNNING
        else:
            status = ExecutionStatus.COMPLETED
        
        return ExecutionState(
            id=ExecutionID(self._execution_id),
            status=status,
            diagram_id=diagram_id,
            started_at=datetime.now().isoformat(),
            node_states={str(k): v for k, v in self._node_states.items()},
            node_outputs=node_outputs,
            token_usage=TokenUsage(input=total_input, output=total_output),
            variables=self._global_context,
            is_active=has_running
        )