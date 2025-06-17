"""
Notion node schema - defines properties for Notion API operations
"""

from pydantic import BaseModel, Field, field_validator, model_validator
from typing import Optional, Literal, Dict, Any, List, Union
from enum import Enum
import json


class NotionOperation(str, Enum):
    """Supported Notion operations"""
    READ_PAGE = "read_page"
    LIST_BLOCKS = "list_blocks"
    APPEND_BLOCKS = "append_blocks"
    UPDATE_BLOCK = "update_block"
    QUERY_DATABASE = "query_database"
    CREATE_PAGE = "create_page"
    EXTRACT_TEXT = "extract_text"


class NotionNodeProps(BaseModel):
    """Properties for Notion node that handles Notion API operations"""
    
    operation: NotionOperation = Field(
        ...,
        description="Type of Notion operation to perform"
    )
    
    apiKeyId: str = Field(
        ...,
        alias="apiKeyId",
        description="ID of the Notion API key to use"
    )
    
    # Operation-specific fields
    pageId: Optional[str] = Field(
        None,
        alias="pageId",
        description="Notion page ID (required for page operations)"
    )
    
    blockId: Optional[str] = Field(
        None,
        alias="blockId",
        description="Notion block ID (required for update_block)"
    )
    
    databaseId: Optional[str] = Field(
        None,
        alias="databaseId",
        description="Notion database ID (required for query_database)"
    )
    
    # Data fields
    blocks: Optional[str] = Field(
        None,
        description="JSON string of blocks to append (for append_blocks)"
    )
    
    blockData: Optional[str] = Field(
        None,
        alias="blockData",
        description="JSON string of block data (for update_block)"
    )
    
    filter: Optional[str] = Field(
        None,
        description="JSON string of database filter (for query_database)"
    )
    
    sorts: Optional[str] = Field(
        None,
        description="JSON string of database sorts (for query_database)"
    )
    
    parentConfig: Optional[str] = Field(
        None,
        alias="parentConfig",
        description="JSON string of parent configuration (for create_page)"
    )
    
    pageProperties: Optional[str] = Field(
        None,
        alias="pageProperties",
        description="JSON string of page properties (for create_page)"
    )
    
    children: Optional[str] = Field(
        None,
        description="JSON string of initial page content blocks (for create_page)"
    )
    
    @field_validator('apiKeyId')
    @classmethod
    def validate_api_key_not_empty(cls, v: str) -> str:
        """Ensure API key ID is not empty"""
        if not v.strip():
            raise ValueError("API key ID cannot be empty")
        return v
    
    @field_validator('blocks', 'blockData', 'filter', 'sorts', 'parentConfig', 'pageProperties', 'children')
    @classmethod
    def validate_json_fields(cls, v: Optional[str]) -> Optional[str]:
        """Validate that JSON fields contain valid JSON when provided"""
        if v and v.strip():
            try:
                json.loads(v)
            except json.JSONDecodeError as e:
                raise ValueError(f"Invalid JSON: {e}")
        return v
    
    @model_validator(mode='after')
    def validate_operation_requirements(self) -> 'NotionNodeProps':
        """Validate that required fields are provided based on operation"""
        operation = self.operation
        
        if operation in [NotionOperation.READ_PAGE, NotionOperation.LIST_BLOCKS]:
            if not self.pageId:
                raise ValueError(f"pageId is required for {operation} operation")
        
        elif operation == NotionOperation.APPEND_BLOCKS:
            if not self.pageId:
                raise ValueError("pageId is required for append_blocks operation")
            if not self.blocks:
                raise ValueError("blocks data is required for append_blocks operation")
        
        elif operation == NotionOperation.UPDATE_BLOCK:
            if not self.blockId:
                raise ValueError("blockId is required for update_block operation")
            if not self.blockData:
                raise ValueError("blockData is required for update_block operation")
        
        elif operation == NotionOperation.QUERY_DATABASE:
            if not self.databaseId:
                raise ValueError("databaseId is required for query_database operation")
        
        elif operation == NotionOperation.CREATE_PAGE:
            if not self.parentConfig:
                raise ValueError("parentConfig is required for create_page operation")
            if not self.pageProperties:
                raise ValueError("pageProperties is required for create_page operation")
        
        # extract_text doesn't require specific fields as it works on input data
        
        return self
    
    class Config:
        use_enum_values = True
        json_schema_extra = {
            "examples": [
                {
                    "operation": "read_page",
                    "apiKeyId": "notion_api_key_1",
                    "pageId": "12345678-1234-1234-1234-123456789012"
                },
                {
                    "operation": "append_blocks",
                    "apiKeyId": "notion_api_key_1",
                    "pageId": "12345678-1234-1234-1234-123456789012",
                    "blocks": '[{"object": "block", "type": "paragraph", "paragraph": {"rich_text": [{"type": "text", "text": {"content": "Hello world"}}]}}]'
                },
                {
                    "operation": "query_database",
                    "apiKeyId": "notion_api_key_1",
                    "databaseId": "87654321-4321-4321-4321-210987654321",
                    "filter": '{"property": "Status", "select": {"equals": "Done"}}',
                    "sorts": '[{"property": "Created", "direction": "descending"}]'
                }
            ]
        }