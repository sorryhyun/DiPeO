import asyncio
import json
import os
import subprocess
from pathlib import Path
from typing import TYPE_CHECKING, Any

import aiohttp
from pydantic import BaseModel

from dipeo.application.execution.execution_request import ExecutionRequest
from dipeo.application.execution.handlers.core.base import TypedNodeHandler
from dipeo.application.execution.handlers.core.decorators import Optional, requires_services
from dipeo.application.execution.handlers.core.factory import register_handler
from dipeo.application.execution.handlers.utils import (
    create_error_body,
    serialize_data,
    validate_config_field,
)
from dipeo.application.registry.keys import FILESYSTEM_ADAPTER
from dipeo.diagram_generated.enums import HookType
from dipeo.diagram_generated.unified_nodes.hook_node import HookNode, NodeType
from dipeo.domain.base.exceptions import InvalidDiagramError, NodeExecutionError
from dipeo.domain.events import DomainEvent
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

        # No need to set temp filesystem adapter, use injected service

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

        # Determine success status
        success = True
        exit_code = 0
        if isinstance(result, dict):
            if "status" in result:
                success = result["status"] != "timeout" and result["status"] != "error"
            if "returncode" in result:
                exit_code = result["returncode"]

        # Create envelope with result as body
        output_envelope = EnvelopeFactory.create(
            body=result, produced_by=node.id, trace_id=trace_id
        )

        # Build metadata based on hook type
        meta = {"hook_type": hook_type, "success": success, "exit_code": exit_code}

        # Add hook-specific metadata
        if node.hook_type == HookType.SHELL and isinstance(result, dict):
            meta["stdout"] = result.get("stdout", result.get("output", ""))
            meta["stderr"] = result.get("stderr", "")
        elif node.hook_type == HookType.WEBHOOK and isinstance(result, dict):
            meta["provider"] = result.get("provider")
        elif node.hook_type == HookType.FILE and isinstance(result, dict):
            meta["file_path"] = result.get("file", "")

        # Add metadata to envelope
        output_envelope = output_envelope.with_meta(**meta)

        return output_envelope

    def post_execute(self, request: ExecutionRequest[HookNode], output: Envelope) -> Envelope:
        self.emit_token_outputs(request, output)

        return output

    async def _execute_hook(
        self, node: HookNode, inputs: dict[str, Any], request: ExecutionRequest[HookNode]
    ) -> Any:
        if node.hook_type == HookType.SHELL:
            return await self._execute_shell_hook(node, inputs, request)
        elif node.hook_type == HookType.WEBHOOK:
            return await self._execute_webhook_hook(node, inputs, request)
        elif node.hook_type == HookType.PYTHON:
            return await self._execute_python_hook(node, inputs, request)
        elif node.hook_type == HookType.FILE:
            return await self._execute_file_hook(node, inputs, request)
        else:
            raise InvalidDiagramError(f"Unknown hook type: {node.hook_type}")

    async def _execute_shell_hook(
        self, node: HookNode, inputs: dict[str, Any], request: ExecutionRequest[HookNode]
    ) -> Any:
        config = node.config
        command = config.get("command")

        env = os.environ.copy()
        if config.get("env"):
            env.update(config["env"])

        for key, value in inputs.items():
            env[f"DIPEO_INPUT_{key.upper()}"] = json.dumps(value)

        args = config.get("args", [])
        cmd = [command, *args]

        try:
            process = await asyncio.create_subprocess_exec(
                *cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd=config.get("cwd"), env=env
            )

            timeout = request.get_handler_state("timeout", 30)
            stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=timeout)

            if process.returncode != 0:
                raise NodeExecutionError(
                    f"Shell command failed with code {process.returncode}: {stderr.decode()}"
                )

            output = stdout.decode().strip()
            try:
                return json.loads(output)
            except json.JSONDecodeError:
                return output

        except TimeoutError:
            raise NodeExecutionError(f"Shell command timed out after {timeout} seconds") from None

    async def _execute_webhook_hook(
        self, node: HookNode, inputs: dict[str, Any], request: ExecutionRequest[HookNode]
    ) -> Any:
        """Execute webhook hook - send request or subscribe to events."""
        config = node.config

        if config.get("subscribe_to"):
            return await self._subscribe_to_webhook_events(node, inputs)

        url = config.get("url")

        method = config.get("method", "POST")
        headers = config.get("headers", {})
        headers["Content-Type"] = "application/json"

        payload = {"inputs": inputs, "hook_type": "hook_node", "node_id": node.label}

        timeout_value = request.get_handler_state("timeout", 30)
        timeout = aiohttp.ClientTimeout(total=timeout_value)

        async with aiohttp.ClientSession(timeout=timeout) as session:
            try:
                async with session.request(
                    method=method, url=url, headers=headers, json=payload
                ) as response:
                    response.raise_for_status()
                    return await response.json()
            except aiohttp.ClientError as e:
                raise NodeExecutionError(f"Webhook request failed: {e!s}") from e

    async def _subscribe_to_webhook_events(self, node: HookNode, inputs: dict[str, Any]) -> Any:
        """Subscribe to webhook events from providers."""
        config = node.config
        subscribe_config = config.get("subscribe_to", {})

        provider = subscribe_config.get("provider")
        event_name = subscribe_config.get("event_name")
        timeout = subscribe_config.get("timeout", 60)  # Default 60 second wait
        filter_conditions = subscribe_config.get("filters", {})

        if not provider:
            raise NodeExecutionError(
                "Webhook subscription requires 'provider' in subscribe_to config"
            )

        received_event = None
        event_received = asyncio.Event()

        class WebhookEventConsumer:
            async def handle(self, event: DomainEvent) -> None:
                nonlocal received_event

                event_data = event.payload
                if event_data.get("source") != "webhook":
                    return

                if event_data.get("provider") != provider:
                    return

                if event_name and event_data.get("event_name") != event_name:
                    return

                payload = event_data.get("payload", {})
                for key, expected_value in filter_conditions.items():
                    if payload.get(key) != expected_value:
                        return

                received_event = event_data
                event_received.set()

        try:
            await asyncio.wait_for(event_received.wait(), timeout=timeout)

            if received_event:
                return {
                    "status": "triggered",
                    "provider": provider,
                    "event_name": received_event.get("event_name"),
                    "payload": received_event.get("payload"),
                    "headers": received_event.get("headers", {}),
                }
            else:
                return {
                    "status": "timeout",
                    "provider": provider,
                    "message": f"No matching webhook event received within {timeout} seconds",
                }

        except TimeoutError:
            return {
                "status": "timeout",
                "provider": provider,
                "message": f"Webhook subscription timed out after {timeout} seconds",
            }

    async def _execute_python_hook(
        self, node: HookNode, inputs: dict[str, Any], request: ExecutionRequest[HookNode]
    ) -> Any:
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

    async def _execute_file_hook(
        self, node: HookNode, inputs: dict[str, Any], request: ExecutionRequest[HookNode]
    ) -> Any:
        config = node.config
        file_path = config.get("file_path")

        format_type = config.get("format", "json")

        data = {"inputs": inputs, "node_id": node.label}

        try:
            path = Path(file_path)
            filesystem_adapter = request.get_handler_state("filesystem_adapter")
            if not filesystem_adapter:
                raise NodeExecutionError("Filesystem adapter not available")

            parent_dir = path.parent
            if parent_dir != Path() and not filesystem_adapter.exists(parent_dir):
                filesystem_adapter.mkdir(parent_dir, parents=True)

            content = serialize_data(data, format_type)

            with filesystem_adapter.open(path, "wb") as f:
                f.write(content.encode("utf-8"))

            return {"status": "success", "file": str(path)}

        except Exception as e:
            raise NodeExecutionError(f"File operation failed: {e!s}") from e
