
from typing import Any, Type

from dipeo.application import register_handler
from dipeo.application.execution.handler_factory import BaseNodeHandler
from dipeo.application.execution.context.unified_execution_context import UnifiedExecutionContext
from dipeo.application.utils import create_node_output
from dipeo.models import EndpointNodeData, NodeOutput
from dipeo.core.static.nodes import EndpointNode
from dipeo.utils.arrow import unwrap_inputs
from pydantic import BaseModel


@register_handler
class EndpointNodeHandler(BaseNodeHandler):
    
    def __init__(self, file_service=None):
        self.file_service = file_service


    @property
    def node_type(self) -> str:
        return "endpoint"

    @property
    def schema(self) -> type[BaseModel]:
        return EndpointNodeData


    @property
    def requires_services(self) -> list[str]:
        return ["file"]

    @property
    def description(self) -> str:
        return "Endpoint node – pass through data and optionally save to file"

    async def execute(
        self,
        props: BaseModel,
        context: UnifiedExecutionContext,
        inputs: dict[str, Any],
        services: dict[str, Any],
    ) -> NodeOutput:
        # Extract typed node from services if available
        typed_node = services.get("typed_node")
        
        # Get service from context or fallback to services dict
        file_service = self.file_service or services.get("file")
        if not file_service:
            file_service = context.get_service("file")

        # Endpoint nodes pass through their inputs
        result_data = inputs if inputs else {}
        
        # Determine save settings based on node type
        save_to_file = False
        file_name = None
        
        if typed_node and isinstance(typed_node, EndpointNode):
            save_to_file = typed_node.save_to_file
            file_name = typed_node.file_name
        elif isinstance(props, EndpointNodeData):
            save_to_file = props.save_to_file
            file_name = props.file_name

        if save_to_file and file_name:
            try:
                if isinstance(result_data, dict) and "default" in result_data:
                    content = str(result_data["default"])
                else:
                    content = str(result_data)

                await file_service.write(file_name, None, None, content)

                return create_node_output(
                    {"default": result_data}, {"saved_to": file_name},
                    node_id=context.current_node_id,
                    executed_nodes=context.executed_nodes
                )
            except Exception as exc:
                return create_node_output(
                    {"default": result_data}, {"save_error": str(exc)},
                    node_id=context.current_node_id,
                    executed_nodes=context.executed_nodes
                )

        return create_node_output(
            {"default": result_data},
            node_id=context.current_node_id,
            executed_nodes=context.executed_nodes
        )