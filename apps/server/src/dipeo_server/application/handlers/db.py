"""DB node handler - file-based database operations."""

import contextlib
from typing import Any

from dipeo_core import BaseNodeHandler, RuntimeContext, register_handler
from dipeo_domain.models import DBNodeData, NodeOutput
from pydantic import BaseModel

from dipeo_core.execution import create_node_output


@register_handler
class DBNodeHandler(BaseNodeHandler):
    """Handler for db nodes."""

    @property
    def node_type(self) -> str:
        return "db"

    @property
    def schema(self) -> type[BaseModel]:
        return DBNodeData

    @property
    def requires_services(self) -> list[str]:
        return ["file_service"]

    @property
    def description(self) -> str:
        return "File-based DB node supporting read, write and append operations"

    async def execute(
        self,
        props: DBNodeData,
        context: RuntimeContext,
        inputs: dict[str, Any],
        services: dict[str, Any],
    ) -> NodeOutput:
        """Execute db node."""
        file_service = services["file_service"]

        # Get single input value
        input_val = None
        if inputs:
            # Get first non-empty value
            for _key, val in inputs.items():
                if val is not None:
                    input_val = val
                    break

        try:
            if props.operation == "read":
                if hasattr(file_service, "aread"):
                    result = await file_service.aread(props.sourceDetails)
                else:
                    result = file_service.read(props.sourceDetails)
            elif props.operation == "write":
                await file_service.write(props.sourceDetails, str(input_val))
                result = f"Saved to {props.sourceDetails}"
            elif props.operation == "append":
                existing = ""
                if hasattr(file_service, "aread"):
                    with contextlib.suppress(Exception):
                        existing = await file_service.aread(props.sourceDetails)
                await file_service.write(props.sourceDetails, existing + str(input_val))
                result = f"Appended to {props.sourceDetails}"
            else:
                result = "Unknown operation"
        except Exception as exc:
            result = f"Error: {exc}"

        return create_node_output({"default": result, "topic": result})

