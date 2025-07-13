
from typing import Any, Type

from dipeo.application import register_handler
from dipeo.domain.notion.services import NotionValidator
from dipeo.application.execution.handler_factory import BaseNodeHandler
from dipeo.application.execution.context.unified_execution_context import UnifiedExecutionContext
from dipeo.application.utils import create_node_output
from dipeo.models import NodeOutput, NotionNodeData, NotionOperation
from dipeo.core.static.nodes import NotionNode
from pydantic import BaseModel


@register_handler
class NotionNodeHandler(BaseNodeHandler):
    
    def __init__(self, notion_service=None, api_key_service=None):
        self.notion_service = notion_service
        self.api_key_service = api_key_service
        self.validator = NotionValidator()


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
        props: BaseModel,
        context: UnifiedExecutionContext,
        inputs: dict[str, Any],
        services: dict[str, Any],
    ) -> NodeOutput:
        # Extract typed node from services if available
        typed_node = services.get("typed_node")
        
        if typed_node and isinstance(typed_node, NotionNode):
            # Convert typed node to props
            notion_props = NotionNodeData(
                label=typed_node.label,
                operation=typed_node.operation,
                page_id=typed_node.page_id,
                database_id=typed_node.database_id,
                properties=typed_node.properties
            )
        elif isinstance(props, NotionNodeData):
            notion_props = props
        else:
            # Handle unexpected case
            return create_node_output(
                {"default": ""}, 
                {"error": "Invalid node data provided"},
                node_id=context.current_node_id,
                executed_nodes=context.executed_nodes
            )
        
        return await self._execute_notion_operation(notion_props, context, inputs, services)
    
    async def _execute_notion_operation(
        self,
        props: NotionNodeData,
        context: UnifiedExecutionContext,
        inputs: dict[str, Any],
        services: dict[str, Any],
    ) -> NodeOutput:
        notion_service = self.notion_service or services["notion_service"]
        api_key_service = self.api_key_service or services["api_key_service"]
        
        # Get the Notion API key
        api_keys = api_key_service.list_api_keys()
        notion_key = next(
            (k for k in api_keys if k["service"] == "notion"), 
            None
        )
        if not notion_key:
            raise ValueError("No Notion API key configured")
        
        api_key = notion_key["key"]
        
        # Validate API key
        api_key_result = self.validator.validate_api_key(api_key)
        if api_key_result.has_errors():
            raise ValueError(f"Invalid API key: {api_key_result.errors[0].message}")
        
        # Validate operation configuration
        validation_result = self.validator.validate_operation_config(
            operation=props.operation,
            page_id=props.page_id,
            database_id=props.database_id,
            inputs=inputs
        )
        
        if validation_result.has_errors():
            raise ValueError(validation_result.errors[0].message)
        
        # Execute based on operation type
        if props.operation == NotionOperation.READ_PAGE:
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
            # For now, we can only append blocks to a page
            blocks = inputs.get("blocks", [])
            if blocks:
                result = await notion_service.append_blocks(props.page_id, blocks, api_key)
            else:
                raise ValueError("UPDATE_PAGE requires blocks to append")
                
        elif props.operation == NotionOperation.QUERY_DATABASE:
            filter_query = inputs.get("filter", None)
            sorts = inputs.get("sorts", None)
            result = await notion_service.query_database(
                database_id=props.database_id,
                filter=filter_query,
                sorts=sorts,
                api_key=api_key
            )
            
        else:
            # This should have been caught by validation, but just in case
            raise ValueError(f"Unsupported Notion operation: {props.operation}")
            
        return create_node_output(
            {"default": result},
            node_id=context.current_node_id,
            executed_nodes=context.executed_nodes
        )
