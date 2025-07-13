# Type-safe handler system implementation

from abc import ABC
from typing import Any, Dict, Generic, TypeVar, Type, Optional, TYPE_CHECKING

from pydantic import BaseModel

from dipeo.core.static.executable_diagram import ExecutableNode
from dipeo.core.static.node_handler import TypedNodeHandler as TypedNodeHandlerProtocol
from dipeo.models import NodeOutput

if TYPE_CHECKING:
    from dipeo.application.execution.stateful_execution_typed import TypedStatefulExecution
    from dipeo.application.execution.context.unified_execution_context import UnifiedExecutionContext

# Type variable for node types
T = TypeVar('T', bound=ExecutableNode)


class TypedNodeHandlerBase(Generic[T], TypedNodeHandlerProtocol[T], ABC):
    """Base implementation class for type-safe node handlers.
    
    This class provides the concrete implementation of the TypedNodeHandler protocol
    from core, adding application-specific functionality.
    """
    
    async def execute(
        self,
        props: BaseModel,
        context: "UnifiedExecutionContext",
        inputs: Dict[str, Any],
        services: Dict[str, Any]
    ) -> NodeOutput:
        """Execute the handler with type-safe node."""
        # Extract typed node from services
        typed_node = services.get("typed_node")
        if not typed_node or not isinstance(typed_node, self.node_class):
            raise ValueError(f"Expected {self.node_class.__name__} but got {type(typed_node)}")
        
        # Delegate to typed execution
        return await self.execute_typed(
            node=typed_node,
            context=context,
            inputs=inputs,
            services=services
        )
    
    # Note: execute_typed is abstract in the protocol, subclasses must implement it
    
    def to_node_handler(self):
        """Convert to node handler for compatibility with registry."""
        return self.execute
    
    def _get_execution(self, context: "UnifiedExecutionContext") -> "TypedStatefulExecution":
        """Get typed execution from context."""
        # The context should have access to the typed execution
        # This is a helper method to ensure type safety
        from dipeo.application.execution.stateful_execution_typed import TypedStatefulExecution
        
        # The execution state in context is managed by TypedStatefulExecution
        # We can reconstruct it or get it from the service registry
        service_registry = context.service_registry
        if service_registry:
            execution = service_registry.get('typed_execution')
            if isinstance(execution, TypedStatefulExecution):
                return execution
        
        raise ValueError("TypedStatefulExecution not found in context")
    
    async def pre_execute(
        self,
        node: T,
        execution: "TypedStatefulExecution"
    ) -> Dict[str, Any]:
        """Pre-execution logic for the node. Override in subclasses."""
        return {}
    
    def _build_output(
        self,
        value: Any,
        context: "UnifiedExecutionContext",
        metadata: Optional[Dict[str, Any]] = None
    ) -> NodeOutput:
        """Build a standard node output."""
        return NodeOutput(
            value=value,
            metadata=metadata or {},
            node_id=context.current_node_id,
            executed_nodes=context.executed_nodes
        )


# Backward compatibility alias
TypedNodeHandler = TypedNodeHandlerBase