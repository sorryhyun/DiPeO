from typing import TYPE_CHECKING, Any, Optional

from pydantic import BaseModel

from dipeo.application.execution.handler_base import TypedNodeHandler
from dipeo.application.execution.execution_request import ExecutionRequest
from dipeo.application.execution.handler_factory import register_handler
from dipeo.core.static.generated_nodes import StartNode
from dipeo.core.execution.node_output import DataOutput, NodeOutputProtocol
from dipeo.models import HookTriggerMode, NodeType, StartNodeData

if TYPE_CHECKING:
    from dipeo.application.execution.execution_runtime import ExecutionRuntime
    from dipeo.core.dynamic.execution_context import ExecutionContext


@register_handler
class StartNodeHandler(TypedNodeHandler[StartNode]):
    
    def __init__(self):
        pass

    @property
    def node_class(self) -> type[StartNode]:
        return StartNode
    
    @property
    def node_type(self) -> str:
        return NodeType.start.value

    @property
    def schema(self) -> type[BaseModel]:
        return StartNodeData

    @property
    def description(self) -> str:
        return "Kick-off node: can start manually or via hook trigger"

    def validate(self, request: ExecutionRequest[StartNode]) -> Optional[str]:
        """Validate the start node configuration."""
        node = request.node
        
        # Validate hook configuration
        if node.trigger_mode == HookTriggerMode.hook:
            if not node.hook_event:
                return "Hook event must be specified when using hook trigger mode"
        
        return None
    
    async def execute_request(self, request: ExecutionRequest[StartNode]) -> NodeOutputProtocol:
        """Execute the start node."""
        node = request.node
        context = request.context
        # Store node configuration in metadata for debugging
        request.add_metadata("trigger_mode", node.trigger_mode)
        request.add_metadata("hook_event", node.hook_event)
        request.add_metadata("hook_filters", node.hook_filters)
        
        # Direct typed access to node properties
        trigger_mode = node.trigger_mode or HookTriggerMode.manual
        
        if trigger_mode == HookTriggerMode.manual:
            output_data = node.custom_data or {}
            return DataOutput(
                value={"default": output_data},
                node_id=node.id,
                metadata={"message": "Manual execution started"}
            )
        
        elif trigger_mode == HookTriggerMode.hook:
            hook_data = await self._get_hook_event_data(node, context, request.services)
            
            if hook_data:
                output_data = {**node.custom_data, **hook_data}
                return DataOutput(
                    value={"default": output_data},
                    node_id=node.id,
                    metadata={"message": f"Triggered by hook event: {node.hook_event}"}
                )
            else:
                output_data = node.custom_data or {}
                return DataOutput(
                    value={"default": output_data},
                    node_id=node.id,
                    metadata={"message": "Hook trigger mode but no event data available"}
                )
    
    async def _get_hook_event_data(
        self,
        node: StartNode,
        context: "ExecutionContext",
        services: dict[str, Any]
    ) -> dict[str, Any] | None:
        # Check if hook event data was provided in the execution state
        event_data = context.get_variable('hook_event_data')
        if event_data:
            
            # Validate event matches filters if specified
            if node.hook_filters:
                for key, expected_value in node.hook_filters.items():
                    if key not in event_data or event_data[key] != expected_value:
                        return None
            
            return event_data
        
        # In a real implementation, we would wait for events here
        # For now, return None to indicate no event data
        return None
    
    def post_execute(
        self,
        request: ExecutionRequest[StartNode],
        output: NodeOutputProtocol
    ) -> NodeOutputProtocol:
        """Post-execution hook to log start node execution."""
        # Log execution details if in debug mode
        if request.metadata.get("debug"):
            print(f"[StartNode] Executed with trigger mode: {request.metadata.get('trigger_mode')}")
        
        return output