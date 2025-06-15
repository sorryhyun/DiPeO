"""
DB node executor - handles file operations and data sources
"""

from typing import Dict, Any, TYPE_CHECKING
import time
import logging
import json
import asyncio
import builtins
import io
import sys

if TYPE_CHECKING:
    from ..execution_engine import Ctx as ExecutionContext

from .base_executor import BaseExecutor, ValidationResult, ExecutorResult
from .validator import validate_file_path, validate_json_field, validate_required_fields
from ..services.file_service import FileService
from ..exceptions import ValidationError, FileOperationError
from ..utils.output_processor import OutputProcessor

logger = logging.getLogger(__name__)


class DBExecutor(BaseExecutor):
    """
    DB node executor that handles file operations and data sources.
    Supports file reading, fixed prompts, code execution, and API tool integrations.
    """
    
    def __init__(self, file_service: FileService):
        super().__init__()
        self.file_service = file_service
    
    async def validate(self, node: Dict[str, Any], context: 'ExecutionContext') -> ValidationResult:
        """Validate DB node configuration"""
        errors = []
        warnings = []
        
        properties = node.get("properties", {})
        sub_type = properties.get("subType", "file")
        source_details = properties.get("sourceDetails", "")
        
        # Check if source details is empty or just contains placeholder text
        is_placeholder = source_details.strip() in ["", "Enter your fixed prompt or content here"]
        
        if not source_details or is_placeholder:
            if sub_type == "file":
                errors.append("File path is required for file subType. Please specify a valid file path (e.g., 'data/input.txt').")
            else:
                errors.append(f"Source details are required for DB node (subType: {sub_type}). Please provide content for your fixed prompt.")
        
        elif sub_type == "file":
            # Use centralized file path validation
            path_errors = validate_file_path(
                source_details,
                field_name="File path",
                allow_empty=False
            )
            errors.extend(path_errors)
        
        elif sub_type == "fixed_prompt":
            # No additional validation needed for fixed prompts
            pass
        
        elif sub_type == "code":
            # Validate code snippet using centralized validation
            code_errors = validate_required_fields(
                properties,
                ["sourceDetails"],
                {"sourceDetails": "Code snippet"}
            )
            errors.extend(code_errors)
        
        elif sub_type == "api_tool":
            # Validate API configuration using centralized JSON validation
            api_config, json_error = validate_json_field(
                properties,
                "sourceDetails",
                required=True
            )
            
            if json_error:
                errors.append(json_error)
            elif api_config:
                api_type = api_config.get("apiType", "").lower()
                if not api_type:
                    errors.append("API type is required for api_tool subType")
                elif api_type not in ["notion"]:
                    warnings.append(f"API type '{api_type}' may not be fully supported")
        
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
            
            elif sub_type == "code":
                # Get inputs from previous nodes
                inputs = self._get_node_inputs(node, context)
                result = await self._execute_code(source_details, inputs)
            
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
            
            # Currently no API types are supported
            # This structure is kept for future API integrations
            raise ValidationError(f"API type '{api_type}' is not currently supported")
        
        except json.JSONDecodeError:
            raise ValidationError("Invalid API configuration JSON")
    
    
    async def _execute_code(self, code_snippet: str, inputs: list) -> Dict[str, Any]:
        """Execute code in sandbox environment"""
        def _run_code():
            stdout_buffer = io.StringIO()
            original_stdout = sys.stdout
            
            try:
                sys.stdout = stdout_buffer
                
                safe_globals = {"__builtins__": builtins}
                
                # Process inputs to handle PersonJob outputs
                processed_inputs = OutputProcessor.process_list(inputs)
                
                local_env = {"inputs": processed_inputs}
                
                exec(code_snippet, safe_globals, local_env)
                
            finally:
                sys.stdout = original_stdout
            
            if "result" in local_env:
                return local_env["result"]
            return stdout_buffer.getvalue()
        
        loop = asyncio.get_event_loop()
        output = await loop.run_in_executor(None, _run_code)
        
        return {
            "output": output,
            "metadata": {
                "source_type": "code",
                "inputs_count": len(inputs),
                "code_length": len(code_snippet)
            }
        }
    
    def _get_node_inputs(self, node: Dict[str, Any], context: 'ExecutionContext') -> list:
        """Get inputs from previous nodes"""
        node_id = node.get("id")
        inputs = []
        
        # Get incoming arrows to this node
        incoming_arrows = context.incoming_arrows.get(node_id, [])
        
        # Collect outputs from source nodes
        for arrow in incoming_arrows:
            source_node_id = arrow.get("source")
            if source_node_id in context.node_outputs:
                inputs.append(context.node_outputs[source_node_id])
        
        return inputs