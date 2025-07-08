"""Endpoint node handler - passes through data and optionally saves to file."""

from typing import Any

from dipeo.application import BaseNodeHandler, register_handler
from dipeo.domain.services.ports.execution_context import ExecutionContextPort
from dipeo.application.utils import create_node_output
from dipeo.models import EndpointNodeData, NodeOutput
from pydantic import BaseModel


@register_handler
class EndpointNodeHandler(BaseNodeHandler):
    """Handler for endpoint nodes."""

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
        props: EndpointNodeData,
        context: ExecutionContextPort,
        inputs: dict[str, Any],
        services: dict[str, Any],
    ) -> NodeOutput:
        """Execute endpoint node."""
        # Get service from context or fallback to services dict
        file_service = context.get_service("file")
        if not file_service:
            file_service = services.get("file")

        # Endpoint nodes pass through their inputs
        result_data = inputs if inputs else {}

        if props.save_to_file and props.file_name:
            try:
                if isinstance(result_data, dict) and "default" in result_data:
                    content = str(result_data["default"])
                else:
                    content = str(result_data)

                await file_service.write(props.file_name, None, None, content)

                return create_node_output(
                    {"default": result_data}, {"saved_to": props.file_name},
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