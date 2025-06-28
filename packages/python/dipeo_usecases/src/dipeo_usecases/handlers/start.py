"""Start node handler - the kick-off point for diagram execution."""

from typing import Any

from dipeo_core import BaseNodeHandler, RuntimeContext, register_handler
from dipeo_core.execution import create_node_output
from dipeo_domain.models import NodeOutput, StartNodeData
from pydantic import BaseModel


@register_handler
class StartNodeHandler(BaseNodeHandler):
    """Handler for start nodes."""

    @property
    def node_type(self) -> str:
        return "start"

    @property
    def schema(self) -> type[BaseModel]:
        return StartNodeData

    @property
    def description(self) -> str:
        return "Kick-off node: no input, always succeeds"

    async def execute(
        self,
        props: StartNodeData,
        context: RuntimeContext,
        inputs: dict[str, Any],
        services: dict[str, Any],
    ) -> NodeOutput:
        """Execute start node."""
        return create_node_output({"default": ""}, {"message": "Execution started"})
