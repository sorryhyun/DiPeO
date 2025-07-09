"""User response node handler - handles interactive user input."""

from typing import Any

from dipeo.application import BaseNodeHandler, register_handler
from dipeo.core.ports.execution_context import ExecutionContextPort
from dipeo.application.utils import create_node_output
from dipeo.models import NodeOutput, UserResponseNodeData
from pydantic import BaseModel


@register_handler
class UserResponseNodeHandler(BaseNodeHandler):
    """Handler for user_response nodes."""
    
    def __init__(self):
        """Initialize handler."""
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
        props: UserResponseNodeData,
        context: ExecutionContextPort,
        inputs: dict[str, Any],
        services: dict[str, Any],
    ) -> NodeOutput:
        """Execute user_response node."""
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
