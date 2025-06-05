"""
Notion node executor - handles Notion API operations
"""

from typing import Dict, Any, TYPE_CHECKING, Optional
import time
import logging
import json

if TYPE_CHECKING:
    from ..engine import ExecutionContext

from .base_executor import BaseExecutor, ValidationResult, ExecutorResult
from .validator import validate_required_fields, validate_json_field
from .utils import get_input_values, substitute_variables
from ...exceptions import ValidationError, DiagramExecutionError
from ...utils.output_processor import OutputProcessor

logger = logging.getLogger(__name__)


class NotionExecutor(BaseExecutor):
    """
    Notion node executor that handles Notion API operations.
    Supports page reading, block operations, database queries, and content creation.
    """
    
    def __init__(self, notion_service=None):
        super().__init__()
        self.notion_service = notion_service
    
    async def validate(self, node: Dict[str, Any], context: 'ExecutionContext') -> ValidationResult:
        """Validate Notion node configuration"""
        errors = []
        warnings = []
        
        properties = node.get("properties", {})
        
        # Validate required fields
        field_errors = validate_required_fields(
            properties,
            ["operation", "apiKeyId"],
            {
                "operation": "Notion operation type",
                "apiKeyId": "Notion API key"
            }
        )
        errors.extend(field_errors)
        
        # Validate operation type
        operation = properties.get("operation", "")
        valid_operations = ["read_page", "list_blocks", "append_blocks", "update_block", 
                          "query_database", "create_page", "extract_text"]
        
        if operation and operation not in valid_operations:
            errors.append(f"Invalid operation '{operation}'. Must be one of: {', '.join(valid_operations)}")
        
        # Validate API key
        api_key_id = properties.get("apiKeyId", "")
        if api_key_id and api_key_id not in context.api_keys:
            errors.append(f"API key '{api_key_id}' not found in available keys")
        
        # Operation-specific validation
        if operation == "read_page" or operation == "list_blocks":
            if not properties.get("pageId"):
                errors.append("Page ID is required for read_page and list_blocks operations")
        
        elif operation == "append_blocks":
            if not properties.get("pageId"):
                errors.append("Page ID is required for append_blocks operation")
            
            # Validate blocks structure
            blocks_str = properties.get("blocks", "")
            if blocks_str:
                blocks, json_error = validate_json_field(
                    properties,
                    "blocks",
                    required=True
                )
                if json_error:
                    errors.append(f"Invalid blocks JSON: {json_error}")
        
        elif operation == "update_block":
            if not properties.get("blockId"):
                errors.append("Block ID is required for update_block operation")
        
        elif operation == "query_database":
            if not properties.get("databaseId"):
                errors.append("Database ID is required for query_database operation")
        
        elif operation == "create_page":
            if not properties.get("parentConfig"):
                errors.append("Parent configuration is required for create_page operation")
        
        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings
        )
    
    async def execute(self, node: Dict[str, Any], context: 'ExecutionContext') -> ExecutorResult:
        """Execute Notion API operation"""
        start_time = time.time()
        
        if not self.notion_service:
            return ExecutorResult(
                output=None,
                error="Notion service not initialized",
                execution_time=time.time() - start_time
            )
        
        properties = node.get("properties", {})
        operation = properties.get("operation", "")
        api_key_id = properties.get("apiKeyId", "")
        
        # Get API key
        api_key_info = context.api_keys.get(api_key_id, {})
        api_key = api_key_info.get("key", "") if isinstance(api_key_info, dict) else ""
        
        if not api_key:
            return ExecutorResult(
                output=None,
                error=f"API key '{api_key_id}' not found or invalid",
                execution_time=time.time() - start_time
            )
        
        # Get inputs from previous nodes
        inputs = get_input_values(node, context)
        
        try:
            result = None
            
            if operation == "read_page":
                page_id = self._substitute_variables(properties.get("pageId", ""), inputs)
                result = await self.notion_service.retrieve_page(page_id, api_key)
            
            elif operation == "list_blocks":
                page_id = self._substitute_variables(properties.get("pageId", ""), inputs)
                blocks = await self.notion_service.list_blocks(page_id, api_key)
                result = {"blocks": blocks, "count": len(blocks)}
            
            elif operation == "append_blocks":
                page_id = self._substitute_variables(properties.get("pageId", ""), inputs)
                blocks_str = self._substitute_variables(properties.get("blocks", "[]"), inputs)
                blocks = json.loads(blocks_str) if isinstance(blocks_str, str) else blocks_str
                result = await self.notion_service.append_blocks(page_id, blocks, api_key)
            
            elif operation == "update_block":
                block_id = self._substitute_variables(properties.get("blockId", ""), inputs)
                block_data_str = self._substitute_variables(properties.get("blockData", "{}"), inputs)
                block_data = json.loads(block_data_str) if isinstance(block_data_str, str) else block_data_str
                result = await self.notion_service.update_block(block_id, block_data, api_key)
            
            elif operation == "query_database":
                database_id = self._substitute_variables(properties.get("databaseId", ""), inputs)
                filter_str = properties.get("filter", "")
                sorts_str = properties.get("sorts", "")
                
                filter_obj = json.loads(filter_str) if filter_str else None
                sorts_obj = json.loads(sorts_str) if sorts_str else None
                
                results = await self.notion_service.query_database(
                    database_id, filter_obj, sorts_obj, api_key
                )
                result = {"results": results, "count": len(results)}
            
            elif operation == "create_page":
                parent_str = self._substitute_variables(properties.get("parentConfig", "{}"), inputs)
                properties_str = self._substitute_variables(properties.get("pageProperties", "{}"), inputs)
                children_str = properties.get("children", "")
                
                parent = json.loads(parent_str) if isinstance(parent_str, str) else parent_str
                page_properties = json.loads(properties_str) if isinstance(properties_str, str) else properties_str
                children = json.loads(children_str) if children_str else None
                
                result = await self.notion_service.create_page(
                    parent, page_properties, children, api_key
                )
            
            elif operation == "extract_text":
                # Extract text from blocks in input
                if inputs:
                    # Process inputs to handle wrapped outputs
                    processed_inputs = OutputProcessor.process_list(inputs)
                    
                    # Extract blocks from the first input that contains them
                    blocks = None
                    for input_data in processed_inputs:
                        if isinstance(input_data, dict) and "blocks" in input_data:
                            blocks = input_data["blocks"]
                            break
                    
                    if blocks:
                        text = self.notion_service.extract_text_from_blocks(blocks)
                        result = {"text": text, "block_count": len(blocks)}
                    else:
                        result = {"text": "", "block_count": 0, "error": "No blocks found in input"}
                else:
                    result = {"text": "", "block_count": 0, "error": "No input provided"}
            
            else:
                raise ValidationError(f"Unknown operation: {operation}")
            
            execution_time = time.time() - start_time
            
            return ExecutorResult(
                output=result,
                metadata={
                    "operation": operation,
                    "executionTime": execution_time
                },
                execution_time=execution_time
            )
        
        except Exception as e:
            logger.error(f"Notion operation failed: {e}")
            return ExecutorResult(
                output=None,
                error=str(e),
                metadata={
                    "operation": operation,
                    "error": str(e)
                },
                execution_time=time.time() - start_time
            )
    
    def _substitute_variables(self, text: str, inputs: list) -> str:
        """Substitute variables in text with input values"""
        if not text:
            return text
        
        # Process inputs to handle wrapped outputs
        processed_inputs = OutputProcessor.process_list(inputs)
        
        # Create a mapping of variables to values
        variables = {}
        for i, value in enumerate(processed_inputs):
            variables[f"input{i}"] = str(value)
            # Also support named variables if the input is a dict
            if isinstance(value, dict):
                for k, v in value.items():
                    variables[k] = str(v)
        
        # Use the utility function to substitute variables
        return substitute_variables(text, variables)