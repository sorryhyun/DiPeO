
import asyncio
import json
import os
import sys
import warnings
from io import StringIO
from typing import TYPE_CHECKING, Any, Optional

from pydantic import BaseModel

from dipeo.application.execution.types import TypedNodeHandler
from dipeo.application.execution.execution_request import ExecutionRequest
from dipeo.application.execution.handler_factory import register_handler
from dipeo.core.static.generated_nodes import CodeJobNode
from dipeo.core.execution.node_output import TextOutput, ErrorOutput, NodeOutputProtocol
from dipeo.models import CodeJobNodeData, NodeType
from dipeo.application.utils.template import TemplateProcessor

if TYPE_CHECKING:
    from dipeo.application.execution.execution_runtime import ExecutionRuntime
    from dipeo.core.dynamic.execution_context import ExecutionContext



@register_handler
class CodeJobNodeHandler(TypedNodeHandler[CodeJobNode]):
    
    def __init__(self, template_service=None):
        if template_service is not None:
            warnings.warn(
                "Passing template_service to CodeJobNodeHandler is deprecated. "
                "It now uses the unified TemplateProcessor internally.",
                DeprecationWarning,
                stacklevel=2
            )
        self._processor = TemplateProcessor()

    @property
    def node_class(self) -> type[CodeJobNode]:
        return CodeJobNode
    
    @property
    def node_type(self) -> str:
        return NodeType.code_job.value

    @property
    def schema(self) -> type[BaseModel]:
        return CodeJobNodeData
    
    
    @property
    def requires_services(self) -> list[str]:
        return ["template"]

    @property
    def description(self) -> str:
        return "Executes Python, JavaScript, or Bash code with enhanced capabilities"

    def validate(self, request: ExecutionRequest[CodeJobNode]) -> Optional[str]:
        """Validate the code job configuration."""
        node = request.node
        
        # Validate code is provided
        if not node.code:
            return "No code provided"
        
        # Validate language is supported
        supported_languages = ["python", "javascript", "bash"]
        language = node.language.value if hasattr(node.language, 'value') else node.language
        if language not in supported_languages:
            return f"Unsupported language: {language}. Supported: {', '.join(supported_languages)}"
        
        return None
    
    async def execute_request(self, request: ExecutionRequest[CodeJobNode]) -> NodeOutputProtocol:
        """Execute the code job."""
        node = request.node
        context = request.context
        inputs = request.inputs
        # Store execution metadata
        language = node.language.value if hasattr(node.language, 'value') else node.language
        request.add_metadata("language", language)
        request.add_metadata("code", node.code)
        request.add_metadata("timeout", node.timeout)
        
        # Direct typed access to node properties
        code = node.code
        timeout = node.timeout or 30  # Default 30 seconds

        try:
            if language == "python":
                result = await self._execute_python(code, inputs, timeout, context)
            elif language == "javascript":
                result = await self._execute_javascript(code, inputs, timeout)
            elif language == "bash":
                result = await self._execute_bash(code, inputs, timeout)
            else:
                return ErrorOutput(
                    value=f"Unsupported language: {language}",
                    node_id=node.id,
                    error_type="UnsupportedLanguageError"
                )

            # Convert result to string if needed
            if isinstance(result, dict):
                output = json.dumps(result)
            else:
                output = str(result)

            return TextOutput(
                value=output,
                node_id=node.id,
                metadata={"language": language, "success": True}
            )

        except TimeoutError:
            return ErrorOutput(
                value=f"Code execution timed out after {timeout} seconds",
                node_id=node.id,
                error_type="TimeoutError",
                metadata={"language": language}
            )
        except Exception as e:
            return ErrorOutput(
                value=str(e),
                node_id=node.id,
                error_type=type(e).__name__,
                metadata={"language": language}
            )
    
    def post_execute(
        self,
        request: ExecutionRequest[CodeJobNode],
        output: NodeOutputProtocol
    ) -> NodeOutputProtocol:
        """Post-execution hook to log code execution details."""
        # Log execution details if in debug mode
        if request.metadata.get("debug"):
            language = request.metadata.get("language")
            success = output.metadata.get("success", False)
            print(f"[CodeJobNode] Executed {language} code - Success: {success}")
            if not success and output.metadata.get("error"):
                print(f"[CodeJobNode] Error: {output.metadata['error']}")
        
        return output
    
    async def on_error(
        self,
        request: ExecutionRequest[CodeJobNode],
        error: Exception
    ) -> Optional[NodeOutputProtocol]:
        """Handle execution errors with better error messages."""
        language = request.metadata.get("language", "unknown")
        
        # Create error output with language information
        return ErrorOutput(
            value=f"Code execution failed: {str(error)}",
            node_id=request.node.id,
            error_type=type(error).__name__,
            metadata={"language": language}
        )

    async def _execute_python(self, code: str, inputs: dict[str, Any], timeout: int, context: Optional["ExecutionContext"] = None) -> Any:
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
            
            # Substitute all template variables using new processor
            result = self._processor.process(code, template_vars, safe=False)
            if result.errors:
                raise ValueError(f"Template errors: {'; '.join(result.errors)}")
            if result.missing_keys:
                raise ValueError(f"Missing template variables: {', '.join(result.missing_keys)}")
            code = result.content
        
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
        
        # Load variables from context if available
        if context:
            # Get all variables from the execution context
            # We'll need to introspect the context to get all variables
            # For now, let's load common variable names
            for var_name in ['a', 'b', 'c', 'x', 'y', 'z', 'result', 'output', 'data']:
                var_value = context.get_variable(var_name)
                if var_value is not None:
                    namespace[var_name] = var_value

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
            
            # Save variables back to context if available
            if context:
                # List of built-in names to exclude
                builtins_to_exclude = {
                    '__builtins__', 'input_data', 'inputs', 'json', 'math', 
                    'random', 'datetime', '_execute', '_result'
                }
                
                # Save user-defined variables back to context
                for name, value in namespace.items():
                    if name not in builtins_to_exclude and not name.startswith('__'):
                        # Only save simple types that can be serialized
                        if isinstance(value, (str, int, float, bool, list, dict, type(None))):
                            context.set_variable(name, value)
            
            return result
        finally:
            sys.stdout = old_stdout

    async def _execute_javascript(self, code: str, inputs: dict[str, Any], timeout: int) -> Any:
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
            
            # Substitute all template variables using new processor
            result = self._processor.process(code, template_vars, safe=False)
            if result.errors:
                raise ValueError(f"Template errors: {'; '.join(result.errors)}")
            if result.missing_keys:
                raise ValueError(f"Missing template variables: {', '.join(result.missing_keys)}")
            code = result.content
        
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
        except TimeoutError:
            proc.kill()
            await proc.wait()
            raise
        
        if proc.returncode != 0:
            raise Exception(f"JavaScript execution failed: {stderr.decode()}")
        
        return stdout.decode().strip()

    async def _execute_bash(self, code: str, inputs: dict[str, Any], timeout: int) -> Any:
        if "{{" in code and inputs:
            template_vars = {}
            for key, value in inputs.items():
                template_vars[key] = str(value)
            
            # Substitute all template variables using new processor
            result = self._processor.process(code, template_vars, safe=False)
            if result.errors:
                raise ValueError(f"Template errors: {'; '.join(result.errors)}")
            if result.missing_keys:
                raise ValueError(f"Missing template variables: {', '.join(result.missing_keys)}")
            code = result.content
        
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
        except TimeoutError:
            proc.kill()
            await proc.wait()
            raise
        
        if proc.returncode != 0:
            raise Exception(f"Bash execution failed: {stderr.decode()}")
        
        return stdout.decode().strip()