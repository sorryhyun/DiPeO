
from typing import TYPE_CHECKING, Any

from pydantic import BaseModel

from dipeo.application.execution.handler_factory import register_handler
from dipeo.application.execution.types import TypedNodeHandler
from dipeo.core.static.generated_nodes import NotionNode
from dipeo.domain.notion.services import NotionValidator
from dipeo.models import NodeOutput, NodeType, NotionNodeData, NotionOperation

if TYPE_CHECKING:
    from dipeo.application.execution.execution_runtime import ExecutionRuntime
    from dipeo.core.dynamic.execution_context import ExecutionContext


@register_handler
class NotionNodeHandler(TypedNodeHandler[NotionNode]):
    
    def __init__(self, notion_service=None, api_key_service=None):
        self.notion_service = notion_service
        self.api_key_service = api_key_service
        self.validator = NotionValidator()


    @property
    def node_class(self) -> type[NotionNode]:
        return NotionNode
    
    @property
    def node_type(self) -> str:
        return NodeType.notion.value

    @property
    def schema(self) -> type[BaseModel]:
        return NotionNodeData
    

    @property
    def requires_services(self) -> list[str]:
        return ["notion_service", "api_key_service"]

    @property
    def description(self) -> str:
        return "Executes Notion API operations"

    async def pre_execute(
        self,
        node: NotionNode,
        execution: "ExecutionRuntime"
    ) -> dict[str, Any]:
        """Pre-execute logic for NotionNode."""
        return {
            "operation": node.operation.value if hasattr(node.operation, 'value') else node.operation,
            "page_id": node.page_id,
            "database_id": node.database_id
        }
    
    async def execute(
        self,
        node: NotionNode,
        context: "ExecutionContext",
        inputs: dict[str, Any],
        services: dict[str, Any],
    ) -> NodeOutput:
        return await self._execute_notion_operation(node, context, inputs, services)
    
    async def _execute_notion_operation(
        self,
        node: NotionNode,
        context: "ExecutionContext",
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
            operation=node.operation,
            page_id=node.page_id,
            database_id=node.database_id,
            inputs=inputs
        )
        
        if validation_result.has_errors():
            raise ValueError(validation_result.errors[0].message)
        
        # Execute based on operation type
        if node.operation == NotionOperation.READ_PAGE:
            result = await notion_service.retrieve_page(node.page_id, api_key)
            
        elif node.operation == NotionOperation.CREATE_PAGE:
            # Extract page data from inputs
            parent = inputs.get("parent", {})
            properties = inputs.get("properties", {})
            children = inputs.get("children")
            result = await notion_service.create_page(
                parent=parent,
                properties=properties,
                children=children,
                api_key=api_key
            )
            
        elif node.operation == NotionOperation.UPDATE_PAGE:
            # For now, we can only append blocks to a page
            blocks = inputs.get("blocks", [])
            if blocks:
                result = await notion_service.append_blocks(node.page_id, blocks, api_key)
            else:
                raise ValueError("UPDATE_PAGE requires blocks to append")
                
        elif node.operation == NotionOperation.QUERY_DATABASE:
            filter_query = inputs.get("filter")
            sorts = inputs.get("sorts")
            result = await notion_service.query_database(
                database_id=node.database_id,
                filter=filter_query,
                sorts=sorts,
                api_key=api_key
            )
            
        else:
            # This should have been caught by validation, but just in case
            raise ValueError(f"Unsupported Notion operation: {node.operation}")
            
        return self._build_output(
            {"default": result},
            context
        )
