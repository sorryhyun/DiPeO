"""Endpoint node handler - passes through data and optionally saves to file."""

from typing import Any

from dipeo_core import BaseNodeHandler, register_handler
from dipeo_core.unified_context import UnifiedExecutionContext
from dipeo_core.execution import create_node_output
from dipeo_domain.models import EndpointNodeData, NodeOutput
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
        context: UnifiedExecutionContext,
        inputs: dict[str, Any],
        services: dict[str, Any],
    ) -> NodeOutput:
        """Execute endpoint node."""
        file_service = services["file"]

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
                    {"default": result_data}, {"saved_to": props.file_name}
                )
            except Exception as exc:
                return create_node_output(
                    {"default": result_data}, {"save_error": str(exc)}
                )

        return create_node_output({"default": result_data})
