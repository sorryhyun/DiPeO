"""
Handler for Endpoint nodes - terminal nodes with optional file saving
"""

from typing import Dict, Any
import time
import logging

from ..schemas.endpoint import EndpointNodeProps
from ..types import ExecutionContext
from ..executor_utils import substitute_variables

logger = logging.getLogger(__name__)


async def endpoint_handler(
    props: EndpointNodeProps,
    context: ExecutionContext,
    inputs: Dict[str, Any]
) -> Any:
    """Handle Endpoint node execution"""
    
    # Prepare content from inputs
    content = _prepare_content(inputs, props)
    
    result_data = {
        "content": content,
        "file_saved": False
    }
    
    metadata = {
        "content_length": len(str(content)),
        "inputs_count": len(inputs)
    }
    
    # Save to file if requested
    if props.saveToFile and props.filePath:
        # Check if file service is available
        file_service = getattr(context, 'file_service', None)
        
        if file_service:
            try:
                saved_path = await file_service.write(
                    props.filePath,
                    content,
                    relative_to="base",
                    format=props.fileFormat
                )
                
                result_data.update({
                    "file_saved": True,
                    "file_path": saved_path,
                    "file_format": props.fileFormat
                })
                
                metadata.update({
                    "saved_at": saved_path,
                    "file_format": props.fileFormat
                })
                
            except Exception as e:
                logger.error(f"Failed to save file {props.filePath}: {str(e)}")
                return {
                    "output": content,
                    "error": f"Failed to save file {props.filePath}: {str(e)}",
                    "metadata": metadata
                }
        else:
            logger.warning("File service not available for endpoint node")
            return {
                "output": content,
                "error": "File service not available",
                "metadata": metadata
            }
    
    return {
        "output": result_data,
        "metadata": metadata
    }


def _prepare_content(inputs: Dict[str, Any], props: EndpointNodeProps) -> str:
    """Prepare content from inputs and properties"""
    # Get custom content format if specified
    content_format = props.contentFormat
    
    if content_format:
        # Use custom format with variable substitution
        content = substitute_variables(content_format, inputs)
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