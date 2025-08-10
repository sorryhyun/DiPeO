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
    
    def __init__(self, filesystem_adapter: FileSystemPort | None = None):
        self._processor = TemplateProcessor()
        self.filesystem_adapter = filesystem_adapter
        
        self._executors: dict[str, CodeExecutor] = {
            "python": PythonExecutor(),
            "typescript": TypeScriptExecutor(),
            "bash": BashExecutor(),
            "shell": BashExecutor()
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
        node = request.node
        
        if not node.filePath and not node.code:
            return "Either filePath or code must be provided"
        
        if node.filePath and node.code:
            return "Cannot provide both filePath and code. Use one or the other."
        
        supported_languages = list(self._executors.keys())
        language = node.language.value if hasattr(node.language, 'value') else node.language
        if language not in supported_languages:
            return f"Unsupported language: {language}. Supported: {', '.join(supported_languages)}"
        
        if node.filePath:
            file_path = Path(node.filePath)
            if not file_path.is_absolute():
                base_dir = os.getenv('DIPEO_BASE_DIR', os.getcwd())
                file_path = Path(base_dir) / node.filePath
            
            if not file_path.exists():
                return f"File not found: {node.filePath}"
            
            if not file_path.is_file():
                return f"Path is not a file: {node.filePath}"
        
        return None
    
    async def execute_request(self, request: ExecutionRequest[CodeJobNode]) -> NodeOutputProtocol:
        node = request.node
        inputs = request.inputs

        language = node.language.value if hasattr(node.language, 'value') else node.language
        timeout = node.timeout or 30
        function_name = node.functionName or "main"

        request.add_metadata("language", language)
        request.add_metadata("timeout", timeout)
        request.add_metadata("functionName", function_name)
        
        executor = self._executors.get(language)
        if not executor:
            return ErrorOutput(
                value=f"No executor found for language: {language}",
                node_id=node.id,
                error_type="UnsupportedLanguageError"
            )
        
        try:
            if node.code:
                request.add_metadata("inline_code", True)
                result = await executor.execute_inline(node.code, inputs, timeout, function_name)
            else:
                request.add_metadata("filePath", node.filePath)
                
                file_path = Path(node.filePath)
                if not file_path.is_absolute():
                    base_dir = os.getenv('DIPEO_BASE_DIR', os.getcwd())
                    file_path = Path(base_dir) / node.filePath
                
                result = await executor.execute_file(file_path, inputs, timeout, function_name)
        
        except TimeoutError:
            # Still use ErrorOutput for errors, but with typed fields
            output = ErrorOutput(
                value=f"Code execution timed out after {timeout} seconds",
                node_id=node.id,
                error_type="TimeoutError"
            )
            output.metadata = json.dumps({"language": language})
            return output
        except Exception as e:
            logger.error(f"Code execution failed: {e}")
            output = ErrorOutput(
                value=str(e),
                node_id=node.id,
                error_type=type(e).__name__
            )
            output.metadata = json.dumps({"language": language})
            return output

        # Use CodeJobOutput for successful executions
        if isinstance(result, dict):
            # For dict results, convert to string representation
            output_str = json.dumps(result, indent=2)
            return CodeJobOutput(
                value=output_str,
                node_id=node.id,
                language=language,
                success=True,
                metadata=json.dumps({"result_type": "dict"})
            )
        else:
            output = str(result)
            return CodeJobOutput(
                value=output,
                node_id=node.id,
                language=language,
                success=True,
                metadata=json.dumps({"result_type": "string"})
            )
    
    def post_execute(
        self,
        request: ExecutionRequest[CodeJobNode],
        output: NodeOutputProtocol
    ) -> NodeOutputProtocol:
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
        language = request.metadata.get("language", "unknown")
        
        return ErrorOutput(
            value=f"Code execution failed: {error!s}",
            node_id=request.node.id,
            error_type=type(error).__name__,
            metadata=json.dumps({"language": language})
        )