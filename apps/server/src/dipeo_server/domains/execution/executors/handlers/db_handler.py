from __future__ import annotations

import asyncio
import io
import json
import sys
from typing import Any, Callable, Dict, List

from dipeo_domain import DBBlockSubType
from ..schemas.db import DBNodeProps
from ..types import RuntimeExecutionContext
from ..decorators import node
from ..utils import BaseNodeHandler, process_inputs, log_action


@node(
    node_type="db",
    schema=DBNodeProps,
    description="Data source node for file operations and fixed prompts",
    requires_services=["file_service"]
)
class DBHandler(BaseNodeHandler):
    """DB handler for various data source operations.
    
    This refactored version eliminates ~40 lines of boilerplate by:
    - Inheriting error handling and timing from BaseNodeHandler
    - Automatic service validation
    - Simplified metadata building
    """
    
    async def _execute_core(
        self,
        props: DBNodeProps,
        context: RuntimeExecutionContext,
        inputs: Dict[str, Any],
        services: Dict[str, Any]
    ) -> Any:
        """Execute the appropriate DB operation based on subType."""
        sub_type = props.subType
        source_details = props.sourceDetails
        
        log_action(
            self.logger,
            context.current_node_id,
            "Executing DB operation",
            sub_type=sub_type.value if sub_type else None
        )
        
        # Define operation handlers
        operations: Dict[DBBlockSubType, Callable[[], Any]] = {
            DBBlockSubType.file: lambda: self._execute_file_read(source_details, services["file_service"]),
            DBBlockSubType.fixed_prompt: lambda: self._execute_fixed_prompt(source_details),
            DBBlockSubType.code: lambda: self._execute_code(source_details, self._prepare_code_inputs(inputs)),
            DBBlockSubType.api_tool: lambda: self._execute_api_tool(source_details, context),
        }
        
        handler = operations.get(sub_type)
        if not handler:
            raise ValueError(f"Unsupported DB node subType: {sub_type}")
        
        # Execute the operation
        result = await handler()
        
        # Store metadata for later use
        self._sub_type = sub_type
        
        return result
    
    def _build_metadata(
        self,
        start_time: float,
        props: DBNodeProps,
        context: RuntimeExecutionContext,
        result: Any
    ) -> Dict[str, Any]:
        """Build DB-specific metadata."""
        metadata = super()._build_metadata(start_time, props, context, result)
        
        if hasattr(self, '_sub_type'):
            sub_type = self._sub_type
            metadata.update({
                "subType": sub_type.value if sub_type else None,
                "dataSource": self._get_data_source_type(sub_type)
            })
            delattr(self, '_sub_type')
        
        return metadata
    
    def _get_data_source_type(self, sub_type: DBBlockSubType) -> str:
        """Map subType to data source type."""
        mapping = {
            DBBlockSubType.file: "file",
            DBBlockSubType.code: "code",
            DBBlockSubType.fixed_prompt: "fixed",
            DBBlockSubType.api_tool: "api"
        }
        return mapping.get(sub_type, "unknown")
    
    async def _execute_file_read(self, file_path: str, file_service: Any) -> str:
        """Execute file reading operation."""
        try:
            content = await file_service.read(file_path, relative_to="base")
            self.logger.info(f"Successfully read file: {file_path} ({len(content)} bytes)")
            return content
        except Exception as e:
            raise RuntimeError(f"Failed to read file {file_path}: {str(e)}")
    
    async def _execute_fixed_prompt(self, prompt_content: str) -> str:
        """Execute fixed prompt operation - simply returns the content."""
        self.logger.debug(f"Returning fixed prompt ({len(prompt_content)} characters)")
        return prompt_content
    
    async def _execute_api_tool(self, api_details: str, context: RuntimeExecutionContext) -> Any:
        """Execute API tool operation."""
        try:
            api_config = json.loads(api_details)
            api_type = api_config.get("apiType", "").lower()
            
            self.logger.warning(f"API type '{api_type}' requested but not currently supported")
            
            # Currently no API types are supported
            # This structure is kept for future API integrations
            raise RuntimeError(f"API type '{api_type}' is not currently supported")
        
        except json.JSONDecodeError as e:
            raise RuntimeError(f"Invalid API configuration JSON: {e}")
    
    async def _execute_code(self, code_snippet: str, inputs: List[Any]) -> Any:
        """Execute code in sandbox environment."""
        
        def _run_code():
            """Run code in isolated context."""
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
        
        self.logger.info(f"Code execution completed (inputs: {len(inputs)}, code length: {len(code_snippet)})")
        return output
    
    def _prepare_code_inputs(self, inputs: Dict[str, Any]) -> List[Any]:
        """Convert inputs dict to list for code execution compatibility."""
        if not inputs:
            return []
        
        # If there's only one input, return it as a single-item list
        if len(inputs) == 1:
            return [next(iter(inputs.values()))]
        
        # Otherwise, return all values as a list
        return list(inputs.values())