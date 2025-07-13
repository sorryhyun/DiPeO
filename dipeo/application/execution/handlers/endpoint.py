
from typing import Any

from dipeo.application import register_handler
from dipeo.application.execution.typed_handler_base import TypedNodeHandler
from dipeo.application.execution.context.unified_execution_context import UnifiedExecutionContext
from dipeo.models import EndpointNodeData, NodeOutput, NodeType
from dipeo.core.static.generated_nodes import EndpointNode
from pydantic import BaseModel


@register_handler
class EndpointNodeHandler(TypedNodeHandler[EndpointNode]):
    
    def __init__(self, file_service=None):
        self.file_service = file_service


    @property
    def node_class(self) -> type[EndpointNode]:
        return EndpointNode
    
    @property
    def node_type(self) -> str:
        return NodeType.endpoint.value

    @property
    def schema(self) -> type[BaseModel]:
        return EndpointNodeData


    @property
    def requires_services(self) -> list[str]:
        return ["file"]

    @property
    def description(self) -> str:
        return "Endpoint node – pass through data and optionally save to file"

    async def execute_typed(
        self,
        node: EndpointNode,
        context: UnifiedExecutionContext,
        inputs: dict[str, Any],
        services: dict[str, Any],
    ) -> NodeOutput:
        # Get service from context or fallback to services dict
        file_service = self.file_service or services.get("file")
        if not file_service:
            file_service = context.get_service("file")

        # Endpoint nodes pass through their inputs
        result_data = inputs if inputs else {}
        
        # Direct typed access to node properties
        save_to_file = node.save_to_file
        file_name = node.file_name

        if save_to_file and file_name:
            try:
                if isinstance(result_data, dict) and "default" in result_data:
                    content = str(result_data["default"])
                else:
                    content = str(result_data)

                await file_service.write(file_name, None, None, content)

                return self._build_output(
                    {"default": result_data},
                    context,
                    {"saved_to": file_name}
                )
            except Exception as exc:
                return self._build_output(
                    {"default": result_data},
                    context,
                    {"save_error": str(exc)}
                )

        return self._build_output(
            {"default": result_data},
            context
        )