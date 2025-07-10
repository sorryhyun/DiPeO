"""Protocol for node handlers in the execution system."""

from typing import Protocol, Dict, Any, Optional, TYPE_CHECKING, List
from abc import abstractmethod

if TYPE_CHECKING:
    from dipeo.models import NodeState


class NodeHandler(Protocol):
    """Base protocol for all node handlers.
    
    Each node type (Person, Job, Condition, etc.) implements this protocol
    to define how it should be executed within a diagram.
    """
    
    @abstractmethod
    async def execute(
        self,
        node_config: Dict[str, Any],
        inputs: Dict[str, Any],
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute the node with given inputs and context.
        
        Args:
            node_config: The node's configuration from the diagram
            inputs: Input data from connected nodes
            context: Execution context (services, state, etc.)
            
        Returns:
            Dictionary containing the node's outputs
            
        Raises:
            NodeExecutionError: If execution fails
        """
        ...
    
    @abstractmethod
    def validate_config(self, node_config: Dict[str, Any]) -> List[str]:
        """Validate the node's configuration.
        
        Args:
            node_config: The node configuration to validate
            
        Returns:
            List of validation errors (empty if valid)
        """
        ...
    
    def get_required_inputs(self) -> List[str]:
        """Get the list of required input names for this handler.
        
        Returns:
            List of required input names
        """
        return []
    
    def get_output_schema(self) -> Dict[str, Any]:
        """Get the schema of outputs this handler produces.
        
        Returns:
            Dictionary describing the output schema
        """
        return {}


class StatefulNodeHandler(NodeHandler):
    """Protocol for node handlers that maintain state across executions."""
    
    @abstractmethod
    async def initialize(self, context: Dict[str, Any]) -> None:
        """Initialize the handler before first execution.
        
        Args:
            context: Initialization context
        """
        ...
    
    @abstractmethod
    async def cleanup(self) -> None:
        """Cleanup resources after execution completes."""
        ...
    
    @abstractmethod
    def get_state(self) -> "NodeState":
        """Get the current state of the node.
        
        Returns:
            Current node state
        """
        ...


class NodeRegistry(Protocol):
    """Registry for managing node type handlers."""
    
    def register_handler(self, node_type: str, handler: NodeHandler) -> None:
        """Register a handler for a specific node type.
        
        Args:
            node_type: The type of node this handler processes
            handler: The handler instance
        """
        ...
    
    def get_handler(self, node_type: str) -> Optional[NodeHandler]:
        """Get the handler for a specific node type.
        
        Args:
            node_type: The type of node
            
        Returns:
            The handler if registered, None otherwise
        """
        ...
    
    def list_supported_types(self) -> List[str]:
        """Get list of all supported node types.
        
        Returns:
            List of node type names
        """
        ...