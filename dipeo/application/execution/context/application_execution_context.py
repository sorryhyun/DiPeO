"""
Application implementation of ExecutionContextPort.

This provides a lightweight execution context that wraps ExecutionState
and provides access to services via a service registry.
"""

from typing import TYPE_CHECKING, Any

from dipeo.models import ExecutionState

if TYPE_CHECKING:
    from dipeo.container import Container


class ApplicationExecutionContext:
    """Concrete implementation of ExecutionContextPort."""
    
    def __init__(
        self, 
        execution_state: ExecutionState, 
        service_registry: Any,
        current_node_id: str = "",
        executed_nodes: list[str] | None = None,
        exec_counts: dict[str, int] | None = None,
    ):
        """Initialize with execution state and service registry.
        
        Args:
            execution_state: The immutable execution state
            service_registry: Registry for accessing services
            current_node_id: ID of the currently executing node
            executed_nodes: List of node IDs that have been executed
            exec_counts: Dictionary of node execution counts
        """
        self._state = execution_state
        self._service_registry = service_registry
        self._current_node_id = current_node_id
        self._executed_nodes = executed_nodes or []
        self._exec_counts = exec_counts or {}
    
    def get_node_output(self, node_id: str) -> Any | None:
        """Get the output of a specific node."""
        if not self._state.node_outputs:
            return None
        output = self._state.node_outputs.get(node_id)
        if output is None:
            return None
        # Extract value from NodeOutput if present
        if hasattr(output, 'value'):
            return output.value
        return output
    
    def get_variable(self, key: str) -> Any | None:
        """Get a variable from the execution context."""
        if not self._state.variables:
            return None
        return self._state.variables.get(key)
    
    def get_service(self, service_name: str) -> Any | None:
        """Get a service by name from the service registry."""
        return getattr(self._service_registry, service_name, None)
    
    @property
    def diagram_id(self) -> str:
        """Get the current diagram ID."""
        return self._state.diagram_id
    
    @property
    def execution_state(self) -> ExecutionState:
        """Get the underlying execution state (read-only)."""
        return self._state
    
    def get_node_execution_count(self, node_id: str) -> int:
        """Get the execution count for a specific node."""
        return self._exec_counts.get(node_id, 0)
    
    @property
    def current_node_id(self) -> str:
        """Get the ID of the currently executing node."""
        return self._current_node_id
    
    @property
    def executed_nodes(self) -> list[str]:
        """Get the list of node IDs that have been executed."""
        return self._executed_nodes
    
    def create_node_view(self, node_id: str) -> "ApplicationExecutionContext":
        """Create a lightweight view of the context for a specific node.
        
        This creates a new context with the current node ID set.
        """
        return ApplicationExecutionContext(
            execution_state=self._state,
            service_registry=self._service_registry,
            current_node_id=node_id,
            executed_nodes=self._executed_nodes,
            exec_counts=self._exec_counts,
        )
    
    @classmethod
    def create_with_services(
        cls,
        execution_state: ExecutionState,
        container: "Container",
        current_node_id: str = "",
        executed_nodes: list[str] | None = None,
        exec_counts: dict[str, int] | None = None,
    ) -> "ApplicationExecutionContext":
        """Create an ApplicationExecutionContext with services from container.
        
        This factory method creates a context object that has all required services
        as attributes, which is necessary for UnifiedServiceRegistry.from_context().
        
        Args:
            execution_state: The execution state
            container: The DI container with all services
            current_node_id: Current node ID
            executed_nodes: List of executed node IDs
            exec_counts: Node execution counts
            
        Returns:
            ApplicationExecutionContext with all services attached
        """
        # Create a service wrapper that provides services as attributes
        class ServiceWrapper:
            def __init__(self, container):
                # Core services
                self.llm_service = container.infra.llm_service()
                self.api_key_service = container.domain.api_key_service()
                self.file_service = container.infra.file_service()
                self.memory_service = container.infra.memory_service()
                self.conversation_service = container.domain.conversation_service()
                self.notion_service = container.infra.notion_service()
                
                # Domain services
                self.diagram_storage_service = container.domain.diagram_storage_domain_service()
                self.api_integration_service = container.infra.api_service()
                self.text_processing_service = container.domain.text_processing_service()
                self.db_operations_service = container.domain.db_operations_service()
                self.code_execution_service = container.infra.code_execution_service()
                
                # Execution domain services
                self.execution_flow_service = container.domain.flow_control_service()
                self.input_resolution_service = container.domain.input_resolution_service()
                
                # Support method for service registry
                def get(self, service_name: str):
                    return getattr(self, service_name, None)
                    
                self.get = get
        
        service_wrapper = ServiceWrapper(container)
        
        return cls(
            execution_state=execution_state,
            service_registry=service_wrapper,
            current_node_id=current_node_id,
            executed_nodes=executed_nodes,
            exec_counts=exec_counts,
        )