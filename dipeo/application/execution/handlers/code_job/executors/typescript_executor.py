"""TypeScript language executor."""

import asyncio
import json
import os
import tempfile
from pathlib import Path
from typing import Any

from .base import BaseCodeExecutor


class TypeScriptExecutor(BaseCodeExecutor):
    """Executor for TypeScript code."""
    
    async def execute_file(
        self,
        file_path: Path,
        inputs: dict[str, Any],
        timeout: int,
        function_name: str = "main"
    ) -> Any:
        """Execute TypeScript file using tsx."""
        # Prepare inputs
        prepared_inputs = self.prepare_inputs(inputs)
        
        # Check if tsx is available, otherwise try ts-node
        tsx_cmd = "tsx"
        
        # Create a temporary wrapper file that calls the main function and outputs JSON
        with tempfile.NamedTemporaryFile(mode='w', suffix='.ts', delete=False) as wrapper:
            wrapper_content = f"""
import * as codeModule from '{file_path.absolute()}';

const inputs = {json.dumps(prepared_inputs)};

// Call the specified function and output result as JSON
const run = async () => {{
    try {{
        const func = codeModule.{function_name};
        if (typeof func !== 'function') {{
            throw new Error(`Function '{function_name}' not found in module`);
        }}
        const result = await func(inputs);
        console.log(JSON.stringify(result));
    }} catch (error) {{
        console.error(JSON.stringify({{
            error: error.message || String(error),
            stack: error.stack
        }}));
        process.exit(1);
    }}
}};

run();
"""
            wrapper.write(wrapper_content)
            wrapper_path = wrapper.name
        
        try:
            # Run TypeScript file with tsx
            proc = await asyncio.create_subprocess_exec(
                tsx_cmd, wrapper_path,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=str(file_path.parent)  # Set working directory to file's directory
            )
            
            try:
                stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=timeout)
            except TimeoutError:
                proc.kill()
                await proc.wait()
                raise TimeoutError(f"TypeScript execution timed out after {timeout} seconds") from None
            
            if proc.returncode != 0:
                # Try to parse error as JSON first
                error_output = stderr.decode().strip() or stdout.decode().strip()
                try:
                    error_data = json.loads(error_output)
                    raise Exception(f"TypeScript execution failed: {error_data.get('error', error_output)}") from None
                except json.JSONDecodeError:
                    raise Exception(f"TypeScript execution failed: {error_output}") from None
            
            # Parse the JSON output
            output = stdout.decode().strip()
            try:
                return json.loads(output)
            except json.JSONDecodeError:
                # If not JSON, return as string
                return output
                
        finally:
            # Clean up temporary wrapper file
            if os.path.exists(wrapper_path):
                os.unlink(wrapper_path)
    
    async def execute_inline(
        self,
        code: str,
        inputs: dict[str, Any],
        timeout: int,
        function_name: str = "main"
    ) -> Any:
        """Execute inline TypeScript code."""
        # Prepare inputs
        _ = self.prepare_inputs(inputs)
        
        # Create a module from the inline code
        module_code = code
        
        # If the code doesn't export the function, wrap it
        if f"export function {function_name}" not in code and f"export const {function_name}" not in code:
            # Wrap the code in a function
            module_code = f"""export function {function_name}(inputs: any): any {{
    {code}
    return (typeof result !== 'undefined') ? result : null;
}}"""
        
        # Create a temporary file to execute the code
        with tempfile.NamedTemporaryFile(mode='w', suffix='.ts', delete=False) as temp_file:
            temp_file.write(module_code)
            temp_file_path = temp_file.name
        
        try:
            # Execute using the file-based method
            result = await self.execute_file(Path(temp_file_path), inputs, timeout, function_name)
            return result
        finally:
            # Clean up temporary file
            if os.path.exists(temp_file_path):
                os.unlink(temp_file_path)