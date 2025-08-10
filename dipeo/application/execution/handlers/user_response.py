
import json
from typing import TYPE_CHECKING, Any

from pydantic import BaseModel

from dipeo.application.execution.handler_factory import register_handler
from dipeo.application.execution.handler_base import TypedNodeHandler
from dipeo.application.execution.execution_request import ExecutionRequest
from dipeo.application.registry import EXECUTION_CONTEXT
from dipeo.diagram_generated.generated_nodes import UserResponseNode, NodeType
from dipeo.core.execution.node_output import TextOutput, NodeOutputProtocol
from dipeo.diagram_generated.models.user_response_model import UserResponseNodeData

if TYPE_CHECKING:
    from dipeo.core.execution.execution_context import ExecutionContext


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

    async def execute_request(self, request: ExecutionRequest[UserResponseNode]) -> NodeOutputProtocol:
        return await self._execute_user_response(request)
    
    async def _execute_user_response(self, request: ExecutionRequest[UserResponseNode]) -> NodeOutputProtocol:
        # Extract properties from request
        node = request.node
        context = request.context
        inputs = request.inputs
        
        # Get execution context from ServiceRegistry
        exec_context = request.services.resolve(EXECUTION_CONTEXT)
        if (
            exec_context
            and hasattr(exec_context, "interactive_handler")
            and exec_context.interactive_handler
        ):
            message = node.prompt
            if inputs:
                input_str = str(inputs.get("default", inputs))
                message = f"{message}\n\nContext: {input_str}"

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
                metadata=json.dumps({"user_response": response})
            )
        return TextOutput(
            value="",
            node_id=node.id,
            metadata=json.dumps({"warning": "No interactive handler available", "user_response": ""})
        )
