
from typing import TYPE_CHECKING, Any

from pydantic import BaseModel

from dipeo.application.execution.handler_factory import register_handler
from dipeo.application.execution.handler_base import TypedNodeHandler
from dipeo.application.execution.execution_request import ExecutionRequest
from dipeo.application.registry import INTEGRATED_API_SERVICE, API_KEY_SERVICE
from dipeo.diagram_generated.generated_nodes import NotionNode, NodeType
from dipeo.core.execution.node_output import DataOutput, ErrorOutput, NodeOutputProtocol
from dipeo.domain.validators import NotionValidator
from dipeo.diagram_generated.models.notion_model import NotionNodeData
from dipeo.diagram_generated import NotionOperation
if TYPE_CHECKING:
    from dipeo.core.execution.execution_context import ExecutionContext


@register_handler
class NotionNodeHandler(TypedNodeHandler[NotionNode]):
    
    def __init__(self, integrated_api_service=None, api_key_service=None):
        self.integrated_api_service = integrated_api_service
        self.api_key_service = api_key_service
        self.validator = NotionValidator()


    @property
    def node_class(self) -> type[NotionNode]:
        return NotionNode
    
    @property
    def node_type(self) -> str:
        return NodeType.NOTION.value

    @property
    def schema(self) -> type[BaseModel]:
        return NotionNodeData
    

    @property
    def requires_services(self) -> list[str]:
        return ["integrated_api_service", "api_key_service"]

    @property
    def description(self) -> str:
        return "Executes Notion API operations"

    async def execute_request(self, request: ExecutionRequest[NotionNode]) -> NodeOutputProtocol:
        return await self._execute_notion_operation(request)
    
    async def _execute_notion_operation(self, request: ExecutionRequest[NotionNode]) -> NodeOutputProtocol:
        # Extract properties from request
        node = request.node
        context = request.context
        inputs = request.inputs
        
        # Get services from ServiceRegistry
        integrated_api_service = self.integrated_api_service or request.services.resolve(INTEGRATED_API_SERVICE)
        api_key_service = self.api_key_service or request.services.resolve(API_KEY_SERVICE)
        
        if not integrated_api_service:
            raise ValueError("Integrated API service not available")
        if not api_key_service:
            raise ValueError("API key service not available")
        
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
        api_key_result = self.validator.validate_api_key(api_key).is_valid
        if not api_key_result:
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
        operation_map = {
            NotionOperation.READ_PAGE: "read_page",
            NotionOperation.CREATE_PAGE: "create_page",
            NotionOperation.UPDATE_PAGE: "update_page",
            NotionOperation.QUERY_DATABASE: "query_database"
        }
        
        operation = operation_map.get(node.operation)
        if not operation:
            raise ValueError(f"Unsupported Notion operation: {node.operation}")
        
        # Prepare configuration based on operation
        config = {}
        resource_id = None
        
        if node.operation == NotionOperation.READ_PAGE:
            resource_id = node.page_id
            
        elif node.operation == NotionOperation.CREATE_PAGE:
            config = {
                "parent": inputs.get("parent", {}),
                "properties": inputs.get("properties", {}),
                "children": inputs.get("children")
            }
            
        elif node.operation == NotionOperation.UPDATE_PAGE:
            resource_id = node.page_id
            blocks = inputs.get("blocks", [])
            if not blocks:
                raise ValueError("UPDATE_PAGE requires blocks to append")
            config = {"blocks": blocks}
                
        elif node.operation == NotionOperation.QUERY_DATABASE:
            resource_id = node.database_id
            config = {
                "filter": inputs.get("filter"),
                "sorts": inputs.get("sorts")
            }
        
        # Execute through integrated API service
        result = await integrated_api_service.execute_operation(
            provider="notion",
            operation=operation,
            config=config,
            resource_id=resource_id,
            api_key=api_key
        )
            
        return DataOutput(
            value={"default": result},
            node_id=node.id,
            metadata={"operation": node.operation}
        )
