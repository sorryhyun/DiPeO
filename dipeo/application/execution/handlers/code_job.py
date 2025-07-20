
import asyncio
import json
import os
import sys
import warnings
import importlib.util
import tempfile
from pathlib import Path
from io import StringIO
from typing import TYPE_CHECKING, Any, Optional

from pydantic import BaseModel

from dipeo.application.execution.handler_base import TypedNodeHandler
from dipeo.application.execution.execution_request import ExecutionRequest
from dipeo.application.execution.handler_factory import register_handler
from dipeo.core.static.generated_nodes import CodeJobNode
from dipeo.core.execution.node_output import TextOutput, ErrorOutput, NodeOutputProtocol, DataOutput
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
        return "Executes Python, TypeScript, or Bash code from files with enhanced capabilities"

    def validate(self, request: ExecutionRequest[CodeJobNode]) -> Optional[str]:
        """Validate the code job configuration."""
        node = request.node
        
        # Validate file path is provided
        if not node.filePath:
            return "No file path provided"
        
        # Validate language is supported
        supported_languages = ["python", "typescript", "bash", "shell"]
        language = node.language.value if hasattr(node.language, 'value') else node.language
        if language not in supported_languages:
            return f"Unsupported language: {language}. Supported: {', '.join(supported_languages)}"
        
        # Validate file exists
        file_path = Path(node.filePath)
        if not file_path.is_absolute():
            # Try relative to project root
            base_dir = os.getenv('DIPEO_BASE_DIR', os.getcwd())
            file_path = Path(base_dir) / node.filePath
        
        if not file_path.exists():
            return f"File not found: {node.filePath}"
        
        if not file_path.is_file():
            return f"Path is not a file: {node.filePath}"
        
        return None
    
    async def execute_request(self, request: ExecutionRequest[CodeJobNode]) -> NodeOutputProtocol:
        """Execute the code job."""
        node = request.node
        context = request.context
        inputs = request.inputs
        # Store execution metadata
        language = node.language.value if hasattr(node.language, 'value') else node.language
        request.add_metadata("language", language)
        request.add_metadata("filePath", node.filePath)
        request.add_metadata("functionName", node.functionName)
        request.add_metadata("timeout", node.timeout)
        
        # Resolve file path
        file_path = Path(node.filePath)
        if not file_path.is_absolute():
            base_dir = os.getenv('DIPEO_BASE_DIR', os.getcwd())
            file_path = Path(base_dir) / node.filePath
        
        timeout = node.timeout or 30  # Default 30 seconds
        function_name = node.functionName or "main"  # Default to 'main'

        try:
            if language == "python":
                result = await self._execute_python(file_path, inputs, timeout, context, function_name)
            elif language == "typescript":
                result = await self._execute_typescript(file_path, inputs, timeout, function_name)
            elif language == "bash" or language == "shell":
                result = await self._execute_bash(file_path, inputs, timeout)
            else:
                return ErrorOutput(
                    value=f"Unsupported language: {language}",
                    node_id=node.id,
                    error_type="UnsupportedLanguageError"
                )

            # Return appropriate output type based on result
            if isinstance(result, dict):
                # For dict results, return DataOutput so object content type works
                return DataOutput(
                    value={"default": result},
                    node_id=node.id,
                    metadata={"language": language, "success": True}
                )
            else:
                # For non-dict results, convert to string
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

    async def _execute_python(self, file_path: Path, inputs: dict[str, Any], timeout: int, context: Optional["ExecutionContext"] = None, function_name: str = "main") -> Any:
        """Execute Python file by loading module and calling specified function."""
        # Prepare inputs dictionary with connection labels as keys
        prepared_inputs = {}
        if inputs:
            for key, value in inputs.items():
                # Try to parse JSON strings
                if isinstance(value, str) and value.strip() and value.strip()[0] in '{[':
                    try:
                        prepared_inputs[key] = json.loads(value)
                    except json.JSONDecodeError:
                        prepared_inputs[key] = value
                else:
                    prepared_inputs[key] = value
        
        # Load the Python module dynamically
        spec = importlib.util.spec_from_file_location("code_module", file_path)
        if spec is None or spec.loader is None:
            raise ImportError(f"Cannot load module from {file_path}")
        
        module = importlib.util.module_from_spec(spec)
        
        # Add the file's directory to sys.path temporarily for imports
        sys_path_added = False
        file_dir = str(file_path.parent)
        if file_dir not in sys.path:
            sys.path.insert(0, file_dir)
            sys_path_added = True
        
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
            if sys_path_added:
                sys.path.remove(file_dir)

    async def _execute_typescript(self, file_path: Path, inputs: dict[str, Any], timeout: int, function_name: str = "main") -> Any:
        """Execute TypeScript file using tsx."""
        # Prepare inputs as JSON to pass as command line argument
        prepared_inputs = {}
        if inputs:
            for key, value in inputs.items():
                # Try to parse JSON strings
                if isinstance(value, str) and value.strip() and value.strip()[0] in '{[':
                    try:
                        prepared_inputs[key] = json.loads(value)
                    except json.JSONDecodeError:
                        prepared_inputs[key] = value
                else:
                    prepared_inputs[key] = value
        
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
            except asyncio.TimeoutError:
                proc.kill()
                await proc.wait()
                raise TimeoutError(f"TypeScript execution timed out after {timeout} seconds")
            
            if proc.returncode != 0:
                # Try to parse error as JSON first
                error_output = stderr.decode().strip() or stdout.decode().strip()
                try:
                    error_data = json.loads(error_output)
                    raise Exception(f"TypeScript execution failed: {error_data.get('error', error_output)}")
                except json.JSONDecodeError:
                    raise Exception(f"TypeScript execution failed: {error_output}")
            
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

    async def _execute_bash(self, file_path: Path, inputs: dict[str, Any], timeout: int) -> Any:
        """Execute Bash script file with inputs as environment variables."""
        # Set up environment variables from inputs
        env = dict(os.environ)
        if inputs:
            # Add a helper variable listing all input keys
            env["INPUT_KEYS"] = " ".join(inputs.keys())
            
            for key, value in inputs.items():
                # Convert values to strings for environment variables
                if isinstance(value, (dict, list)):
                    env[f"INPUT_{key}"] = json.dumps(value)
                else:
                    env[f"INPUT_{key}"] = str(value)
        
        # Make sure the script is executable
        if not os.access(file_path, os.X_OK):
            # Try to make it executable
            os.chmod(file_path, os.stat(file_path).st_mode | 0o111)
        
        # Run the bash script
        proc = await asyncio.create_subprocess_exec(
            str(file_path),
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            env=env,
            cwd=str(file_path.parent)  # Set working directory to script's directory
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