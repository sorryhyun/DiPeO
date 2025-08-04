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
        """Execute Python file by loading module and calling specified function."""
        # Prepare inputs
        prepared_inputs = self.prepare_inputs(inputs)
        
        # Load the Python module dynamically
        spec = importlib.util.spec_from_file_location("code_module", file_path)
        if spec is None or spec.loader is None:
            raise ImportError(f"Cannot load module from {file_path}")
        
        module = importlib.util.module_from_spec(spec)
        
        # Add the file's directory to sys.path temporarily for imports
        sys_path_added = []
        file_dir = str(file_path.parent)
        if file_dir not in sys.path:
            sys.path.insert(0, file_dir)
            sys_path_added.append(file_dir)
        
        # Also add project root for relative imports
        project_root = os.getenv('DIPEO_BASE_DIR', os.getcwd())
        if project_root not in sys.path:
            sys.path.insert(0, project_root)
            sys_path_added.append(project_root)
        
        try:
            # Execute the module
            spec.loader.exec_module(module)
            
            # Get the function to call
            if not hasattr(module, function_name):
                raise AttributeError(f"Module {file_path} does not have function '{function_name}'")
            
            func = getattr(module, function_name)
            
            # Call the function with inputs
            # Use asyncio.wait_for to implement timeout
            if asyncio.iscoroutinefunction(func):
                result = await asyncio.wait_for(func(prepared_inputs), timeout=timeout)
            else:
                # Run sync function in executor with timeout
                loop = asyncio.get_event_loop()
                result = await asyncio.wait_for(
                    loop.run_in_executor(None, func, prepared_inputs),
                    timeout=timeout
                )
            
            return result
            
        finally:
            # Clean up sys.path
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
        """Execute inline Python code."""
        import logging
        logger = logging.getLogger(__name__)
        
        logger.debug(f"[PythonExecutor] execute_inline called with {len(code)} chars of code")
        logger.debug(f"[PythonExecutor] Input keys: {list(inputs.keys())}")
        
        # Prepare inputs
        prepared_inputs = self.prepare_inputs(inputs)
        logger.debug(f"[PythonExecutor] Prepared inputs: {list(prepared_inputs.keys())}")
        
        # Create a module from the inline code
        module_code = code
        
        # If the code doesn't define the function, wrap it
        if f"def {function_name}" not in code:
            logger.debug(f"[PythonExecutor] Code doesn't define {function_name}, wrapping it")
            # Create a function that unpacks inputs as local variables
            input_vars = '\n'.join(f'    {k} = inputs.get("{k}")' for k in prepared_inputs)
            indented_code = '\n'.join('    ' + line for line in code.split('\n') if line.strip())
            module_code = f"""def {function_name}(inputs):
{input_vars}
{indented_code}
    return locals().get('result', None)"""
        
        # Create a temporary file to execute the code
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as temp_file:
            temp_file.write(module_code)
            temp_file_path = temp_file.name
        
        try:
            # Execute using the file-based method
            logger.debug(f"[PythonExecutor] Executing wrapped code from temp file: {temp_file_path}")
            result = await self.execute_file(Path(temp_file_path), inputs, timeout, function_name)
            logger.debug(f"[PythonExecutor] Execution result type: {type(result)}, value: {result if not isinstance(result, dict) else f'dict with keys: {list(result.keys())}'}")
            return result
        finally:
            # Clean up temporary file
            if os.path.exists(temp_file_path):
                os.unlink(temp_file_path)