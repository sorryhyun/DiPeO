
from typing import Any, Optional

from dipeo.application import BaseNodeHandler, register_handler
from dipeo.core.application.context.execution_context import ExecutionContextPort
from dipeo.application.utils import create_node_output
from dipeo.models import NodeOutput, StartNodeData, HookTriggerMode
from pydantic import BaseModel


@register_handler
class StartNodeHandler(BaseNodeHandler):
    
    def __init__(self):
        pass


    @property
    def node_type(self) -> str:
        return "start"

    @property
    def schema(self) -> type[BaseModel]:
        return StartNodeData

    @property
    def description(self) -> str:
        return "Kick-off node: can start manually or via hook trigger"

    async def execute(
        self,
        props: StartNodeData,
        context: ExecutionContextPort,
        inputs: dict[str, Any],
        services: dict[str, Any],
    ) -> NodeOutput:
        # Check trigger mode
        trigger_mode = props.trigger_mode or HookTriggerMode.manual
        
        if trigger_mode == HookTriggerMode.manual:
            # Traditional manual start
            output_data = props.custom_data or {}
            return create_node_output(
                {"default": output_data}, 
                {"message": "Manual execution started"},
                node_id=context.current_node_id,
                executed_nodes=context.executed_nodes
            )
        
        elif trigger_mode == HookTriggerMode.hook:
            # Hook-triggered start
            # In a full implementation, this would wait for matching events
            # For now, we'll check if hook event data was passed in context
            hook_data = await self._get_hook_event_data(props, context, services)
            
            if hook_data:
                # Merge hook data with custom data
                output_data = {**props.custom_data, **hook_data}
                return create_node_output(
                    {"default": output_data},
                    {"message": f"Triggered by hook event: {props.hook_event}"},
                    node_id=context.current_node_id,
                    executed_nodes=context.executed_nodes
                )
            else:
                # No hook data available, start with custom data only
                output_data = props.custom_data or {}
                return create_node_output(
                    {"default": output_data},
                    {"message": "Hook trigger mode but no event data available"},
                    node_id=context.current_node_id,
                    executed_nodes=context.executed_nodes
                )
    
    async def _get_hook_event_data(
        self, 
        props: StartNodeData, 
        context: ExecutionContextPort,
        services: dict[str, Any]
    ) -> Optional[dict[str, Any]]:
        # Check if hook event data was provided in the execution state
        event_data = context.get_variable('hook_event_data')
        if event_data:
            
            # Validate event matches filters if specified
            if props.hook_filters:
                for key, expected_value in props.hook_filters.items():
                    if key not in event_data or event_data[key] != expected_value:
                        return None
            
            return event_data
        
        # In a real implementation, we would wait for events here
        # For now, return None to indicate no event data
        return None