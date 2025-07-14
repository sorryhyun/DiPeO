from typing import TYPE_CHECKING, Any

from pydantic import BaseModel

from dipeo.application.execution import UnifiedExecutionContext
from dipeo.application.execution.handler_factory import register_handler
from dipeo.application.execution.types import TypedNodeHandler
from dipeo.core.static.generated_nodes import StartNode
from dipeo.models import HookTriggerMode, NodeOutput, NodeType, StartNodeData

if TYPE_CHECKING:
    from dipeo.application.execution.simple_execution import SimpleExecution


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

    async def pre_execute(
        self,
        node: StartNode,
        execution: "SimpleExecution"
    ) -> dict[str, Any]:
        """Pre-execute logic for StartNode."""
        return {
            "custom_data": node.custom_data,
            "output_data_structure": node.output_data_structure,
            "trigger_mode": node.trigger_mode,
            "hook_event": node.hook_event,
            "hook_filters": node.hook_filters
        }
    
    async def execute(
        self,
        node: StartNode,
        context: UnifiedExecutionContext,
        inputs: dict[str, Any],
        services: dict[str, Any],
    ) -> NodeOutput:
        # Direct typed access to node properties
        trigger_mode = node.trigger_mode or HookTriggerMode.manual
        
        if trigger_mode == HookTriggerMode.manual:
            output_data = node.custom_data or {}
            return self._build_output(
                {"default": output_data}, 
                context,
                {"message": "Manual execution started"}
            )
        
        elif trigger_mode == HookTriggerMode.hook:
            hook_data = await self._get_hook_event_data(node, context, services)
            
            if hook_data:
                output_data = {**node.custom_data, **hook_data}
                return self._build_output(
                    {"default": output_data},
                    context,
                    {"message": f"Triggered by hook event: {node.hook_event}"}
                )
            else:
                output_data = node.custom_data or {}
                return self._build_output(
                    {"default": output_data},
                    context,
                    {"message": "Hook trigger mode but no event data available"}
                )
    
    async def _get_hook_event_data(
        self,
        node: StartNode,
        context: UnifiedExecutionContext,
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