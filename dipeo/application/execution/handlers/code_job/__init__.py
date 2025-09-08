import logging
import os
from pathlib import Path
from typing import Any

from pydantic import BaseModel

from dipeo.application.execution.execution_request import ExecutionRequest
from dipeo.application.execution.handler_base import TypedNodeHandler
from dipeo.application.execution.handler_factory import register_handler
from dipeo.diagram_generated.unified_nodes.code_job_node import CodeJobNode, NodeType
from dipeo.domain.base.storage_port import FileSystemPort
from dipeo.domain.diagram.ports import TemplateProcessorPort
from dipeo.domain.execution.envelope import Envelope, EnvelopeFactory

from .executors import (
    BashExecutor,
    CodeExecutor,
    PythonExecutor,
    TypeScriptExecutor,
)

logger = logging.getLogger(__name__)


@register_handler
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

        # Instance vars for current execution (pre_execute -> execute_with_envelopes)
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
        return CodeJobNode

    @property
    def requires_services(self) -> list[str]:
        return ["template", "filesystem_adapter"]

    @property
    def description(self) -> str:
        return "Executes Python, TypeScript, or Bash code from files or inline with enhanced capabilities"

    async def pre_execute(self, request: ExecutionRequest[CodeJobNode]) -> Envelope | None:
        """Runtime validation and setup - prepares execution environment."""
        node = request.node

        # 1. Extract configuration with defaults
        language = node.language.value if hasattr(node.language, "value") else node.language
        timeout = node.timeout or 30
        function_name = node.function_name or "main"

        # 2. Runtime validation: Check executor availability
        executor = self._executors.get(language)
        if not executor:
            supported = ", ".join(self._executors.keys())
            return EnvelopeFactory.create(
                body=f"Unsupported language: {language}. Supported: {supported}",
                produced_by=node.id,
                trace_id=request.execution_id or "",
                error="ValueError",
            )

        # 3. Runtime validation: Resolve and check file path if needed
        file_path = None
        if node.file_path:
            file_path = Path(node.file_path)
            if not file_path.is_absolute():
                base_dir = os.getenv("DIPEO_BASE_DIR", os.getcwd())
                file_path = Path(base_dir) / node.file_path

            # Check file exists at runtime
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

        # Check that exactly one of file_path or code is provided
        if not node.file_path and not node.code:
            return "Either file_path or code must be provided"

        if node.file_path and node.code:
            return "Cannot provide both file_path and code. Use one or the other."

        # Note: Language validation moved to pre_execute since it depends on runtime executors
        # File existence check also moved to pre_execute since it's a runtime concern

        return None

    async def prepare_inputs(
        self, request: ExecutionRequest[CodeJobNode], inputs: dict[str, Envelope]
    ) -> dict[str, Any]:
        """Prepare execution context from envelopes.

        Phase 5: Now consumes tokens from incoming edges when available.
        """
        node = request.node

        # Phase 5: Consume tokens from incoming edges or fall back to regular inputs
        envelope_inputs = self.consume_token_inputs(request, inputs)

        # Prepare execution context from envelopes
        exec_context = {}

        # Add all inputs to context
        for key, envelope in envelope_inputs.items():
            # Convert envelope to appropriate Python type
            if envelope.content_type == "raw_text":
                exec_context[key] = envelope.as_text()
            elif envelope.content_type == "object":
                value = envelope.as_json()
                # SEAC: Direct pass-through - no shape mutation
                exec_context[key] = value
            elif envelope.content_type == "binary":
                exec_context[key] = envelope.as_bytes()
            else:
                # Default to raw body
                exec_context[key] = envelope.body

        # Add standard variables
        exec_context["inputs"] = exec_context.copy()
        exec_context["node_id"] = node.id

        # Expose global variables from context to user code
        if hasattr(request.context, "get_variables"):
            exec_context["globals"] = request.context.get_variables()

        return exec_context

    async def run(self, inputs: dict[str, Any], request: ExecutionRequest[CodeJobNode]) -> Any:
        """Execute code with prepared context."""
        import logging
        import time

        node = request.node
        # Ensure exec_context is always a dictionary
        exec_context = inputs if isinstance(inputs, dict) else {}

        # Use pre-validated data from instance variables (set in pre_execute)
        timeout = self._current_timeout
        function_name = self._current_function_name
        executor = self._current_executor

        # Track execution time
        start_time = time.time()

        if node.code:
            request.add_metadata("inline_code", True)
            result = await executor.execute_inline(node.code, exec_context, timeout, function_name)
        else:
            # Use pre-resolved file path from instance variable
            file_path = self._current_file_path
            request.add_metadata("filePath", str(file_path))
            result = await executor.execute_file(file_path, exec_context, timeout, function_name)

        # Store execution metadata for building representations
        self._execution_time = time.time() - start_time
        self._execution_meta = {
            "execution_time": self._execution_time,
            "exit_code": 0 if result is not None else 1,
            "stdout": getattr(executor, "last_stdout", ""),
            "stderr": getattr(executor, "last_stderr", ""),
        }

        return result

    def _build_node_output(
        self, result: Any, request: ExecutionRequest[CodeJobNode]
    ) -> dict[str, Any]:
        """Build multi-representation output for code execution."""
        node = request.node
        execution_meta = getattr(self, "_execution_meta", {})

        # Build representations
        representations = {
            "text": str(result) if result is not None else "",
            "object": result if isinstance(result, dict | list) else None,
            "stdout": execution_meta.get("stdout", ""),
            "stderr": execution_meta.get("stderr", ""),
            "return_value": result,
            "execution_info": {
                "language": self._current_language,
                "execution_time": execution_meta.get("execution_time", 0),
                "exit_code": execution_meta.get("exit_code", 0),
                "function_name": self._current_function_name,
                "timeout": self._current_timeout,
            },
        }

        # Add code/file info
        if node.code:
            representations["code_info"] = {
                "type": "inline",
                "code_hash": hash(node.code),
                "lines": len(node.code.splitlines()),
            }
        else:
            representations["code_info"] = {
                "type": "file",
                "file_path": str(self._current_file_path),
                "file_hash": hash(str(self._current_file_path)),
            }

        # Determine primary body for backward compatibility
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
                "execution_time": self._execution_time if hasattr(self, "_execution_time") else 0,
                "code_hash": hash(node.code) if node.code else hash(str(self._current_file_path)),
                "language": self._current_language,
                "result_type": type(result).__name__,
            },
        }

    def serialize_output(self, result: Any, request: ExecutionRequest[CodeJobNode]) -> Envelope:
        """Serialize code execution result to multi-representation envelope."""
        node = request.node
        trace_id = request.execution_id or ""

        # Build multi-representation output
        output = self._build_node_output(result, request)

        # Use natural data output with auto-detection
        primary = output["primary"]
        output_envelope = EnvelopeFactory.create(
            body=primary,  # Let auto-detection handle the content type
            produced_by=node.id,
            trace_id=trace_id,
        )

        # Representations no longer needed - removed deprecated with_representations() call

        # Add metadata
        if "meta" in output:
            output_envelope = output_envelope.with_meta(**output["meta"])

        return output_envelope

    def post_execute(self, request: ExecutionRequest[CodeJobNode], output: Envelope) -> Envelope:
        """Post-execution hook for logging and token emission.

        Phase 5: Now emits output as tokens to trigger downstream nodes.
        """
        # Use instance variable for language
        if request.metadata and request.metadata.get("debug"):
            language = self._current_language
            # Check if output is an error by checking has_error method
            is_error = hasattr(output, "has_error") and output.has_error()
            print(f"[CodeJobNode] Executed {language} code - Success: {not is_error}")
            if is_error and hasattr(output, "value"):
                print(f"[CodeJobNode] Error: {output.value}")

        # Phase 5: Emit output as tokens to trigger downstream nodes
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
