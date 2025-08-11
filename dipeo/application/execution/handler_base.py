
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
    
    
    def validate(self, request: "ExecutionRequest[T]") -> Optional[str]:
        return None
    
    @abstractmethod
    async def execute_request(self, request: "ExecutionRequest[T]") -> NodeOutputProtocol:
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
    



TypedNodeHandlerBase = TypedNodeHandler
