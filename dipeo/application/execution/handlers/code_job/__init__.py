import logging
import os
from pathlib import Path
from typing import Any

from pydantic import BaseModel

from dipeo.application.execution.engine.request import ExecutionRequest
from dipeo.application.execution.handlers.core.base import TypedNodeHandler
from dipeo.application.execution.handlers.core.decorators import requires_services
from dipeo.application.execution.handlers.core.factory import register_handler
from dipeo.config.base_logger import get_module_logger
from dipeo.diagram_generated.unified_nodes.code_job_node import CodeJobNode, NodeType
from dipeo.domain.base.storage_port import FileSystemPort
from dipeo.domain.diagram.ports import TemplateProcessorPort
from dipeo.domain.execution.messaging.envelope import Envelope, EnvelopeFactory

from .executors import (
    BashExecutor,
    CodeExecutor,
    PythonExecutor,
    TypeScriptExecutor,
)

logger = get_module_logger(__name__)


@register_handler
@requires_services()  # No services actually used
class CodeJobNodeHandler(TypedNodeHandler[CodeJobNode]):
    """Handler for code execution nodes with envelope support.

    This handler follows the clean separation pattern:
    1. validate() - Static/structural validation (compile-time checks)
    2. pre_execute() - Runtime validation and setup (file existence, service availability)
    3. execute_with_envelopes() - Core execution logic using envelope-based inputs

    Instance variables are used to pass validated data between pre_execute and execute_with_envelopes,
    avoiding metadata pollution and providing clean, type-safe data flow.
    """

    NODE_TYPE = NodeType.CODE_JOB

    def __init__(self):
        super().__init__()

        self._executors: dict[str, CodeExecutor] = {
            "python": PythonExecutor(),
            "typescript": TypeScriptExecutor(),
            "bash": BashExecutor(),
            "shell": BashExecutor(),
        }

    @property
    def node_class(self) -> type[CodeJobNode]:
        return CodeJobNode

    @property
    def node_type(self) -> str:
        return NodeType.CODE_JOB.value

    @property
    def schema(self) -> type[BaseModel]:
        return CodeJobNode

    @property
    def description(self) -> str:
        return "Executes Python, TypeScript, or Bash code from files or inline with enhanced capabilities"

    async def pre_execute(self, request: ExecutionRequest[CodeJobNode]) -> Envelope | None:
        node = request.node

        language = node.language.value if hasattr(node.language, "value") else node.language
        timeout = node.timeout or 30
        function_name = node.function_name or "main"

        executor = self._executors.get(language)
        if not executor:
            supported = ", ".join(self._executors.keys())
            return EnvelopeFactory.create(
                body=f"Unsupported language: {language}. Supported: {supported}",
                produced_by=node.id,
                trace_id=request.execution_id or "",
                error="ValueError",
            )

        file_path = None
        if node.file_path:
            file_path = Path(node.file_path)
            if not file_path.is_absolute():
                base_dir = os.getenv("DIPEO_BASE_DIR", os.getcwd())
                file_path = Path(base_dir) / node.file_path

            if not file_path.exists():
                return EnvelopeFactory.create(
                    body=f"File not found: {node.file_path}",
                    produced_by=node.id,
                    trace_id=request.execution_id or "",
                    error="FileNotFoundError",
                )

            if not file_path.is_file():
                return EnvelopeFactory.create(
                    body=f"Path is not a file: {node.file_path}",
                    produced_by=node.id,
                    trace_id=request.execution_id or "",
                    error="ValueError",
                )

        request.set_handler_state("language", language)
        request.set_handler_state("timeout", timeout)
        request.set_handler_state("function_name", function_name)
        request.set_handler_state("executor", executor)
        request.set_handler_state("file_path", file_path)

        return None

    def validate(self, request: ExecutionRequest[CodeJobNode]) -> str | None:
        node = request.node

        if not node.file_path and not node.code:
            return "Either file_path or code must be provided"

        if node.file_path and node.code:
            return "Cannot provide both file_path and code. Use one or the other."

        return None

    async def prepare_inputs(
        self, request: ExecutionRequest[CodeJobNode], inputs: dict[str, Envelope]
    ) -> dict[str, Any]:
        node = request.node

        envelope_inputs = self.get_effective_inputs(request, inputs)

        exec_context = {}

        for key, envelope in envelope_inputs.items():
            if envelope.content_type == "raw_text":
                exec_context[key] = envelope.as_text()
            elif envelope.content_type == "object":
                value = envelope.as_json()
                exec_context[key] = value
            elif envelope.content_type == "binary":
                exec_context[key] = envelope.as_bytes()
            else:
                exec_context[key] = envelope.body

        exec_context["inputs"] = exec_context.copy()
        exec_context["node_id"] = node.id

        if hasattr(request.context, "get_variables"):
            exec_context["globals"] = request.context.get_variables()

        return exec_context

    async def run(self, inputs: dict[str, Any], request: ExecutionRequest[CodeJobNode]) -> Any:
        import time

        node = request.node
        exec_context = inputs if isinstance(inputs, dict) else {}

        timeout = request.get_handler_state("timeout")
        function_name = request.get_handler_state("function_name")
        executor = request.get_handler_state("executor")

        start_time = time.time()

        if node.code:
            request.add_metadata("inline_code", True)
            result = await executor.execute_inline(node.code, exec_context, timeout, function_name)
        else:
            file_path = request.get_handler_state("file_path")
            request.add_metadata("filePath", str(file_path))
            result = await executor.execute_file(file_path, exec_context, timeout, function_name)

        execution_time = time.time() - start_time
        execution_meta = {
            "execution_time": execution_time,
            "exit_code": 0 if result is not None else 1,
            "stdout": getattr(executor, "last_stdout", ""),
            "stderr": getattr(executor, "last_stderr", ""),
        }
        request.set_handler_state("execution_time", execution_time)
        request.set_handler_state("execution_meta", execution_meta)

        return result

    def _build_node_output(
        self, result: Any, request: ExecutionRequest[CodeJobNode]
    ) -> dict[str, Any]:
        node = request.node
        execution_meta = request.get_handler_state("execution_meta", {})
        language = request.get_handler_state("language")
        function_name = request.get_handler_state("function_name")
        timeout = request.get_handler_state("timeout")
        file_path = request.get_handler_state("file_path")
        execution_time = request.get_handler_state("execution_time", 0)

        representations = {
            "text": str(result) if result is not None else "",
            "object": result if isinstance(result, dict | list) else None,
            "stdout": execution_meta.get("stdout", ""),
            "stderr": execution_meta.get("stderr", ""),
            "return_value": result,
            "execution_info": {
                "language": language,
                "execution_time": execution_meta.get("execution_time", 0),
                "exit_code": execution_meta.get("exit_code", 0),
                "function_name": function_name,
                "timeout": timeout,
            },
        }

        if node.code:
            representations["code_info"] = {
                "type": "inline",
                "code_hash": hash(node.code),
                "lines": len(node.code.splitlines()),
            }
        else:
            representations["code_info"] = {
                "type": "file",
                "file_path": str(file_path),
                "file_hash": hash(str(file_path)),
            }

        if result is None:
            primary = ""
        elif isinstance(result, str | bytes | dict | list):
            primary = result
        else:
            primary = str(result)

        return {
            "primary": primary,
            "representations": representations,
            "meta": {
                "execution_time": execution_time,
                "code_hash": hash(node.code) if node.code else hash(str(file_path)),
                "language": language,
                "result_type": type(result).__name__,
            },
        }

    def serialize_output(self, result: Any, request: ExecutionRequest[CodeJobNode]) -> Envelope:
        node = request.node
        trace_id = request.execution_id or ""

        output = self._build_node_output(result, request)

        primary = output["primary"]
        output_envelope = EnvelopeFactory.create(
            body=primary,
            produced_by=node.id,
            trace_id=trace_id,
        )

        if "meta" in output:
            output_envelope = output_envelope.with_meta(**output["meta"])

        return output_envelope

    def post_execute(self, request: ExecutionRequest[CodeJobNode], output: Envelope) -> Envelope:
        if request.metadata and request.metadata.get("debug"):
            language = request.get_handler_state("language")
            is_error = hasattr(output, "has_error") and output.has_error()
            print(f"[CodeJobNode] Executed {language} code - Success: {not is_error}")
            if is_error and hasattr(output, "value"):
                print(f"[CodeJobNode] Error: {output.value}")

        self.emit_token_outputs(request, output)

        return output

    async def on_error(
        self, request: ExecutionRequest[CodeJobNode], error: Exception
    ) -> Envelope | None:
        return EnvelopeFactory.create(
            body=str(error),
            produced_by=request.node.id,
            trace_id=request.execution_id or "",
            error=error.__class__.__name__,
        )
