# Core execution types for DiPeO

from dataclasses import dataclass, field
from typing import Any, Dict, Optional, Generic, TypeVar, TYPE_CHECKING
from dipeo.core.static.executable_diagram import ExecutableNode
from dipeo.core.static.node_handler import TypedNodeHandler as CoreTypedHandler
from dipeo.models import NodeOutput

if TYPE_CHECKING:
    from dipeo.application.execution.stateful_execution_typed import TypedStatefulExecution


ExecutionContext = Any


@dataclass
class ExecutionOptions:

    debug: bool = False
    timeout: Optional[float] = None
    max_iterations: Optional[int] = None
    monitor: bool = False
    interactive: bool = False
    variables: Dict[str, Any] = field(default_factory=dict)


# Type variable for node types
T = TypeVar('T', bound=ExecutableNode)


class TypedNodeHandlerBase(CoreTypedHandler[T]):
    """Application-specific extensions for type-safe node handlers.
    
    This class extends the core handler base with application-specific
    functionality like service registry access, execution state management,
    and output building helpers.
    """
    
    def _get_execution(self, context: Any) -> "TypedStatefulExecution":
        """Get typed execution from context."""
        # The context should have access to the typed execution
        # This is a helper method to ensure type safety
        from dipeo.application.execution.stateful_execution_typed import TypedStatefulExecution
        
        # The execution state in context is managed by TypedStatefulExecution
        # Try to get from execution_state first
        execution_state = getattr(context, 'execution_state', None)
        if execution_state:
            stateful_execution = getattr(execution_state, '_stateful_execution', None)
            if isinstance(stateful_execution, TypedStatefulExecution):
                return stateful_execution
        
        # Fall back to service registry
        service_registry = getattr(context, 'service_registry', None)
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
        context: Any,
        metadata: Optional[Dict[str, Any]] = None
    ) -> NodeOutput:
        """Build a standard node output."""
        return NodeOutput(
            value=value,
            metadata=metadata or {},
            node_id=getattr(context, 'current_node_id', None),
            executed_nodes=getattr(context, 'executed_nodes', [])
        )


# Backward compatibility alias
TypedNodeHandler = TypedNodeHandlerBase

