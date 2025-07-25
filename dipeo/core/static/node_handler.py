"""Base implementation for typed node handlers in the execution system."""

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any, Generic, TypeVar

from pydantic import BaseModel

if TYPE_CHECKING:
    from dipeo.core.static.executable_diagram import ExecutableNode
    from dipeo.core.execution.node_output import NodeOutputProtocol

# Type variable for node types
T = TypeVar('T', bound='ExecutableNode')


class TypedNodeHandler(ABC, Generic[T]):
    """Base implementation for type-safe node handlers.
    
    Each node type implements this abstract class to define how it should be executed
    within a diagram. This provides the common execution pattern where typed nodes are
    extracted from services and passed to execute_typed.
    """
    
    @property
    @abstractmethod
    def node_class(self) -> type[T]:
        """The typed node class this handler handles."""
        ...
    
    @property
    @abstractmethod
    def node_type(self) -> str:
        """The node type string identifier."""
        ...
    
    @property
    @abstractmethod
    def schema(self) -> type[BaseModel]:
        """The Pydantic schema for validation."""
        ...
    
    @property
    def requires_services(self) -> list[str]:
        """List of services required by this handler."""
        return []
    
    @property
    def description(self) -> str:
        """Description of this handler."""
        return f"Typed handler for {self.node_type} nodes"
    
    @abstractmethod
    async def execute(
        self,
        node: T,
        context: Any,
        inputs: dict[str, Any],
        services: dict[str, Any]
    ) -> 'NodeOutputProtocol':
        """Execute the handler with strongly-typed node.
        
        Args:
            node: The typed node instance
            context: Execution context (application-specific)
            inputs: Input data from connected nodes
            services: Available services for execution
            
        Returns:
            NodeOutputProtocol containing the execution results
        """
        ...