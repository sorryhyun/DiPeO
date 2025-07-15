"""Modern node executor using improved output and state tracking."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from dipeo.core.execution.execution_tracker import CompletionStatus, ExecutionTracker, FlowStatus
from dipeo.core.execution.node_output import ErrorOutput, NodeOutputProtocol

if TYPE_CHECKING:
    from dipeo.core.dynamic.execution_context import ExecutionContext
    from dipeo.core.static.executable_diagram import ExecutableNode
    from dipeo.core.static.generated_nodes import PersonJobNode
    from dipeo.models import NodeID


class ModernNodeExecutor:
    """Node executor using improved output and state tracking."""
    
    def __init__(self, tracker: ExecutionTracker):
        self.tracker = tracker
    
    async def execute_node(
        self,
        node: ExecutableNode,
        context: ExecutionContext,
        inputs: dict[str, Any],
        handler: Any
    ) -> NodeOutputProtocol:
        """Execute node with proper state and output management."""
        
        # Start execution tracking
        execution_number = self.tracker.start_execution(node.id)
        
        try:
            # Inject execution metadata into context
            context.metadata = context.metadata or {}
            context.metadata.update({
                "execution_number": execution_number,
                "previous_executions": self.tracker.get_execution_count(node.id) - 1,
                "execution_tracker": self.tracker
            })
            
            # Execute handler with proper output typing
            output = await handler.execute(
                node=node,
                context=context,
                inputs=inputs,
                services=context.service_registry
            )
            
            # Validate output type
            if not isinstance(output, NodeOutputProtocol):
                # Handle legacy outputs
                from dipeo.core.execution.node_output import LegacyNodeOutput
                from dipeo.models import NodeOutput as LegacyModel
                
                if isinstance(output, LegacyModel):
                    # Convert from legacy model
                    legacy = LegacyNodeOutput(
                        value=output.value,
                        metadata=output.metadata or {}
                    )
                    output = legacy.to_modern(node.id)
                else:
                    raise TypeError(f"Handler returned {type(output)}, expected NodeOutputProtocol")
            
            # Extract token usage if available
            token_usage = None
            if hasattr(output, 'metadata') and 'token_usage' in output.metadata:
                token_usage = output.metadata['token_usage']
            
            # Complete execution successfully
            self.tracker.complete_execution(
                node.id,
                CompletionStatus.SUCCESS,
                output,
                token_usage=token_usage
            )
            
            return output
            
        except Exception as error:
            # Complete execution with failure
            error_output = ErrorOutput(
                value=str(error),
                node_id=node.id,
                error_type=type(error).__name__
            )
            
            self.tracker.complete_execution(
                node.id,
                CompletionStatus.FAILED,
                error_output,
                str(error)
            )
            
            raise
    
    def should_execute_node(self, node: ExecutableNode) -> bool:
        """Check if node should execute based on runtime state and history."""
        runtime_state = self.tracker.get_runtime_state(node.id)
        
        # Check basic execution readiness
        if not runtime_state.can_execute():
            return False
        
        # Check max iterations for PersonJobNodes
        from dipeo.core.static.generated_nodes import PersonJobNode
        if isinstance(node, PersonJobNode):
            execution_count = self.tracker.get_execution_count(node.id)
            max_iter = getattr(node, 'max_iteration', 1) or 1
            
            if execution_count >= max_iter:
                # Mark as blocked to prevent further attempts
                self.tracker.update_runtime_state(node.id, FlowStatus.BLOCKED)
                return False
        
        return True
    
    def reset_node_for_iteration(self, node_id: NodeID) -> None:
        """Reset node for next iteration while preserving execution history."""
        # This preserves outputs for condition checking while allowing re-execution
        self.tracker.reset_for_iteration(node_id)
    
    def mark_node_ready(self, node_id: NodeID) -> None:
        """Mark a node as ready to execute."""
        runtime_state = self.tracker.get_runtime_state(node_id)
        runtime_state.flow_status = FlowStatus.READY
        runtime_state.dependencies_met = True
    
    def mark_node_blocked(self, node_id: NodeID) -> None:
        """Mark a node as blocked."""
        self.tracker.update_runtime_state(node_id, FlowStatus.BLOCKED)
    
    def get_node_output(self, node_id: NodeID) -> NodeOutputProtocol | None:
        """Get the last output for a node."""
        return self.tracker.get_last_output(node_id)
    
    def has_node_executed(self, node_id: NodeID) -> bool:
        """Check if a node has executed at least once."""
        return self.tracker.has_executed(node_id)