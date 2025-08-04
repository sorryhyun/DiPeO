import logging
import os
from pathlib import Path

from pydantic import BaseModel

from dipeo.application.execution.execution_request import ExecutionRequest
from dipeo.application.execution.handler_base import TypedNodeHandler
from dipeo.application.execution.handler_factory import register_handler
from dipeo.application.utils.template import TemplateProcessor
from dipeo.core.execution.node_output import DataOutput, ErrorOutput, NodeOutputProtocol, TextOutput
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
    
    def __init__(self, filesystem_adapter: FileSystemPort | None = None):
        self._processor = TemplateProcessor()
        self.filesystem_adapter = filesystem_adapter
        
        # Initialize language executors
        self._executors: dict[str, CodeExecutor] = {
            "python": PythonExecutor(),
            "typescript": TypeScriptExecutor(),
            "bash": BashExecutor(),
            "shell": BashExecutor()  # Shell uses same executor as bash
        }

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

    def validate(self, request: ExecutionRequest[CodeJobNode]) -> str | None:
        """Validate the code job configuration."""
        node = request.node
        
        # Check if either filePath or code is provided
        if not node.filePath and not node.code:
            return "Either filePath or code must be provided"
        
        if node.filePath and node.code:
            return "Cannot provide both filePath and code. Use one or the other."
        
        # Validate language is supported
        supported_languages = list(self._executors.keys())
        language = node.language.value if hasattr(node.language, 'value') else node.language
        if language not in supported_languages:
            return f"Unsupported language: {language}. Supported: {', '.join(supported_languages)}"
        
        # If using file path, validate file exists
        if node.filePath:
            file_path = Path(node.filePath)
            if not file_path.is_absolute():
                # Try relative to project root
                base_dir = os.getenv('DIPEO_BASE_DIR', os.getcwd())
                file_path = Path(base_dir) / node.filePath
            
            # Note: We can't use filesystem_adapter in validate() since services aren't available yet
            # The actual file existence check will happen in execute_request()
            # For now, we'll use basic path validation
            if not file_path.exists():
                return f"File not found: {node.filePath}"
            
            if not file_path.is_file():
                return f"Path is not a file: {node.filePath}"
        
        return None
    
    async def execute_request(self, request: ExecutionRequest[CodeJobNode]) -> NodeOutputProtocol:
        """Execute the code job."""
        node = request.node
        inputs = request.inputs

        language = node.language.value if hasattr(node.language, 'value') else node.language
        timeout = node.timeout or 30  # Default 30 seconds
        function_name = node.functionName or "main"  # Default to 'main'

        # Store execution metadata
        request.add_metadata("language", language)
        request.add_metadata("timeout", timeout)
        request.add_metadata("functionName", function_name)
        
        # Get the appropriate executor
        executor = self._executors.get(language)
        if not executor:
            return ErrorOutput(
                value=f"No executor found for language: {language}",
                node_id=node.id,
                error_type="UnsupportedLanguageError"
            )
        
        try:
            if node.code:
                # Handle inline code execution
                request.add_metadata("inline_code", True)
                result = await executor.execute_inline(node.code, inputs, timeout, function_name)
            else:
                # Handle file-based execution
                request.add_metadata("filePath", node.filePath)
                
                # Resolve file path
                file_path = Path(node.filePath)
                if not file_path.is_absolute():
                    base_dir = os.getenv('DIPEO_BASE_DIR', os.getcwd())
                    file_path = Path(base_dir) / node.filePath
                
                result = await executor.execute_file(file_path, inputs, timeout, function_name)
        
        except TimeoutError:
            return ErrorOutput(
                value=f"Code execution timed out after {timeout} seconds",
                node_id=node.id,
                error_type="TimeoutError",
                metadata={"language": language}
            )
        except Exception as e:
            logger.error(f"Code execution failed: {e}")
            return ErrorOutput(
                value=str(e),
                node_id=node.id,
                error_type=type(e).__name__,
                metadata={"language": language}
            )

        # Return appropriate output type based on result
        if isinstance(result, dict):
            # For dict results, return DataOutput so object content type works
            # logger.debug(f"[CodeJobNode {node.id}] Returning dict with keys: {list(result.keys())}")
            return DataOutput(
                value=result,
                node_id=node.id,
                metadata={"language": language, "success": True}
            )
        else:
            # For non-dict results, convert to string
            output = str(result)
            # logger.debug(f"[CodeJobNode {node.id}] Returning {len(output)} chars")
            return TextOutput(
                value=output,
                node_id=node.id,
                metadata={"language": language, "success": True}
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
    ) -> NodeOutputProtocol | None:
        """Handle execution errors with better error messages."""
        language = request.metadata.get("language", "unknown")
        
        # Create error output with language information
        return ErrorOutput(
            value=f"Code execution failed: {error!s}",
            node_id=request.node.id,
            error_type=type(error).__name__,
            metadata={"language": language}
        )