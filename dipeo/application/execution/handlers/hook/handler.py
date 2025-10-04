import asyncio
import json
import subprocess
from typing import TYPE_CHECKING, Any

from pydantic import BaseModel

from dipeo.application.execution.engine.request import ExecutionRequest
from dipeo.application.execution.handlers.core.base import TypedNodeHandler
from dipeo.application.execution.handlers.core.decorators import Optional, requires_services
from dipeo.application.execution.handlers.core.factory import register_handler
from dipeo.application.execution.handlers.hook.file_executor import execute_file_hook
from dipeo.application.execution.handlers.hook.shell_executor import execute_shell_hook
from dipeo.application.execution.handlers.hook.webhook_executor import execute_webhook_hook
from dipeo.application.execution.handlers.utils import (
    create_error_body,
    serialize_data,
    validate_config_field,
)
from dipeo.application.registry.keys import FILESYSTEM_ADAPTER
from dipeo.diagram_generated.enums import HookType
from dipeo.diagram_generated.unified_nodes.hook_node import HookNode, NodeType
from dipeo.domain.base.exceptions import InvalidDiagramError, NodeExecutionError
from dipeo.domain.execution.envelope import Envelope, EnvelopeFactory

if TYPE_CHECKING:
    pass


@register_handler
@requires_services(filesystem_adapter=(FILESYSTEM_ADAPTER, Optional))
class HookNodeHandler(TypedNodeHandler[HookNode]):
    """Execute external hooks (shell commands, webhooks, Python scripts, or file operations)."""

    NODE_TYPE = NodeType.HOOK

    def __init__(self):
        super().__init__()

    @property
    def node_class(self) -> type[HookNode]:
        return HookNode

    @property
    def node_type(self) -> str:
        return NodeType.HOOK.value

    @property
    def schema(self) -> type[BaseModel]:
        return HookNode

    @property
    def description(self) -> str:
        return (
            "Execute external hooks (shell commands, webhooks, Python scripts, or file operations)"
        )

    async def pre_execute(self, request: ExecutionRequest[HookNode]) -> Envelope | None:
        node = request.node

        valid_hook_types = {HookType.SHELL, HookType.WEBHOOK, HookType.PYTHON, HookType.FILE}
        if node.hook_type not in valid_hook_types:
            return EnvelopeFactory.create(
                body=create_error_body(f"Unknown hook type: {node.hook_type}"),
                produced_by=str(node.id),
            )

        config = node.config or {}

        if node.hook_type == HookType.SHELL:
            error = validate_config_field(config, "command", "shell")
            if error:
                return EnvelopeFactory.create(
                    body=create_error_body(error),
                    produced_by=str(node.id),
                )
        elif node.hook_type == HookType.WEBHOOK:
            error = validate_config_field(config, "url", "webhook")
            if error:
                return EnvelopeFactory.create(
                    body=create_error_body(error),
                    produced_by=str(node.id),
                )
        elif node.hook_type == HookType.PYTHON:
            error = validate_config_field(config, "script", "python")
            if error:
                return EnvelopeFactory.create(
                    body=create_error_body(error),
                    produced_by=str(node.id),
                )
        elif node.hook_type == HookType.FILE:
            error = validate_config_field(config, "file_path", "file")
            if error:
                return EnvelopeFactory.create(
                    body=create_error_body(error),
                    produced_by=str(node.id),
                )
            filesystem_adapter = request.get_optional_service(FILESYSTEM_ADAPTER)

            if not filesystem_adapter:
                return EnvelopeFactory.create(
                    body=create_error_body("Filesystem adapter is required for file hooks"),
                    produced_by=str(node.id),
                )
            request.set_handler_state("filesystem_adapter", filesystem_adapter)

        request.set_handler_state("timeout", node.timeout or 30)

        return None

    async def prepare_inputs(
        self, request: ExecutionRequest[HookNode], inputs: dict[str, Envelope]
    ) -> dict[str, Any]:
        envelope_inputs = self.get_effective_inputs(request, inputs)

        prepared_inputs = {}
        for key, envelope in envelope_inputs.items():
            try:
                prepared_inputs[key] = envelope.as_json()
            except ValueError:
                prepared_inputs[key] = envelope.as_text()

        return prepared_inputs

    async def run(self, inputs: dict[str, Any], request: ExecutionRequest[HookNode]) -> Any:
        node = request.node

        try:
            result = await self._execute_hook(node, inputs, request)
            return result
        finally:
            if hasattr(self, "_temp_filesystem_adapter"):
                delattr(self, "_temp_filesystem_adapter")

    def serialize_output(self, result: Any, request: ExecutionRequest[HookNode]) -> Envelope:
        node = request.node
        trace_id = request.execution_id or ""
        hook_type = str(node.hook_type)

        success = True
        exit_code = 0
        if isinstance(result, dict):
            if "status" in result:
                success = result["status"] != "timeout" and result["status"] != "error"
            if "returncode" in result:
                exit_code = result["returncode"]

        output_envelope = EnvelopeFactory.create(
            body=result, produced_by=node.id, trace_id=trace_id
        )

        meta = {"hook_type": hook_type, "success": success, "exit_code": exit_code}

        if node.hook_type == HookType.SHELL and isinstance(result, dict):
            meta["stdout"] = result.get("stdout", result.get("output", ""))
            meta["stderr"] = result.get("stderr", "")
        elif node.hook_type == HookType.WEBHOOK and isinstance(result, dict):
            meta["provider"] = result.get("provider")
        elif node.hook_type == HookType.FILE and isinstance(result, dict):
            meta["file_path"] = result.get("file", "")

        output_envelope = output_envelope.with_meta(**meta)

        return output_envelope

    def post_execute(self, request: ExecutionRequest[HookNode], output: Envelope) -> Envelope:
        self.emit_token_outputs(request, output)

        return output

    async def _execute_hook(
        self, node: HookNode, inputs: dict[str, Any], request: ExecutionRequest[HookNode]
    ) -> Any:
        if node.hook_type == HookType.SHELL:
            return await execute_shell_hook(node, inputs, request)
        elif node.hook_type == HookType.WEBHOOK:
            return await execute_webhook_hook(node, inputs, request)
        elif node.hook_type == HookType.PYTHON:
            return await self._execute_python_hook(node, inputs, request)
        elif node.hook_type == HookType.FILE:
            return await execute_file_hook(node, inputs, request)
        else:
            raise InvalidDiagramError(f"Unknown hook type: {node.hook_type}")

    async def _execute_python_hook(
        self, node: HookNode, inputs: dict[str, Any], request: ExecutionRequest[HookNode]
    ) -> Any:
        """Execute Python hook - run a Python script with inputs.

        Python hooks are kept in the main handler as they're simpler and
        don't require extensive external dependencies.
        """
        config = node.config
        script = config.get("script")

        function_name = config.get("function_name", "hook")

        code = f"""
import json
import sys

{script}

# Execute the hook function
result = {function_name}({json.dumps(inputs)})
print(json.dumps(result))
"""

        try:
            process = await asyncio.create_subprocess_exec(
                "python", "-c", code, stdout=subprocess.PIPE, stderr=subprocess.PIPE
            )

            timeout = request.get_handler_state("timeout", 30)
            stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=timeout)

            if process.returncode != 0:
                raise NodeExecutionError(
                    f"Python script failed with code {process.returncode}: {stderr.decode()}"
                )

            return json.loads(stdout.decode().strip())

        except TimeoutError:
            raise NodeExecutionError(f"Python script timed out after {timeout} seconds") from None
        except json.JSONDecodeError as e:
            raise NodeExecutionError(f"Failed to parse Python script output: {e!s}") from e
