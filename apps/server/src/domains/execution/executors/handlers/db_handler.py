"""
DB node handler - handles file operations and data sources
"""

import json
import asyncio
import io
import sys
import builtins
import logging
from typing import Dict, Any, List
from ..schemas.db import DBNodeProps, DBSubType
from ..types import ExecutionContext
from src.__generated__.models import NodeOutput
from ..decorators import node

logger = logging.getLogger(__name__)


@node(
    node_type="db",
    schema=DBNodeProps,
    description="Data source node for file operations and fixed prompts",
    requires_services=["file_service"]
)
async def db_handler(
    props: DBNodeProps,
    context: ExecutionContext,
    inputs: Dict[str, Any],
    services: Dict[str, Any]
) -> Any:
    """Handle DB node execution for various data source operations"""
    
    sub_type = props.subType
    source_details = props.sourceDetails
    
    logger.info(f"Executing DB node with subType: {sub_type}")
    
    try:
        if sub_type == DBSubType.FILE:
            file_service = services.get('file_service')
            if not file_service:
                raise RuntimeError("File service not available")
            result = await _execute_file_read(source_details, file_service)
        
        elif sub_type == DBSubType.FIXED_PROMPT:
            result = await _execute_fixed_prompt(source_details)
        
        elif sub_type == DBSubType.CODE:
            # Convert inputs dict to list for code execution
            input_list = _prepare_code_inputs(inputs)
            result = await _execute_code(source_details, input_list)
        
        elif sub_type == DBSubType.API_TOOL:
            result = await _execute_api_tool(source_details, context)
        
        else:
            raise ValueError(f"Unsupported DB node subType: {sub_type}")
        
        logger.info(f"DB node execution completed successfully")
        # Return unified NodeOutput format
        return NodeOutput(
            value=result,
            metadata={
                "subType": sub_type.value if sub_type else None,
                "dataSource": "file" if sub_type == DBSubType.FILE else "code" if sub_type == DBSubType.CODE else "fixed"
            }
        )
        
    except Exception as e:
        error_msg = f"DB node execution failed: {str(e)}"
        logger.error(error_msg, exc_info=True)
        raise RuntimeError(error_msg)


async def _execute_file_read(file_path: str, file_service: Any) -> str:
    """Execute file reading operation"""
    try:
        # Use file service to read the file
        content = await file_service.read(file_path, relative_to="base")
        logger.info(f"Successfully read file: {file_path} ({len(content)} bytes)")
        return content
    except Exception as e:
        raise RuntimeError(f"Failed to read file {file_path}: {str(e)}")


async def _execute_fixed_prompt(prompt_content: str) -> str:
    """Execute fixed prompt operation - simply returns the content"""
    logger.debug(f"Returning fixed prompt ({len(prompt_content)} characters)")
    return prompt_content


async def _execute_api_tool(api_details: str, context: ExecutionContext) -> Any:
    """Execute API tool operation"""
    try:
        # Parse the API configuration
        api_config = json.loads(api_details)
        api_type = api_config.get("apiType", "").lower()
        
        logger.warning(f"API type '{api_type}' requested but not currently supported")
        
        # Currently no API types are supported
        # This structure is kept for future API integrations
        raise RuntimeError(f"API type '{api_type}' is not currently supported")
    
    except json.JSONDecodeError as e:
        raise RuntimeError(f"Invalid API configuration JSON: {e}")


async def _execute_code(code_snippet: str, inputs: List[Any]) -> Any:
    """Execute code in sandbox environment"""
    
    def _run_code():
        """Run code in isolated context"""
        stdout_buffer = io.StringIO()
        original_stdout = sys.stdout
        
        try:
            sys.stdout = stdout_buffer
            
            # Create restricted globals with safe builtins
            safe_globals = {
                "__builtins__": {
                    # Safe built-in functions
                    "len": len,
                    "range": range,
                    "str": str,
                    "int": int,
                    "float": float,
                    "bool": bool,
                    "list": list,
                    "dict": dict,
                    "set": set,
                    "tuple": tuple,
                    "print": print,
                    "sum": sum,
                    "min": min,
                    "max": max,
                    "abs": abs,
                    "round": round,
                    "sorted": sorted,
                    "enumerate": enumerate,
                    "zip": zip,
                    "map": map,
                    "filter": filter,
                    "any": any,
                    "all": all,
                    "isinstance": isinstance,
                    "type": type,
                    # Add json for data processing
                    "json": json,
                }
            }
            
            # Process inputs to handle special output types
            processed_inputs = _process_inputs(inputs)
            
            # Create local environment with inputs
            local_env = {"inputs": processed_inputs}
            
            # Execute the code
            exec(code_snippet, safe_globals, local_env)
            
        finally:
            sys.stdout = original_stdout
        
        # Return result if defined, otherwise return stdout
        if "result" in local_env:
            return local_env["result"]
        
        stdout_content = stdout_buffer.getvalue()
        return stdout_content if stdout_content else None
    
    # Run code in executor to avoid blocking
    loop = asyncio.get_event_loop()
    output = await loop.run_in_executor(None, _run_code)
    
    logger.info(f"Code execution completed (inputs: {len(inputs)}, code length: {len(code_snippet)})")
    return output


def _prepare_code_inputs(inputs: Dict[str, Any]) -> List[Any]:
    """Convert inputs dict to list for code execution compatibility"""
    if not inputs:
        return []
    
    # If there's only one input, return it as a single-item list
    if len(inputs) == 1:
        return [next(iter(inputs.values()))]
    
    # Otherwise, return all values as a list
    return list(inputs.values())


def _process_inputs(inputs: List[Any]) -> List[Any]:
    """Process inputs to handle special output types like PersonJob outputs"""
    processed = []
    
    for input_item in inputs:
        if isinstance(input_item, dict):
            # Check if this is a PersonJob output
            if "output" in input_item and "conversation_history" in input_item:
                # Extract just the output content
                processed.append(input_item.get("output"))
            else:
                # Regular dict, keep as is
                processed.append(input_item)
        else:
            # Non-dict input, keep as is
            processed.append(input_item)
    
    return processed