"""User response node handler - handles interactive user input."""

from typing import Any

from dipeo_core import BaseNodeHandler, RuntimeContext, register_handler
from dipeo_core.execution import create_node_output
from dipeo_domain.models import NodeOutput, UserResponseNodeData
from pydantic import BaseModel


@register_handler
class UserResponseNodeHandler(BaseNodeHandler):
    """Handler for user_response nodes."""

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
        context: RuntimeContext,
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
                    "node_id": context.current_node_id,
                    "prompt": message,
                    "timeout": props.timeout,
                }
            )

            return create_node_output({"default": response, "user_response": response})
        # If no interactive handler, return empty response
        return create_node_output(
            {"default": "", "user_response": ""},
            {"warning": "No interactive handler available"},
        )
