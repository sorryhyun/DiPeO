"""Python language executor."""

import asyncio
import importlib.util
import os
import sys
import tempfile
from pathlib import Path
from typing import Any

from .base import BaseCodeExecutor


class PythonExecutor(BaseCodeExecutor):
    """Executor for Python code."""
    
    async def execute_file(
        self,
        file_path: Path,
        inputs: dict[str, Any],
        timeout: int,
        function_name: str = "main"
    ) -> Any:
        prepared_inputs = self.prepare_inputs(inputs)
        
        spec = importlib.util.spec_from_file_location("code_module", file_path)
        if spec is None or spec.loader is None:
            raise ImportError(f"Cannot load module from {file_path}")
        
        module = importlib.util.module_from_spec(spec)
        
        sys_path_added = []
        file_dir = str(file_path.parent)
        if file_dir not in sys.path:
            sys.path.insert(0, file_dir)
            sys_path_added.append(file_dir)
        
        project_root = os.getenv('DIPEO_BASE_DIR', os.getcwd())
        if project_root not in sys.path:
            sys.path.insert(0, project_root)
            sys_path_added.append(project_root)
        
        try:
            spec.loader.exec_module(module)
            
            if not hasattr(module, function_name):
                raise AttributeError(f"Module {file_path} does not have function '{function_name}'")
            
            func = getattr(module, function_name)
            
            if asyncio.iscoroutinefunction(func):
                result = await asyncio.wait_for(func(prepared_inputs), timeout=timeout)
            else:
                loop = asyncio.get_event_loop()
                result = await asyncio.wait_for(
                    loop.run_in_executor(None, func, prepared_inputs),
                    timeout=timeout
                )
            
            return result
            
        finally:
            for path in reversed(sys_path_added):
                if path in sys.path:
                    sys.path.remove(path)
    
    async def execute_inline(
        self,
        code: str,
        inputs: dict[str, Any],
        timeout: int,
        function_name: str = "main"
    ) -> Any:
        prepared_inputs = self.prepare_inputs(inputs)
        module_code = code
        
        if f"def {function_name}" not in code:
            input_vars = '\n'.join(f'    {k} = inputs.get("{k}")' for k in prepared_inputs)
            indented_code = '\n'.join('    ' + line for line in code.split('\n') if line.strip())
            module_code = f"""def {function_name}(inputs):
{input_vars}
{indented_code}
    return locals().get('result', None)"""
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as temp_file:
            temp_file.write(module_code)
            temp_file_path = temp_file.name
        
        try:
            result = await self.execute_file(Path(temp_file_path), inputs, timeout, function_name)
            return result
        finally:
            if os.path.exists(temp_file_path):
                os.unlink(temp_file_path)