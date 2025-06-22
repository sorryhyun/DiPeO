from __future__ import annotations

import json
from typing import Any, Dict

from ..base import BaseNodeHandler
from ..decorators import node
from ..executor_utils import substitute_variables
from ..schemas.endpoint import EndpointNodeProps
from ..types import RuntimeCtx


@node(
    node_type="endpoint",
    schema=EndpointNodeProps,
    description="Terminal node for data output with optional file saving",
    requires_services=["file_service"],
)
class EndpointHandler(BaseNodeHandler):
    """Endpoint handler for terminal data output."""

    async def _execute_core(
        self,
        props: EndpointNodeProps,
        context: RuntimeCtx,
        inputs: Dict[str, Any],
        services: Dict[str, Any],
    ) -> Any:
        """Process inputs and optionally save to file."""
        content = self._prepare_content(inputs, props)

        self._endpoint_metadata = {
            "content_length": len(str(content)),
            "inputs_count": len(inputs),
            "file_saved": False,
        }

        if props.saveToFile and props.filePath:
            file_service = services["file_service"]

            saved_path = await file_service.write(
                props.filePath, content, relative_to="base", format=props.fileFormat
            )

            self._endpoint_metadata.update(
                {
                    "file_saved": True,
                    "file_path": saved_path,
                    "file_format": props.fileFormat,
                    "saved_at": saved_path,
                }
            )

        return content

    def _build_metadata(
        self,
        start_time: float,
        props: EndpointNodeProps,
        context: RuntimeCtx,
        result: Any,
    ) -> Dict[str, Any]:
        """Build endpoint-specific metadata."""
        metadata = super()._build_metadata(start_time, props, context, result)

        if hasattr(self, "_endpoint_metadata"):
            metadata.update(self._endpoint_metadata)
            delattr(self, "_endpoint_metadata")

        return metadata

    def _prepare_content(self, inputs: Dict[str, Any], props: EndpointNodeProps) -> str:
        """Prepare content from inputs and properties."""
        content_format = props.contentFormat

        if content_format:
            content = substitute_variables(content_format, inputs)
        else:
            if len(inputs) == 1:
                content = str(list(inputs.values())[0])
            else:
                content_parts = []
                for key, value in inputs.items():
                    if isinstance(value, (dict, list)):
                        value_str = json.dumps(value, indent=2)
                    else:
                        value_str = str(value)
                    content_parts.append(f"{key}: {value_str}")
                content = "\n".join(content_parts)

        return content
