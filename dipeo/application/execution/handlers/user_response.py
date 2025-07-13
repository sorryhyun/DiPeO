
from typing import Any, Type

from dipeo.application import register_handler
from dipeo.application.execution.handler_factory import BaseNodeHandler
from dipeo.application.execution.context.unified_execution_context import UnifiedExecutionContext
from dipeo.application.utils import create_node_output
from dipeo.models import NodeOutput, UserResponseNodeData
from dipeo.core.static.nodes import UserResponseNode
from pydantic import BaseModel


@register_handler
class UserResponseNodeHandler(BaseNodeHandler):
    
    def __init__(self):
        pass


    @property
    def node_type(self) -> str:
        return "user_response"

    @property
    def schema(self) -> type[BaseModel]:
        return UserResponseNodeData
    

    @property
    def description(self) -> str:
        return "Interactive node that prompts for user input"

    async def execute(
        self,
        props: BaseModel,
        context: UnifiedExecutionContext,
        inputs: dict[str, Any],
        services: dict[str, Any],
    ) -> NodeOutput:
        # Extract typed node from services if available
        typed_node = services.get("typed_node")
        
        if typed_node and isinstance(typed_node, UserResponseNode):
            # Convert typed node to props
            response_props = UserResponseNodeData(
                label=typed_node.label,
                prompt=typed_node.prompt,
                timeout=typed_node.timeout
            )
        elif isinstance(props, UserResponseNodeData):
            response_props = props
        else:
            # Handle unexpected case
            return create_node_output(
                {"default": "", "user_response": ""}, 
                {"error": "Invalid node data provided"},
                node_id=context.current_node_id,
                executed_nodes=context.executed_nodes
            )
        
        return await self._execute_user_response(response_props, context, inputs, services)
    
    async def _execute_user_response(
        self,
        props: UserResponseNodeData,
        context: UnifiedExecutionContext,
        inputs: dict[str, Any],
        services: dict[str, Any],
    ) -> NodeOutput:
        # Check if we have an interactive handler
        exec_context = services.get("execution_context")
        if (
            exec_context
            and hasattr(exec_context, "interactive_handler")
            and exec_context.interactive_handler
        ):
            # Prepare the message with inputs if available
            message = props.prompt
            if inputs:
                input_str = str(inputs.get("default", inputs))
                message = f"{message}\n\nContext: {input_str}"

            # Call the interactive handler
            response = await exec_context.interactive_handler(
                {
                    "type": "user_input_required",
                    "node_id": getattr(context, 'current_node_id', 'unknown'),
                    "prompt": message,
                    "timeout": props.timeout,
                }
            )

            return create_node_output(
                {"default": response, "user_response": response},
                node_id=context.current_node_id,
                executed_nodes=context.executed_nodes
            )
        # If no interactive handler, return empty response
        return create_node_output(
            {"default": "", "user_response": ""},
            {"warning": "No interactive handler available"},
            node_id=context.current_node_id,
            executed_nodes=context.executed_nodes
        )
