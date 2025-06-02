"""
Endpoint node executor - handles output and optional file saving
"""

from typing import Dict, Any
import time
import logging

from .base_executor import ClientSafeExecutor, ValidationResult, ExecutorResult
from ....services.file_service import FileService

logger = logging.getLogger(__name__)


class EndpointExecutor(ClientSafeExecutor):
    """
    Endpoint node executor that handles terminal nodes with optional file saving.
    Endpoint nodes mark the end of execution flows and can save results to files.
    """
    
    def __init__(self, file_service: FileService = None):
        super().__init__()
        self.file_service = file_service
    
    async def validate(self, node: Dict[str, Any], context: 'ExecutionContext') -> ValidationResult:
        """Validate endpoint node configuration"""
        errors = []
        warnings = []
        
        properties = node.get("properties", {})
        save_to_file = properties.get("saveToFile", False)
        
        if save_to_file:
            file_path = properties.get("filePath", "")
            if not file_path:
                errors.append("File path is required when saveToFile is enabled")
            
            # Validate file path doesn't contain dangerous characters
            if file_path and any(char in file_path for char in ["../", "..\\"]):
                errors.append("File path cannot contain directory traversal sequences")
        
        # Check if endpoint has incoming connections
        if not self.has_incoming_connection(node, context):
            warnings.append("Endpoint node has no incoming connections")
        
        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings
        )
    
    async def execute(self, node: Dict[str, Any], context: 'ExecutionContext') -> ExecutorResult:
        """Execute endpoint node and optionally save to file"""
        start_time = time.time()
        
        properties = node.get("properties", {})
        save_to_file = properties.get("saveToFile", False)
        file_path = properties.get("filePath", "")
        file_format = properties.get("fileFormat", "text")
        
        # Get input values (content to output/save)
        inputs = self.get_input_values(node, context)
        
        # Combine all inputs into content
        content = self._prepare_content(inputs, properties)
        
        result_data = {
            "content": content,
            "file_saved": False
        }
        
        metadata = {
            "content_length": len(str(content)),
            "inputs_count": len(inputs),
            "executionTime": 0
        }
        
        # Save to file if requested
        if save_to_file and file_path and self.file_service:
            try:
                saved_path = await self.file_service.write(
                    file_path,
                    content,
                    relative_to="base",
                    format=file_format
                )
                
                result_data.update({
                    "file_saved": True,
                    "file_path": saved_path,
                    "file_format": file_format
                })
                
                metadata.update({
                    "saved_at": saved_path,
                    "file_format": file_format
                })
                
            except Exception as e:
                return ExecutorResult(
                    output=content,
                    error=f"Failed to save file {file_path}: {str(e)}",
                    metadata=metadata,
                    cost=0.0,
                    execution_time=time.time() - start_time
                )
        
        execution_time = time.time() - start_time
        metadata["executionTime"] = execution_time
        
        return ExecutorResult(
            output=result_data,
            metadata=metadata,
            cost=0.0,
            execution_time=execution_time
        )
    
    def _prepare_content(self, inputs: Dict[str, Any], properties: Dict[str, Any]) -> str:
        """Prepare content from inputs and properties"""
        # Get custom content format if specified
        content_format = properties.get("contentFormat", "")
        
        if content_format:
            # Use custom format with variable substitution
            content = self.substitute_variables(content_format, inputs)
        else:
            # Default: combine all inputs
            if len(inputs) == 1:
                # Single input - use its value directly
                content = str(list(inputs.values())[0])
            else:
                # Multiple inputs - create formatted output
                content_parts = []
                for key, value in inputs.items():
                    if isinstance(value, (dict, list)):
                        import json
                        value_str = json.dumps(value, indent=2)
                    else:
                        value_str = str(value)
                    content_parts.append(f"{key}: {value_str}")
                content = "\n".join(content_parts)
        
        return content