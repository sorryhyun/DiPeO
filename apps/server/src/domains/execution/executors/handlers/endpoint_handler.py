"""
Handler for Endpoint nodes - terminal nodes with optional file saving
"""

from typing import Dict, Any
import logging

from ..schemas.endpoint import EndpointNodeProps
from ..types import ExecutionContext
from src.__generated__.models import NodeOutput
from ..executor_utils import substitute_variables
from ..decorators import node

logger = logging.getLogger(__name__)


@node(
    node_type="endpoint",
    schema=EndpointNodeProps,
    description="Terminal node for data output with optional file saving",
    requires_services=["file_service"]
)
async def endpoint_handler(
    props: EndpointNodeProps,
    context: ExecutionContext,
    inputs: Dict[str, Any],
    services: Dict[str, Any]
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
        file_service = services.get('file_service')
        
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
                return NodeOutput(
                    value=content,
                    metadata={
                        **metadata,
                        "error": f"Failed to save file {props.filePath}: {str(e)}",
                        "file_saved": False
                    }
                )
        else:
            logger.warning("File service not available for endpoint node")
            return NodeOutput(
                value=content,
                metadata={
                    **metadata,
                    "error": "File service not available",
                    "file_saved": False
                }
            )
    
    # Return unified NodeOutput format
    return NodeOutput(
        value=content,
        metadata={
            **metadata,
            "file_saved": result_data["file_saved"],
            "file_path": result_data.get("file_path"),
            "file_format": result_data.get("file_format")
        }
    )


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