
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any, Optional, TypeVar, Generic

from pydantic import BaseModel
from dipeo.domain.diagram.models.executable_diagram import ExecutableNode
from dipeo.core.execution.node_output import NodeOutputProtocol, BaseNodeOutput

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
    
    @abstractmethod
    async def execute(
        self,
        node: T,
        context: Any,
        inputs: dict[str, Any],
        services: dict[str, Any]
    ) -> NodeOutputProtocol:
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
    
    def validate(self, request: "ExecutionRequest[T]") -> Optional[str]:
        return None
    
    async def execute_request(self, request: "ExecutionRequest[T]") -> NodeOutputProtocol:
        """Execute the node with the unified request object.
        
        If not overridden, delegates to the execute method for backward compatibility.
        """
        return await self.execute(
            request.node,
            request.context,
            request.inputs,
            request.services
        )
    
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
    
    def _build_output(
        self,
        value: Any,
        context: Any,
        metadata: dict[str, Any] | None = None
    ) -> NodeOutputProtocol:
        from dipeo.models import NodeID
        node_id = getattr(context, 'current_node_id', None)
        return BaseNodeOutput(
            value=value,
            metadata=metadata or {},
            node_id=NodeID(node_id) if node_id else NodeID("unknown")
        )
    
    async def execute(
        self,
        node: T,
        context: Any,
        inputs: dict[str, Any],
        services: dict[str, Any]
    ) -> NodeOutputProtocol:
        from dipeo.application.execution.execution_request import ExecutionRequest
        
        # Extract metadata from context if available
        context_metadata = {}
        if hasattr(context, 'metadata') and context.metadata:
            context_metadata = context.metadata
        
        request = ExecutionRequest(
            node=node,
            context=context,
            inputs=inputs,
            services=services,
            metadata=context_metadata,
            execution_id=getattr(context, 'execution_id', ''),
            parent_container=getattr(context, '_container', None),
            parent_registry=getattr(context, '_service_registry', None)
        )
        
        try:
            validation_error = self.validate(request)
            if validation_error:
                raise ValueError(validation_error)
            
            output = await self.execute_request(request)
            
            output = self.post_execute(request, output)
            
            return output
            
        except Exception as e:
            recovery_output = await self.on_error(request, e)
            if recovery_output:
                return recovery_output
            
            raise


# Backward compatibility alias
TypedNodeHandlerBase = TypedNodeHandler
