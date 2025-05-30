import asyncio
from typing import Any, List

from .constants import DBBlockSubType
from .exceptions import FileOperationError, DatabaseError, ValidationError
from .utils.dependencies import get_unified_file_service
from .utils.output_processor import OutputProcessor


async def run_db_block(data: dict, inputs: List[Any]) -> Any:
    """Handle different DB block subtypes with improved error handling."""
    sub_type = data.get("subType")
    
    if not sub_type:
        raise ValidationError("DB block requires explicit 'subType' specification")
    
    try:
        if sub_type == DBBlockSubType.FIXED_PROMPT.value:
            return data.get("sourceDetails", "")
        
        elif sub_type == DBBlockSubType.FILE.value:
            return await _handle_file_read(data)
        
        elif sub_type == DBBlockSubType.CODE.value:
            return await _handle_code_execution(data, inputs)
        
        else:
            raise ValidationError(f"Unsupported dbBlock subType: {sub_type}")
            
    except Exception as e:
        if isinstance(e, (ValidationError, FileOperationError, DatabaseError)):
            raise
        raise DatabaseError(f"DB block execution failed: {e}")


async def _handle_file_read(data: dict) -> str:
    """Handle file reading with security checks."""
    source_path = data.get("sourceDetails", "")
    
    file_service = get_unified_file_service()
    return file_service.read(source_path, relative_to="base")


async def _handle_code_execution(data: dict, inputs: List[Any]) -> Any:
    """Handle code execution in sandbox."""
    snippet = data.get("sourceDetails", "")
    
    def _run():
        import builtins
        import io
        import sys
        
        stdout_buffer = io.StringIO()
        original_stdout = sys.stdout
        
        try:
            sys.stdout = stdout_buffer
            
            safe_globals = {"__builtins__": builtins}
            
            # Process inputs to handle PersonJob outputs
            processed_inputs = OutputProcessor.process_list(inputs)
            
            local_env = {"inputs": processed_inputs}
            
            exec(snippet, safe_globals, local_env)
            
        finally:
            sys.stdout = original_stdout
        
        if "result" in local_env:
            return local_env["result"]
        return stdout_buffer.getvalue()
    
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, _run)


# db_target_block functionality has been deprecated and removed.
# Use 'endpoint' block type with saveToFile capability instead.
