"""Base implementation for typed node handlers in the execution system."""

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any, Generic, TypeVar

from pydantic import BaseModel

if TYPE_CHECKING:
    from dipeo.core.execution.executable_diagram import ExecutableNode
    from dipeo.core.execution.node_output import NodeOutputProtocol

# Type variable for node types
T = TypeVar('T', bound='ExecutableNode')


class TypedNodeHandler(ABC, Generic[T]):
    """Base for type-safe node handlers. Defines execution pattern for typed nodes."""
    
    @property
    @abstractmethod
    def node_class(self) -> type[T]:
        ...
    
    @property
    @abstractmethod
    def node_type(self) -> str:
        ...
    
    @property
    @abstractmethod
    def schema(self) -> type[BaseModel]:
        ...
    
    @property
    def requires_services(self) -> list[str]:
        return []
    
    @property
    def description(self) -> str:
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