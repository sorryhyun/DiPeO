"""Notion node handler - integrates with Notion API."""

from typing import Any

from dipeo_core import BaseNodeHandler, RuntimeContext, register_handler
from dipeo_core.execution import create_node_output
from dipeo_domain.models import NodeOutput, NotionNodeData, NotionOperation
from pydantic import BaseModel


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
        return ["notion_service", "api_key_service"]

    @property
    def description(self) -> str:
        return "Executes Notion API operations"

    async def execute(
        self,
        props: NotionNodeData,
        context: RuntimeContext,
        inputs: dict[str, Any],
        services: dict[str, Any],
    ) -> NodeOutput:
        """Execute notion node based on operation type."""
        notion_service = services["notion_service"]
        api_key_service = services["api_key_service"]
        
        # Get the Notion API key
        api_keys = api_key_service.list_api_keys()
        notion_key = next(
            (k for k in api_keys if k["service"] == "notion"), 
            None
        )
        if not notion_key:
            raise ValueError("No Notion API key configured")
        
        api_key = notion_key["key"]
        
        # Execute based on operation type
        if props.operation == NotionOperation.READ_PAGE:
            if not props.page_id:
                raise ValueError("page_id is required for READ_PAGE operation")
            result = await notion_service.retrieve_page(props.page_id, api_key)
            
        elif props.operation == NotionOperation.CREATE_PAGE:
            # Extract page data from inputs
            parent = inputs.get("parent", {})
            properties = inputs.get("properties", {})
            children = inputs.get("children", None)
            result = await notion_service.create_page(
                parent=parent,
                properties=properties,
                children=children,
                api_key=api_key
            )
            
        elif props.operation == NotionOperation.UPDATE_PAGE:
            if not props.page_id:
                raise ValueError("page_id is required for UPDATE_PAGE operation")
            # For now, we can only append blocks to a page
            blocks = inputs.get("blocks", [])
            if blocks:
                result = await notion_service.append_blocks(props.page_id, blocks, api_key)
            else:
                raise ValueError("UPDATE_PAGE requires blocks to append")
                
        elif props.operation == NotionOperation.QUERY_DATABASE:
            if not props.database_id:
                raise ValueError("database_id is required for QUERY_DATABASE operation")
            filter_query = inputs.get("filter", None)
            sorts = inputs.get("sorts", None)
            result = await notion_service.query_database(
                database_id=props.database_id,
                filter=filter_query,
                sorts=sorts,
                api_key=api_key
            )
            
        else:
            raise ValueError(f"Unsupported Notion operation: {props.operation}")
            
        return create_node_output({"default": result})
