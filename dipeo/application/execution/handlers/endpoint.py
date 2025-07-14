
from typing import Any, TYPE_CHECKING

from dipeo.application import register_handler
from dipeo.application.execution.types import TypedNodeHandler
from dipeo.application.execution.context.unified_execution_context import UnifiedExecutionContext
from dipeo.models import EndpointNodeData, NodeOutput, NodeType
from dipeo.core.static.generated_nodes import EndpointNode
from pydantic import BaseModel

if TYPE_CHECKING:
    from dipeo.application.execution.stateful_execution_typed import TypedStatefulExecution


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

    async def pre_execute(
        self,
        node: EndpointNode,
        execution: "TypedStatefulExecution"
    ) -> dict[str, Any]:
        """Pre-execute logic for EndpointNode."""
        save_config = None
        if node.save_to_file:
            save_config = {
                "save": True,
                "filename": node.file_name or f"output_{node.id}.json"
            }
        
        return {"save_config": save_config}
    
    async def execute(
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
        # Handle both file_name and file_path from node data
        file_name = node.file_name
        
        # Also check the original node data for file_path if file_name is not set
        if not file_name and hasattr(node, 'metadata') and node.metadata:
            file_name = node.metadata.get('file_path')
        
        # Check in the raw node data from services
        if not file_name and 'typed_node' in services:
            typed_node = services['typed_node']
            if hasattr(typed_node, 'to_dict'):
                node_dict = typed_node.to_dict()
                file_name = node_dict.get('file_path') or node_dict.get('file_name')

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