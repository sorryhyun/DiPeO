
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Optional, TypeVar, Generic

from pydantic import BaseModel
from dipeo.domain.diagram.models.executable_diagram import ExecutableNode
from dipeo.core.execution.node_output import NodeOutputProtocol

if TYPE_CHECKING:
    from dipeo.application.execution.execution_request import ExecutionRequest


T = TypeVar('T', bound=ExecutableNode)


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
    
    # Note: This method has a default implementation below that creates an ExecutionRequest.
    # Subclasses can override either execute() or execute_request() as needed.
    
    def validate(self, request: "ExecutionRequest[T]") -> Optional[str]:
        return None
    
    @abstractmethod
    async def execute_request(self, request: "ExecutionRequest[T]") -> NodeOutputProtocol:
        """Execute the node with the unified request object.
        
        This is the main method that handlers must implement.
        """
        ...
    
    def post_execute(
        self,
        request: "ExecutionRequest[T]",
        output: NodeOutputProtocol
    ) -> NodeOutputProtocol:
        return output
    
    async def on_error(
        self,
        request: "ExecutionRequest[T]",
        error: Exception
    ) -> Optional[NodeOutputProtocol]:
        return None
    


# Backward compatibility alias
TypedNodeHandlerBase = TypedNodeHandler
