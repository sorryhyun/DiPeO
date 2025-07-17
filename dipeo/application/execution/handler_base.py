# Base handler class for DiPeO node handlers

from typing import TYPE_CHECKING, Any, Optional, TypeVar

from dipeo.core.static.executable_diagram import ExecutableNode
from dipeo.core.static.node_handler import TypedNodeHandler as CoreTypedHandler
from dipeo.core.execution.node_output import NodeOutputProtocol, BaseNodeOutput

if TYPE_CHECKING:
    from dipeo.application.execution.execution_request import ExecutionRequest
    from dipeo.application.execution.execution_runtime import ExecutionRuntime


# Type variable for node types
T = TypeVar('T', bound=ExecutableNode)


class TypedNodeHandlerBase(CoreTypedHandler[T]):
    """Application-specific extensions for type-safe node handlers.
    
    This class extends the core handler base with application-specific
    functionality like service registry access, execution state management,
    output building helpers, and lifecycle methods.
    
    Lifecycle methods (all optional):
    - validate: Pre-execution validation
    - execute_request: New unified execution interface
    - post_execute: Post-processing after execution
    - on_error: Error recovery handling
    """
    
    def _get_execution(self, context: Any) -> "ExecutionRuntime":
        """Get typed execution from context."""
        # Get ExecutionRuntime from context
        if hasattr(context, 'runtime') and context.runtime:
            return context.runtime
        
        # Try to get from execution_state
        execution_state = getattr(context, 'execution_state', None)
        if execution_state:
            runtime = getattr(execution_state, '_runtime', None)
            if runtime:
                return runtime
        
        # Fall back to service registry
        service_registry = getattr(context, 'service_registry', None)
        if service_registry:
            runtime = service_registry.get('execution_runtime')
            if runtime:
                return runtime
        
        raise ValueError("ExecutionRuntime not found in context")
    
    def validate(self, request: "ExecutionRequest[T]") -> Optional[str]:
        """Validate the execution request before execution.
        
        Args:
            request: The execution request to validate
            
        Returns:
            Error message if validation fails, None if valid
        """
        # Default implementation - can be overridden
        return None
    
    async def execute_request(self, request: "ExecutionRequest[T]") -> NodeOutputProtocol:
        """Execute the node with the unified request object.
        
        This is the new execution interface that provides a cleaner API.
        If not overridden, it delegates to the execute method.
        
        Args:
            request: The unified execution request
            
        Returns:
            NodeOutputProtocol containing the execution results
        """
        # Default implementation delegates to execute for backward compatibility
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
        """Post-execution hook for cleanup or enrichment.
        
        Args:
            request: The execution request
            output: The output from execution
            
        Returns:
            Modified output (or original if no changes)
        """
        # Default implementation - can be overridden
        return output
    
    async def on_error(
        self,
        request: "ExecutionRequest[T]",
        error: Exception
    ) -> Optional[NodeOutputProtocol]:
        """Error recovery hook.
        
        Args:
            request: The execution request
            error: The exception that occurred
            
        Returns:
            Recovery output if possible, None to propagate error
        """
        # Default implementation - can be overridden
        return None
    
    def _build_output(
        self,
        value: Any,
        context: Any,
        metadata: dict[str, Any] | None = None
    ) -> NodeOutputProtocol:
        """Build a standard node output."""
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
        """Execute the handler with lifecycle support.
        
        Always creates ExecutionRequest and uses the lifecycle flow.
        """
        # Import here to avoid circular dependency
        from dipeo.application.execution.execution_request import ExecutionRequest
        
        # Always create ExecutionRequest and use lifecycle flow
        request = ExecutionRequest(
            node=node,
            context=context,
            inputs=inputs,
            services=services,
            metadata={},
            execution_id=getattr(context, 'execution_id', ''),
            runtime=getattr(context, 'runtime', None)
        )
        
        try:
            # Validate
            validation_error = self.validate(request)
            if validation_error:
                raise ValueError(validation_error)
            
            # Execute
            output = await self.execute_request(request)
            
            # Post-execute
            output = self.post_execute(request, output)
            
            return output
            
        except Exception as e:
            # Try error recovery
            recovery_output = await self.on_error(request, e)
            if recovery_output:
                return recovery_output
            
            # No recovery - re-raise
            raise


# Backward compatibility alias
TypedNodeHandler = TypedNodeHandlerBase

