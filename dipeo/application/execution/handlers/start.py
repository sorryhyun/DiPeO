from typing import Any, Dict, Optional

from dipeo.application import register_handler
from dipeo.application.execution.handler_factory import BaseNodeHandler
from dipeo.application.execution.context.unified_execution_context import UnifiedExecutionContext
from dipeo.application.utils import create_node_output
from dipeo.models import NodeOutput, StartNodeData, HookTriggerMode
from dipeo.core.static.nodes import StartNode
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
        props: Any,  # Will receive typed node directly
        context: UnifiedExecutionContext,
        inputs: Dict[str, Any],
        services: Dict[str, Any],
    ) -> NodeOutput:
        # Extract typed node from props or services
        if isinstance(props, StartNode):
            node = props
        else:
            # Fallback for compatibility during migration
            node = services.get("typed_node")
            if not isinstance(node, StartNode):
                raise ValueError("StartNodeHandler requires a StartNode instance")
        
        trigger_mode = node.trigger_mode or HookTriggerMode.manual
        
        if trigger_mode == HookTriggerMode.manual:
            output_data = node.custom_data or {}
            return create_node_output(
                {"default": output_data}, 
                {"message": "Manual execution started"},
                node_id=context.current_node_id,
                executed_nodes=context.executed_nodes
            )
        
        elif trigger_mode == HookTriggerMode.hook:
            hook_data = await self._get_hook_event_data(node, context, services)
            
            if hook_data:
                output_data = {**node.custom_data, **hook_data}
                return create_node_output(
                    {"default": output_data},
                    {"message": f"Triggered by hook event: {node.hook_event}"},
                    node_id=context.current_node_id,
                    executed_nodes=context.executed_nodes
                )
            else:
                output_data = node.custom_data or {}
                return create_node_output(
                    {"default": output_data},
                    {"message": "Hook trigger mode but no event data available"},
                    node_id=context.current_node_id,
                    executed_nodes=context.executed_nodes
                )
    
    async def _get_hook_event_data(
        self,
        node: StartNode,
        context: UnifiedExecutionContext,
        services: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
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