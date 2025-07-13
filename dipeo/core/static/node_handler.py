"""Protocol for typed node handlers in the execution system."""

from typing import Protocol, Type, TypeVar, List, Dict, Any, TYPE_CHECKING, runtime_checkable
from abc import abstractmethod

if TYPE_CHECKING:
    from dipeo.core.static.executable_diagram import ExecutableNode
    from dipeo.models import BaseModel, NodeOutput

# Type variable for node types
T = TypeVar('T', bound='ExecutableNode')


@runtime_checkable
class TypedNodeHandler(Protocol[T]):
    """Protocol for type-safe node handlers using generics.
    
    Each node type implements this protocol to define how it should be executed
    within a diagram. The handler is parameterized by the specific node type
    to ensure type safety.
    """
    
    @property
    @abstractmethod
    def node_class(self) -> Type[T]:
        """The typed node class this handler handles."""
        ...
    
    @property
    @abstractmethod
    def node_type(self) -> str:
        """The node type string identifier."""
        ...
    
    @property
    @abstractmethod
    def schema(self) -> Type['BaseModel']:
        """The Pydantic schema for validation."""
        ...
    
    @property
    def requires_services(self) -> List[str]:
        """List of services required by this handler."""
        return []
    
    @property
    def description(self) -> str:
        """Description of this handler."""
        return f"Typed handler for {self.node_type} nodes"
    
    @abstractmethod
    async def execute_typed(
        self,
        node: T,
        context: Any,
        inputs: Dict[str, Any],
        services: Dict[str, Any]
    ) -> 'NodeOutput':
        """Execute with strongly-typed node.
        
        Args:
            node: The typed node instance
            context: Execution context (application-specific)
            inputs: Input data from connected nodes
            services: Available services for execution
            
        Returns:
            NodeOutput containing the execution results
        """
        ...