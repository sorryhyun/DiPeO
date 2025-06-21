"""
DB node handler - handles file operations and data sources
"""

import json
import asyncio
import io
import sys
import logging
from typing import Dict, Any, List, Callable, Awaitable
from ..schemas.db import DBNodeProps, DBSubType
from ..types import ExecutionContext
from src.__generated__.models import NodeOutput
from ..decorators import node
from ..utils import process_inputs, log_action

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
    
    log_action(logger, context.node_id, f"Executing DB node with subType: {sub_type}")
    
    # Define operation handlers
    operations: Dict[DBSubType, Callable[[], Awaitable[Any]]] = {
        DBSubType.FILE: lambda: _execute_file_read(source_details, services.get('file_service')),
        DBSubType.FIXED_PROMPT: lambda: _execute_fixed_prompt(source_details),
        DBSubType.CODE: lambda: _execute_code(source_details, _prepare_code_inputs(inputs)),
        DBSubType.API_TOOL: lambda: _execute_api_tool(source_details, context),
    }
    
    try:
        handler = operations.get(sub_type)
        if not handler:
            raise ValueError(f"Unsupported DB node subType: {sub_type}")
        
        # Special check for file service
        if sub_type == DBSubType.FILE:
            file_service = services.get('file_service')
            if not file_service:
                raise RuntimeError("File service not available")
        
        result = await handler()
        
        log_action(logger, context.node_id, "DB node execution completed successfully")
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
            processed_inputs = process_inputs({f"input{i}": v for i, v in enumerate(inputs)})
            
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


