"""Endpoint node handler - passes through data and optionally saves to file."""

from typing import Any

from dipeo_core import BaseNodeHandler, RuntimeContext, register_handler
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
        context: RuntimeContext,
        inputs: dict[str, Any],
        services: dict[str, Any],
    ) -> NodeOutput:
        """Execute endpoint node."""
        file_service = services["file"]

        if props.data is not None:
            result_data = props.data
        else:
            result_data = inputs if inputs else {}

        if props.saveToFile:
            file_path = props.filePath or props.fileName

            if file_path:
                try:
                    if isinstance(result_data, dict) and "default" in result_data:
                        content = str(result_data["default"])
                    else:
                        content = str(result_data)

                    await file_service.write(file_path, content)

                    return create_node_output(
                        {"default": result_data}, {"saved_to": file_path}
                    )
                except Exception as exc:
                    return create_node_output(
                        {"default": result_data}, {"save_error": str(exc)}
                    )

        return create_node_output({"default": result_data})
