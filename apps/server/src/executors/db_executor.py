"""
DB node executor - handles file operations and data sources
"""

from typing import Dict, Any
import time
import logging
import json

from .base_executor import ServerOnlyExecutor, ValidationResult, ExecutorResult
from ..services.unified_file_service import UnifiedFileService
from ..exceptions import ValidationError, FileOperationError

logger = logging.getLogger(__name__)


class DBExecutor(ServerOnlyExecutor):
    """
    DB node executor that handles file operations and data sources.
    Supports file reading, fixed prompts, and API tool integrations.
    """
    
    def __init__(self, file_service: UnifiedFileService):
        super().__init__()
        self.file_service = file_service
    
    async def validate(self, node: Dict[str, Any], context: 'ExecutionContext') -> ValidationResult:
        """Validate DB node configuration"""
        errors = []
        warnings = []
        
        properties = node.get("properties", {})
        sub_type = properties.get("subType", "file")
        source_details = properties.get("sourceDetails", "")
        
        if not source_details:
            errors.append("Source details are required")
        
        if sub_type == "file":
            # Validate file path
            if not source_details:
                errors.append("File path is required for file subType")
            elif any(char in source_details for char in ["../", "..\\"]):
                errors.append("File path cannot contain directory traversal sequences")
        
        elif sub_type == "fixed_prompt":
            # No additional validation needed for fixed prompts
            pass
        
        elif sub_type == "api_tool":
            # Validate API configuration
            try:
                if isinstance(source_details, str):
                    api_config = json.loads(source_details)
                else:
                    api_config = source_details
                
                api_type = api_config.get("apiType", "").lower()
                if not api_type:
                    errors.append("API type is required for api_tool subType")
                elif api_type not in ["notion"]:
                    warnings.append(f"API type '{api_type}' may not be fully supported")
                
            except json.JSONDecodeError:
                errors.append("Invalid JSON in source details for api_tool subType")
        
        else:
            errors.append(f"Unsupported DB node subType: {sub_type}")
        
        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings
        )
    
    async def execute(self, node: Dict[str, Any], context: 'ExecutionContext') -> ExecutorResult:
        """Execute DB node based on its subType"""
        start_time = time.time()
        
        properties = node.get("properties", {})
        sub_type = properties.get("subType", "file")
        source_details = properties.get("sourceDetails", "")
        
        try:
            if sub_type == "file":
                result = await self._execute_file_read(source_details)
            
            elif sub_type == "fixed_prompt":
                result = await self._execute_fixed_prompt(source_details)
            
            elif sub_type == "api_tool":
                result = await self._execute_api_tool(source_details)
            
            else:
                raise ValidationError(f"Unsupported DB node subType: {sub_type}")
            
            execution_time = time.time() - start_time
            
            return ExecutorResult(
                output=result["output"],
                metadata={
                    **result.get("metadata", {}),
                    "subType": sub_type,
                    "executionTime": execution_time
                },
                cost=0.0,
                execution_time=execution_time
            )
        
        except Exception as e:
            return ExecutorResult(
                output=None,
                error=str(e),
                metadata={
                    "subType": sub_type,
                    "error": str(e)
                },
                cost=0.0,
                execution_time=time.time() - start_time
            )
    
    async def _execute_file_read(self, file_path: str) -> Dict[str, Any]:
        """Execute file reading operation"""
        try:
            content = self.file_service.read(file_path, relative_to="base")
            return {
                "output": content,
                "metadata": {
                    "source_type": "file",
                    "source_path": file_path,
                    "content_length": len(content)
                }
            }
        except Exception as e:
            raise FileOperationError(f"Failed to read file {file_path}: {str(e)}")
    
    async def _execute_fixed_prompt(self, prompt_content: str) -> Dict[str, Any]:
        """Execute fixed prompt operation"""
        return {
            "output": prompt_content,
            "metadata": {
                "source_type": "fixed_prompt",
                "content_length": len(prompt_content)
            }
        }
    
    async def _execute_api_tool(self, api_details: str) -> Dict[str, Any]:
        """Execute API tool operation"""
        try:
            # Parse the API configuration
            if isinstance(api_details, str):
                api_config = json.loads(api_details)
            else:
                api_config = api_details
            
            api_type = api_config.get("apiType", "").lower()
            
            if api_type == "notion":
                return await self._execute_notion_api(api_config)
            else:
                raise ValidationError(f"Unsupported API type: {api_type}")
        
        except json.JSONDecodeError:
            raise ValidationError("Invalid API configuration JSON")
    
    async def _execute_notion_api(self, api_config: Dict[str, Any]) -> Dict[str, Any]:
        """Execute Notion API calls"""
        action = api_config.get("action", "search")
        
        if action == "search":
            query = api_config.get("query", "")
            # Simulate Notion search for now
            # In production, this would use the actual Notion API
            return {
                "output": {
                    "results": [
                        {
                            "object": "page",
                            "id": "mock-page-id",
                            "properties": {
                                "title": {
                                    "type": "title",
                                    "title": [{"text": {"content": f"Mock result for '{query}'"}}]
                                }
                            }
                        }
                    ]
                },
                "metadata": {
                    "api_type": "notion",
                    "action": "search",
                    "query": query
                }
            }
        else:
            raise ValidationError(f"Unsupported Notion action: {action}")