import json
import logging
import os
from pathlib import Path

from pydantic import BaseModel

from dipeo.application.execution.execution_request import ExecutionRequest
from dipeo.application.execution.handler_base import TypedNodeHandler
from dipeo.application.execution.handler_factory import register_handler
from dipeo.application.utils.template import TemplateProcessor
from dipeo.core.execution.node_output import DataOutput, ErrorOutput, NodeOutputProtocol, TextOutput, CodeJobOutput
from dipeo.diagram_generated.generated_nodes import CodeJobNode, NodeType
from dipeo.diagram_generated.models.code_job_model import CodeJobNodeData
from dipeo.domain.ports.storage import FileSystemPort

from .executors import (
    BashExecutor,
    CodeExecutor,
    PythonExecutor,
    TypeScriptExecutor,
)

logger = logging.getLogger(__name__)



@register_handler
class CodeJobNodeHandler(TypedNodeHandler[CodeJobNode]):
    """Handler for code execution nodes.
    
    This handler follows the clean separation pattern:
    1. validate() - Static/structural validation (compile-time checks)
    2. pre_execute() - Runtime validation and setup (file existence, service availability)
    3. execute_request() - Core execution logic using validated data from instance variables
    
    Instance variables are used to pass validated data between pre_execute and execute_request,
    avoiding metadata pollution and providing clean, type-safe data flow.
    """
    
    def __init__(self, filesystem_adapter: FileSystemPort | None = None):
        self._processor = TemplateProcessor()
        self.filesystem_adapter = filesystem_adapter
        
        self._executors: dict[str, CodeExecutor] = {
            "python": PythonExecutor(),
            "typescript": TypeScriptExecutor(),
            "bash": BashExecutor(),
            "shell": BashExecutor()
        }
        
        # Instance vars for current execution (pre_execute -> execute_request)
        self._current_language = None
        self._current_timeout = None
        self._current_function_name = None
        self._current_executor = None
        self._current_file_path = None

    @property
    def node_class(self) -> type[CodeJobNode]:
        return CodeJobNode
    
    @property
    def node_type(self) -> str:
        return NodeType.CODE_JOB.value

    @property
    def schema(self) -> type[BaseModel]:
        return CodeJobNodeData
    
    
    @property
    def requires_services(self) -> list[str]:
        return ["template", "filesystem_adapter"]

    @property
    def description(self) -> str:
        return "Executes Python, TypeScript, or Bash code from files or inline with enhanced capabilities"

    async def pre_execute(self, request: ExecutionRequest[CodeJobNode]) -> NodeOutputProtocol | None:
        """Runtime validation and setup - prepares execution environment."""
        node = request.node
        
        # 1. Extract configuration with defaults
        language = node.language.value if hasattr(node.language, 'value') else node.language
        timeout = node.timeout or 30
        function_name = node.functionName or "main"
        
        # 2. Runtime validation: Check executor availability
        executor = self._executors.get(language)
        if not executor:
            supported = ', '.join(self._executors.keys())
            return ErrorOutput(
                value=f"Unsupported language: {language}. Supported: {supported}",
                node_id=node.id,
                error_type="UnsupportedLanguageError"
            )
        
        # 3. Runtime validation: Resolve and check file path if needed
        file_path = None
        if node.filePath:
            file_path = Path(node.filePath)
            if not file_path.is_absolute():
                base_dir = os.getenv('DIPEO_BASE_DIR', os.getcwd())
                file_path = Path(base_dir) / node.filePath
            
            # Check file exists at runtime
            if not file_path.exists():
                return ErrorOutput(
                    value=f"File not found: {node.filePath}",
                    node_id=node.id,
                    error_type="FileNotFoundError"
                )
            
            if not file_path.is_file():
                return ErrorOutput(
                    value=f"Path is not a file: {node.filePath}",
                    node_id=node.id,
                    error_type="ValidationError"
                )
        
        # 4. Store all validated data in instance variables for execute_request
        self._current_language = language
        self._current_timeout = timeout
        self._current_function_name = function_name
        self._current_executor = executor
        self._current_file_path = file_path
        
        return None  # Proceed to execute_request

    def validate(self, request: ExecutionRequest[CodeJobNode]) -> str | None:
        """Static validation - checks that can be done at compile/planning time."""
        node = request.node
        
        # Check that exactly one of filePath or code is provided
        if not node.filePath and not node.code:
            return "Either filePath or code must be provided"
        
        if node.filePath and node.code:
            return "Cannot provide both filePath and code. Use one or the other."
        
        # Note: Language validation moved to pre_execute since it depends on runtime executors
        # File existence check also moved to pre_execute since it's a runtime concern
        
        return None
    
    async def execute_request(self, request: ExecutionRequest[CodeJobNode]) -> NodeOutputProtocol:
        node = request.node
        inputs = request.inputs
        
        # Use pre-validated data from instance variables (set in pre_execute)
        language = self._current_language
        timeout = self._current_timeout
        function_name = self._current_function_name
        executor = self._current_executor
        
        try:
            if node.code:
                request.add_metadata("inline_code", True)
                result = await executor.execute_inline(node.code, inputs, timeout, function_name)
            else:
                # Use pre-resolved file path from instance variable
                file_path = self._current_file_path
                request.add_metadata("filePath", str(file_path))
                result = await executor.execute_file(file_path, inputs, timeout, function_name)
        
        except TimeoutError:
            # Still use ErrorOutput for errors
            return ErrorOutput(
                value=f"Code execution timed out after {timeout} seconds",
                node_id=node.id,
                error_type="TimeoutError",
                metadata="{}"  # Empty metadata
            )
        except Exception as e:
            logger.error(f"Code execution failed: {e}")
            return ErrorOutput(
                value=str(e),
                node_id=node.id,
                error_type=type(e).__name__,
                metadata="{}"  # Empty metadata
            )

        # Use CodeJobOutput for successful executions
        if isinstance(result, dict):
            # For dict results, convert to string representation
            output_str = json.dumps(result, indent=2)
            return CodeJobOutput(
                value=output_str,
                node_id=node.id,
                language=language,
                result_type="dict",  # Use typed field
                metadata="{}"  # Empty metadata
            )
        else:
            output = str(result)
            return CodeJobOutput(
                value=output,
                node_id=node.id,
                language=language,
                result_type="string",  # Use typed field
                metadata="{}"  # Empty metadata
            )
    
    def post_execute(
        self,
        request: ExecutionRequest[CodeJobNode],
        output: NodeOutputProtocol
    ) -> NodeOutputProtocol:
        # Use instance variable for language
        if request.metadata and request.metadata.get("debug"):
            language = self._current_language
            # Check if output is an error
            is_error = isinstance(output, ErrorOutput)
            print(f"[CodeJobNode] Executed {language} code - Success: {not is_error}")
            if is_error:
                print(f"[CodeJobNode] Error: {output.value}")
        
        return output
    
    async def on_error(
        self,
        request: ExecutionRequest[CodeJobNode],
        error: Exception
    ) -> NodeOutputProtocol | None:
        return ErrorOutput(
            value=f"Code execution failed: {error!s}",
            node_id=request.node.id,
            error_type=type(error).__name__,
            metadata="{}"  # Empty metadata
        )