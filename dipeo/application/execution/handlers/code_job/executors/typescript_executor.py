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
        prepared_inputs = self.prepare_inputs(inputs)
        
        tsx_cmd = "tsx"
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.ts', delete=False) as wrapper:
            wrapper_content = f"""
import * as codeModule from '{file_path.absolute()}';

const inputs = {json.dumps(prepared_inputs)};

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
            proc = await asyncio.create_subprocess_exec(
                tsx_cmd, wrapper_path,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=str(file_path.parent)
            )
            
            try:
                stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=timeout)
            except TimeoutError:
                proc.kill()
                await proc.wait()
                raise TimeoutError(f"TypeScript execution timed out after {timeout} seconds") from None
            
            if proc.returncode != 0:
                error_output = stderr.decode().strip() or stdout.decode().strip()
                try:
                    error_data = json.loads(error_output)
                    raise Exception(f"TypeScript execution failed: {error_data.get('error', error_output)}") from None
                except json.JSONDecodeError:
                    raise Exception(f"TypeScript execution failed: {error_output}") from None
            
            output = stdout.decode().strip()
            try:
                return json.loads(output)
            except json.JSONDecodeError:
                return output
                
        finally:
            if os.path.exists(wrapper_path):
                os.unlink(wrapper_path)
    
    async def execute_inline(
        self,
        code: str,
        inputs: dict[str, Any],
        timeout: int,
        function_name: str = "main"
    ) -> Any:
        _ = self.prepare_inputs(inputs)
        module_code = code
        
        if f"export function {function_name}" not in code and f"export const {function_name}" not in code:
            module_code = f"""export function {function_name}(inputs: any): any {{
    {code}
    return (typeof result !== 'undefined') ? result : null;
}}"""
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.ts', delete=False) as temp_file:
            temp_file.write(module_code)
            temp_file_path = temp_file.name
        
        try:
            result = await self.execute_file(Path(temp_file_path), inputs, timeout, function_name)
            return result
        finally:
            if os.path.exists(temp_file_path):
                os.unlink(temp_file_path)