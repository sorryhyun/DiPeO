"""
Application implementation of ExecutionContextPort.

This provides a lightweight execution context that wraps ExecutionState
and provides direct access to the infrastructure container.
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
        container: "Container",
        current_node_id: str = "",
        executed_nodes: list[str] | None = None,
        exec_counts: dict[str, int] | None = None,
    ):
        """Initialize with execution state and container.
        
        Args:
            execution_state: The immutable execution state
            container: The DI container with all services
            current_node_id: ID of the currently executing node
            executed_nodes: List of node IDs that have been executed
            exec_counts: Dictionary of node execution counts
        """
        self._state = execution_state
        self._container = container
        self._current_node_id = current_node_id
        self._executed_nodes = executed_nodes or []
        self._exec_counts = exec_counts or {}
        
        # Initialize service attributes for UnifiedServiceRegistry.from_context() compatibility
        self._initialize_service_attributes()
    
    def _initialize_service_attributes(self):
        """Initialize service attributes for backward compatibility.
        
        This method creates attributes on the context object that match the expected
        service names, allowing UnifiedServiceRegistry.from_context() to work correctly.
        """
        # Core services
        self.llm_service = self._lazy_service('llm_service')
        self.api_key_service = self._lazy_service('api_key_service')
        self.file_service = self._lazy_service('file_service')
        self.memory_service = self._lazy_service('memory_service')
        self.conversation_service = self._lazy_service('conversation_service')
        self.notion_service = self._lazy_service('notion_service')
        
        # Infrastructure services
        self.diagram_loader = self._lazy_service('diagram_loader')
        self.api_integration_service = self._lazy_service('api_integration_service')
        
        # Domain services
        self.diagram_storage_service = self._lazy_service('diagram_storage_service')
        self.text_processing_service = self._lazy_service('text_processing_service')
        self.db_operations_service = self._lazy_service('db_operations_service')
        
        # Execution domain services
        self.execution_flow_service = self._lazy_service('execution_flow_service')
        self.input_resolution_service = self._lazy_service('input_resolution_service')
    
    def _lazy_service(self, service_name: str):
        """Create a lazy service accessor.
        
        Returns the actual service when accessed, or None if not available.
        """
        return self.get_service(service_name)
    
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
        """Get a service by name from the container.
        
        This method provides backward compatibility for code that expects
        to access services by name. It directly accesses the container's
        infrastructure and domain services.
        """
        # Map service names to container paths
        service_mapping = {
            # Infrastructure services
            'llm_service': lambda: self._container.infra.llm_service(),
            'api_key_service': lambda: self._container.domain.api_key_service(),
            'file_service': lambda: self._container.infra.file_service(),
            'memory_service': lambda: self._container.infra.memory_service(),
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
                # Service might not be available
                return None
        return None
    
    @property
    def container(self) -> "Container":
        """Get the underlying container for direct access."""
        return self._container
    
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
            container=self._container,
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
        
        This is now a simple factory that directly uses the container.
        The method is kept for backward compatibility.
        
        Args:
            execution_state: The execution state
            container: The DI container with all services
            current_node_id: Current node ID
            executed_nodes: List of executed node IDs
            exec_counts: Node execution counts
            
        Returns:
            ApplicationExecutionContext with container access
        """
        return cls(
            execution_state=execution_state,
            container=container,
            current_node_id=current_node_id,
            executed_nodes=executed_nodes,
            exec_counts=exec_counts,
        )