
from typing import TYPE_CHECKING, Any

from pydantic import BaseModel

from dipeo.application.execution.handler_factory import register_handler
from dipeo.application.execution.handler_base import TypedNodeHandler
from dipeo.application.unified_service_registry import EXECUTION_CONTEXT
from dipeo.diagram_generated.generated_nodes import UserResponseNode, NodeType
from dipeo.core.execution.node_output import TextOutput, NodeOutputProtocol
from dipeo.diagram_generated.models.user_response_model import UserResponseNodeData

if TYPE_CHECKING:
    from dipeo.application.execution.execution_runtime import ExecutionRuntime
    from dipeo.core.dynamic.execution_context import ExecutionContext


@register_handler
class UserResponseNodeHandler(TypedNodeHandler[UserResponseNode]):
    
    def __init__(self):
        pass


    @property
    def node_class(self) -> type[UserResponseNode]:
        return UserResponseNode
    
    @property
    def node_type(self) -> str:
        return NodeType.USER_RESPONSE.value

    @property
    def schema(self) -> type[BaseModel]:
        return UserResponseNodeData
    

    @property
    def description(self) -> str:
        return "Interactive node that prompts for user input"

    async def execute(
        self,
        node: UserResponseNode,
        context: "ExecutionContext",
        inputs: dict[str, Any],
        services: dict[str, Any],
    ) -> NodeOutputProtocol:
        return await self._execute_user_response(node, context, inputs, services)
    
    async def _execute_user_response(
        self,
        node: UserResponseNode,
        context: "ExecutionContext",
        inputs: dict[str, Any],
        services: dict[str, Any],
    ) -> NodeOutputProtocol:
        # Check if we have an interactive handler
        exec_context = services.get(EXECUTION_CONTEXT.name)
        if (
            exec_context
            and hasattr(exec_context, "interactive_handler")
            and exec_context.interactive_handler
        ):
            # Prepare the message with inputs if available
            message = node.prompt
            if inputs:
                input_str = str(inputs.get("default", inputs))
                message = f"{message}\n\nContext: {input_str}"

            # Call the interactive handler
            response = await exec_context.interactive_handler(
                {
                    "type": "user_input_required",
                    "node_id": getattr(context, 'current_node_id', 'unknown'),
                    "prompt": message,
                    "timeout": node.timeout,
                }
            )

            return TextOutput(
                value=response,
                node_id=node.id,
                metadata={"user_response": response}
            )
        # If no interactive handler, return empty response
        return TextOutput(
            value="",
            node_id=node.id,
            metadata={"warning": "No interactive handler available", "user_response": ""}
        )
