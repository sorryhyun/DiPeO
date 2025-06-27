"""Notion node handler - integrates with Notion API."""

from typing import Any

from dipeo_core import BaseNodeHandler, RuntimeContext, register_handler
from dipeo_domain.models import NodeOutput, NotionNodeData
from pydantic import BaseModel

from dipeo_core.execution import create_node_output


@register_handler
class NotionNodeHandler(BaseNodeHandler):
    """Handler for notion nodes."""

    @property
    def node_type(self) -> str:
        return "notion"

    @property
    def schema(self) -> type[BaseModel]:
        return NotionNodeData

    @property
    def requires_services(self) -> list[str]:
        return ["notion_service"]

    @property
    def description(self) -> str:
        return "Wrapper around notion_service.execute_action"

    async def execute(
        self,
        props: NotionNodeData,
        context: RuntimeContext,
        inputs: dict[str, Any],
        services: dict[str, Any],
    ) -> NodeOutput:
        """Execute notion node."""
        notion_service = services["notion_service"]

        result = await notion_service.execute_action(
            action=props.action,
            database_id=props.database_id,
            data=inputs,
        )
        return create_node_output({"default": result})

