"""Code job node handler - executes Python, JavaScript, or Bash code."""

import asyncio
import json
import os
import sys
from io import StringIO
from typing import Any

from dipeo_core import BaseNodeHandler, RuntimeContext, register_handler
from dipeo_core.execution import create_node_output
from dipeo_domain.models import CodeJobNodeData, NodeOutput
from pydantic import BaseModel

from ..utils.template import substitute_template


@register_handler
class CodeJobNodeHandler(BaseNodeHandler):
    """Handler for code_job nodes - executes code in various languages."""

    @property
    def node_type(self) -> str:
        return "code_job"

    @property
    def schema(self) -> type[BaseModel]:
        return CodeJobNodeData

    @property
    def description(self) -> str:
        return "Executes Python, JavaScript, or Bash code with enhanced capabilities"

    async def execute(
        self,
        props: CodeJobNodeData,
        context: RuntimeContext,
        inputs: dict[str, Any],
        services: dict[str, Any],
    ) -> NodeOutput:
        """Execute code_job node with code."""
        language = props.language
        code = props.code
        timeout = props.timeout or 30  # Default 30 seconds

        if not code:
            return create_node_output(
                {"default": ""}, 
                {"error": "No code provided"}
            )

        try:
            if language == "python":
                result = await self._execute_python(code, inputs, timeout)
            elif language == "javascript":
                result = await self._execute_javascript(code, inputs, timeout)
            elif language == "bash":
                result = await self._execute_bash(code, inputs, timeout)
            else:
                return create_node_output(
                    {"default": ""}, 
                    {"error": f"Unsupported language: {language}"}
                )

            # Convert result to string if needed
            if isinstance(result, dict):
                output = json.dumps(result)
            else:
                output = str(result)

            return create_node_output(
                {"default": output},
                {"language": language, "success": True}
            )

        except asyncio.TimeoutError:
            return create_node_output(
                {"default": ""}, 
                {"error": f"Code execution timed out after {timeout} seconds", "language": language, "success": False}
            )
        except Exception as e:
            return create_node_output(
                {"default": ""}, 
                {"error": str(e), "language": language, "success": False}
            )

    async def _execute_python(self, code: str, inputs: dict[str, Any], timeout: int) -> Any:
        """Execute Python code safely with timeout."""
        # Replace template variables using the standard utility
        if "{{" in code and inputs:
            # Create a namespace with all inputs
            template_vars = {}
            for key, value in inputs.items():
                # If value is a JSON string, parse it
                if isinstance(value, str) and value.strip().startswith('{'):
                    try:
                        template_vars[key] = json.loads(value)
                    except json.JSONDecodeError:
                        template_vars[key] = value
                else:
                    template_vars[key] = value
            
            # Substitute all template variables
            code, missing_keys, used_keys = substitute_template(code, template_vars)
            
            if missing_keys:
                raise ValueError(f"Missing template variables: {', '.join(missing_keys)}")
        
        # Create a more complete namespace with inputs
        namespace = {
            "input_data": inputs.get("default", "") if inputs else "",
            "inputs": inputs,
            "json": json,
            "math": __import__("math"),
            "random": __import__("random"),
            "datetime": __import__("datetime"),
            "__builtins__": {
                # Basic types
                "len": len,
                "str": str,
                "int": int,
                "float": float,
                "bool": bool,
                "list": list,
                "dict": dict,
                "tuple": tuple,
                "set": set,
                # Functions
                "sum": sum,
                "min": min,
                "max": max,
                "abs": abs,
                "round": round,
                "sorted": sorted,
                "reversed": reversed,
                "print": print,
                "range": range,
                "enumerate": enumerate,
                "zip": zip,
                "map": map,
                "filter": filter,
                "any": any,
                "all": all,
                "isinstance": isinstance,
                "type": type,
                # Exceptions
                "Exception": Exception,
                "ValueError": ValueError,
                "TypeError": TypeError,
                "KeyError": KeyError,
                "IndexError": IndexError,
                "AttributeError": AttributeError,
                "NameError": NameError,
                "ZeroDivisionError": ZeroDivisionError,
                "ImportError": ImportError,
                "RuntimeError": RuntimeError,
                # Import
                "__import__": __import__,
            }
        }

        # Capture stdout
        old_stdout = sys.stdout
        sys.stdout = StringIO()

        try:
            # Check if code has a return statement
            if "return " in code:
                # Wrap the code in a function to handle return statements
                # Properly indent the code
                lines = code.split('\n')
                indented_lines = ['    ' + line for line in lines]
                func_code = "def _execute():\n" + '\n'.join(indented_lines) + "\n\n_result = _execute()"
                
                # Execute the wrapped code
                exec(func_code, namespace)
                result = namespace["_result"]
            else:
                # Execute code directly and look for 'result' variable
                exec(code, namespace)
                
                # Check if a 'result' variable was defined
                if "result" in namespace:
                    result = namespace["result"]
                else:
                    # Get the printed output
                    printed_output = sys.stdout.getvalue()
                    result = printed_output.strip() if printed_output else "Code executed successfully"
            
            return result
        finally:
            sys.stdout = old_stdout

    async def _execute_javascript(self, code: str, inputs: dict[str, Any], timeout: int) -> Any:
        """Execute JavaScript code using Node.js with timeout."""
        # Replace template variables
        if "{{" in code and inputs:
            template_vars = {}
            for key, value in inputs.items():
                if isinstance(value, str) and value.strip().startswith('{'):
                    try:
                        template_vars[key] = json.loads(value)
                    except json.JSONDecodeError:
                        template_vars[key] = value
                else:
                    template_vars[key] = value
            
            code, missing_keys, used_keys = substitute_template(code, template_vars)
            if missing_keys:
                raise ValueError(f"Missing template variables: {', '.join(missing_keys)}")
        
        # Prepare the code with all inputs available as variables
        # Check if code has a return statement
        if "return " in code:
            # Wrap in a function and capture the return value
            js_code = f"""
            const inputs = {json.dumps(inputs) if inputs else '{}'};
            const input_data = {json.dumps(inputs.get('default', '') if inputs else '')};
            
            const __result = (function() {{
                {code}
            }})();
            
            if (__result !== undefined) {{
                console.log(JSON.stringify(__result));
            }}
            """
        else:
            # Execute code directly
            js_code = f"""
            const inputs = {json.dumps(inputs) if inputs else '{}'};
            const input_data = {json.dumps(inputs.get('default', '') if inputs else '')};
            
            {code}
            """
        
        # Run with node
        proc = await asyncio.create_subprocess_exec(
            "node", "-e", js_code,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        try:
            stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=timeout)
        except asyncio.TimeoutError:
            proc.kill()
            await proc.wait()
            raise
        
        if proc.returncode != 0:
            raise Exception(f"JavaScript execution failed: {stderr.decode()}")
        
        return stdout.decode().strip()

    async def _execute_bash(self, code: str, inputs: dict[str, Any], timeout: int) -> Any:
        """Execute Bash code with timeout."""
        # Replace template variables
        if "{{" in code and inputs:
            template_vars = {}
            for key, value in inputs.items():
                template_vars[key] = str(value)
            
            code, missing_keys, used_keys = substitute_template(code, template_vars)
            if missing_keys:
                raise ValueError(f"Missing template variables: {', '.join(missing_keys)}")
        
        # Set up environment variables from inputs
        env = dict(os.environ)
        if inputs:
            for key, value in inputs.items():
                env[f"INPUT_{key.upper()}"] = str(value)
        
        # Run the bash code
        proc = await asyncio.create_subprocess_shell(
            code,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            env=env
        )
        
        try:
            stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=timeout)
        except asyncio.TimeoutError:
            proc.kill()
            await proc.wait()
            raise
        
        if proc.returncode != 0:
            raise Exception(f"Bash execution failed: {stderr.decode()}")
        
        return stdout.decode().strip()