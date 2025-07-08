"""Job node handler - executes Python, JavaScript, or Bash code."""

import asyncio
import json
import os
import sys
from io import StringIO
from typing import Any

from dipeo.application import BaseNodeHandler, register_handler
from dipeo.domain.services.ports.execution_context import ExecutionContextPort
from dipeo.application.utils import create_node_output
from dipeo.models import JobNodeData, NodeOutput
from pydantic import BaseModel


@register_handler
class JobNodeHandler(BaseNodeHandler):
    """Handler for job nodes - executes code in various languages."""

    @property
    def node_type(self) -> str:
        return "job"

    @property
    def schema(self) -> type[BaseModel]:
        return JobNodeData

    @property
    def description(self) -> str:
        return "Executes Python, JavaScript, or Bash code"

    async def execute(
        self,
        props: JobNodeData,
        context: ExecutionContextPort,
        inputs: dict[str, Any],
        services: dict[str, Any],
    ) -> NodeOutput:
        """Execute job node with code."""
        code_type = props.code_type
        code = props.code

        if not code:
            return create_node_output(
                {"default": ""}, 
                {"error": "No code provided"},
                node_id=context.current_node_id,
                executed_nodes=context.executed_nodes
            )

        try:
            if code_type == "python":
                result = await self._execute_python(code, inputs)
            elif code_type == "javascript":
                result = await self._execute_javascript(code, inputs)
            elif code_type == "bash":
                result = await self._execute_bash(code, inputs)
            else:
                return create_node_output(
                    {"default": ""}, 
                    {"error": f"Unsupported code type: {code_type}"},
                    node_id=context.current_node_id,
                    executed_nodes=context.executed_nodes
                )

            # Convert result to string if needed
            if isinstance(result, dict):
                output = json.dumps(result)
            else:
                output = str(result)

            return create_node_output(
                {"default": output},
                {"code_type": code_type, "success": True},
                node_id=context.current_node_id,
                executed_nodes=context.executed_nodes
            )

        except Exception as e:
            return create_node_output(
                {"default": ""}, 
                {"error": str(e), "code_type": code_type, "success": False},
                node_id=context.current_node_id,
                executed_nodes=context.executed_nodes
            )

    async def _execute_python(self, code: str, inputs: dict[str, Any]) -> Any:
        """Execute Python code safely."""
        # Create a restricted namespace with inputs
        namespace = {
            "input_data": inputs.get("default", "") if inputs else "",
            "inputs": inputs,
            "json": json,
            "__builtins__": {
                "len": len,
                "str": str,
                "int": int,
                "float": float,
                "bool": bool,
                "list": list,
                "dict": dict,
                "sum": sum,
                "min": min,
                "max": max,
                "print": print,
                "range": range,
                "enumerate": enumerate,
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

    async def _execute_javascript(self, code: str, inputs: dict[str, Any]) -> Any:
        """Execute JavaScript code using Node.js."""
        # Prepare the code with inputs
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
        
        stdout, stderr = await proc.communicate()
        
        if proc.returncode != 0:
            raise Exception(f"JavaScript execution failed: {stderr.decode()}")
        
        return stdout.decode().strip()

    async def _execute_bash(self, code: str, inputs: dict[str, Any]) -> Any:
        """Execute Bash code."""
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
        
        stdout, stderr = await proc.communicate()
        
        if proc.returncode != 0:
            raise Exception(f"Bash execution failed: {stderr.decode()}")
        
        return stdout.decode().strip()