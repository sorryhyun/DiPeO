import asyncio
from typing import Any, List

from .constants import DBBlockSubType, DBTargetSubType, SUPPORTED_DOC_EXTENSIONS, SUPPORTED_CODE_EXTENSIONS
from .exceptions import FileOperationError, DatabaseError, ValidationError
from .utils.dependencies import get_unified_file_service
from .utils.output_processor import OutputProcessor


async def run_db_block(data: dict, inputs: List[Any]) -> Any:
    """Handle different DB block subtypes with improved error handling."""
    sub_type = data.get("subType")
    
    if not sub_type:
        if data.get("source") or data.get("sourceDetails"):
            source = data.get("source") or data.get("sourceDetails", "")
            all_extensions = SUPPORTED_DOC_EXTENSIONS | SUPPORTED_CODE_EXTENSIONS
            if any(source.endswith(ext) for ext in all_extensions):
                sub_type = DBBlockSubType.FILE.value
            else:
                sub_type = DBBlockSubType.FIXED_PROMPT.value
    
    try:
        if sub_type == DBBlockSubType.FIXED_PROMPT.value:
            return data.get("sourceDetails") or data.get("source", "")
        
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
    source_path = data.get("sourceDetails") or data.get("source", "")
    
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


async def run_db_target_block(data: dict, inputs: List[Any]) -> str:
    """Handle different DB target block subtypes with improved error handling."""
    target_type = data.get("targetType")
    details = data.get("targetDetails") or data.get("target", "")
    
    if not target_type and details:
        all_extensions = SUPPORTED_DOC_EXTENSIONS | SUPPORTED_CODE_EXTENSIONS
        if any(details.endswith(ext) for ext in all_extensions):
            target_type = DBTargetSubType.LOCAL_FILE.value
    
    try:
        if target_type == DBTargetSubType.LOCAL_FILE.value:
            return await _handle_file_write(details, inputs)
        
        elif target_type == DBTargetSubType.SQLITE.value:
            return await _handle_sqlite_insert(details, inputs)
        
        else:
            raise ValidationError(f"Unsupported dbTargetBlock subType: {target_type}")
            
    except Exception as e:
        if isinstance(e, (ValidationError, FileOperationError, DatabaseError)):
            raise
        raise DatabaseError(f"DB target block execution failed: {e}")


async def _handle_file_write(details: str, inputs: List[Any]) -> str:
    """Handle file writing with security checks."""
    file_service = get_unified_file_service()
    
    # Extract content, handling PersonJob outputs
    content = ""
    if inputs:
        first_input = inputs[0]
        content = str(OutputProcessor.extract_value(first_input))
    
    relative_path = await file_service.write(details, content, relative_to="results")
    return f"Wrote to {relative_path}"


async def _handle_sqlite_insert(details: str, inputs: List[Any]) -> str:
    """Handle SQLite database insertion."""
    try:
        if ":" not in details:
            raise ValidationError("SQLite details must be in format 'db_path:table_name'")
        
        db_path, table_name = details.split(":", 1)
        
        file_service = get_unified_file_service()
        
        # Extract values, handling PersonJob outputs
        data = []
        for val in inputs:
            extracted_value = OutputProcessor.extract_value(val)
            data.append({"value": str(extracted_value)})
        
        relative_path = file_service.write_sqlite(db_path, table_name, data, relative_to="results")
        
        return f"Inserted {len(inputs)} rows into {table_name} at {relative_path}"
        
    except Exception as e:
        if isinstance(e, (DatabaseError, ValidationError)):
            raise
        raise DatabaseError(f"Database operation failed: {e}")
