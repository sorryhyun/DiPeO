
from typing import TYPE_CHECKING, Any, Optional, TypeVar

from dipeo.core.compilation.executable_diagram import ExecutableNode
from dipeo.core.execution.node_handler import TypedNodeHandler as CoreTypedHandler
from dipeo.core.execution.node_output import NodeOutputProtocol, BaseNodeOutput
from dipeo.application.registry import EXECUTION_RUNTIME

if TYPE_CHECKING:
    from dipeo.application.execution.execution_request import ExecutionRequest
    from dipeo.application.execution.execution_runtime import ExecutionRuntime


T = TypeVar('T', bound=ExecutableNode)


class TypedNodeHandlerBase(CoreTypedHandler[T]):
    
    def _get_execution(self, context: Any) -> "ExecutionRuntime":
        if hasattr(context, 'runtime') and context.runtime:
            return context.runtime
        
        execution_state = getattr(context, 'execution_state', None)
        if execution_state:
            runtime = getattr(execution_state, '_runtime', None)
            if runtime:
                return runtime
        
        service_registry = getattr(context, 'service_registry', None)
        if service_registry:
            runtime = service_registry.resolve(EXECUTION_RUNTIME)
            if runtime:
                return runtime
        
        raise ValueError("ExecutionRuntime not found in context")
    
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
        
        request = ExecutionRequest(
            node=node,
            context=context,
            inputs=inputs,
            services=services,
            metadata={},
            execution_id=getattr(context, 'execution_id', ''),
            runtime=getattr(context, 'runtime', None),
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
TypedNodeHandler = TypedNodeHandlerBase

