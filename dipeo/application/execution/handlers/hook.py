import asyncio
import json
import os
import subprocess
from pathlib import Path
from typing import TYPE_CHECKING, Any, Optional

import aiohttp
from pydantic import BaseModel
from dipeo.domain.ports.storage import FileSystemPort

from dipeo.application.execution.handler_factory import register_handler
from dipeo.application.execution.handler_base import TypedNodeHandler
from dipeo.application.execution.execution_request import ExecutionRequest
from dipeo.application.registry.keys import FILESYSTEM_ADAPTER, EVENT_BUS
from dipeo.domain.base.exceptions import InvalidDiagramError, NodeExecutionError
from dipeo.diagram_generated.generated_nodes import HookNode, NodeType
from dipeo.domain.execution.envelope import Envelope, EnvelopeFactory
from dipeo.diagram_generated.models.hook_model import HookNodeData, HookType
from dipeo.domain.events import EventConsumer, ExecutionEvent

if TYPE_CHECKING:
    from dipeo.domain.execution.execution_context import ExecutionContext


@register_handler
class HookNodeHandler(TypedNodeHandler[HookNode]):
    """
    Clean separation of concerns:
    1. validate() - Static/structural validation (compile-time checks)
    2. pre_execute() - Runtime validation and setup
    3. execute_with_envelopes() - Core execution logic with envelope inputs
    
    Now uses envelope-based communication for clean input/output interfaces.
    """
    
    
    def __init__(self, filesystem_adapter: Optional[FileSystemPort] = None):
        super().__init__()
        self.filesystem_adapter = filesystem_adapter
        # Instance variables for passing data between methods
        self._current_filesystem_adapter = None
        self._current_timeout = None

    
    @property
    def node_class(self) -> type[HookNode]:
        return HookNode
    
    @property
    def node_type(self) -> str:
        return NodeType.HOOK.value
    
    @property
    def schema(self) -> type[BaseModel]:
        return HookNodeData
    
    
    @property
    def description(self) -> str:
        return "Execute external hooks (shell commands, webhooks, Python scripts, or file operations)"
    
    @property
    def requires_services(self) -> list[str]:
        return ["filesystem_adapter"]
    
    async def pre_execute(self, request: ExecutionRequest[HookNode]) -> Optional[Envelope]:
        """Pre-execution setup: validate hook configuration and prepare resources.
        
        Moves hook validation, configuration parsing, and service resolution
        out of execute_request for cleaner separation of concerns.
        """
        node = request.node
        
        # Validate hook type
        valid_hook_types = {HookType.SHELL, HookType.WEBHOOK, HookType.PYTHON, HookType.FILE}
        if node.hook_type not in valid_hook_types:
            return EnvelopeFactory.error(
                f"Unknown hook type: {node.hook_type}",
                error_type="ValueError",
                produced_by=str(node.id)
            )
        
        # Validate configuration based on hook type
        config = node.config or {}
        
        if node.hook_type == HookType.SHELL:
            if not config.get("command"):
                return EnvelopeFactory.error(
                    "Shell hook requires 'command' in config",
                    error_type="ValueError",
                    produced_by=str(node.id)
                )
        elif node.hook_type == HookType.WEBHOOK:
            if not config.get("url"):
                return EnvelopeFactory.error(
                    "Webhook hook requires 'url' in config",
                    error_type="ValueError",
                    produced_by=str(node.id)
                )
        elif node.hook_type == HookType.PYTHON:
            if not config.get("script"):
                return EnvelopeFactory.error(
                    "Python hook requires 'script' in config",
                    error_type="ValueError",
                    produced_by=str(node.id)
                )
        elif node.hook_type == HookType.FILE:
            if not config.get("file_path"):
                return EnvelopeFactory.error(
                    "File hook requires 'file_path' in config",
                    error_type="ValueError",
                    produced_by=str(node.id)
                )
            # Get filesystem adapter for file hooks
            filesystem_adapter = self.filesystem_adapter or request.services.resolve(FILESYSTEM_ADAPTER)
            if not filesystem_adapter:
                return EnvelopeFactory.error(
                    "Filesystem adapter is required for file hooks",
                    error_type="ValueError",
                    produced_by=str(node.id)
                )
            # Store in instance variable for execute_request
            self._current_filesystem_adapter = filesystem_adapter
        else:
            # Clear filesystem adapter for non-file hooks
            self._current_filesystem_adapter = None
        
        # Store timeout configuration in instance variable
        self._current_timeout = node.timeout or 30
        
        # No early return - proceed to execute_request
        return None
    
    async def prepare_inputs(
        self,
        request: ExecutionRequest[HookNode],
        inputs: dict[str, Envelope]
    ) -> dict[str, Any]:
        """Convert envelope inputs to legacy format for hook execution."""
        # Convert envelope inputs to legacy format
        prepared_inputs = {}
        for key, envelope in inputs.items():
            try:
                # Try to parse as JSON first
                prepared_inputs[key] = envelope.as_json()
            except ValueError:
                # Fall back to text
                prepared_inputs[key] = envelope.as_text()
        
        # Filesystem adapter already available in instance variable if needed (set in pre_execute for file hooks)
        if request.node.hook_type == HookType.FILE:
            self._temp_filesystem_adapter = self._current_filesystem_adapter
        
        return prepared_inputs
    
    async def run(
        self,
        inputs: dict[str, Any],
        request: ExecutionRequest[HookNode]
    ) -> Any:
        """Execute the hook with prepared inputs."""
        node = request.node
        
        try:
            result = await self._execute_hook(node, inputs)
            return result
        finally:
            if hasattr(self, '_temp_filesystem_adapter'):
                delattr(self, '_temp_filesystem_adapter')
    
    def serialize_output(
        self,
        result: Any,
        request: ExecutionRequest[HookNode]
    ) -> Envelope:
        """Serialize hook result to envelope."""
        node = request.node
        trace_id = request.execution_id or ""
        
        # Create output envelope
        output_envelope = EnvelopeFactory.text(
            str(result) if not isinstance(result, dict) else json.dumps(result),
            produced_by=node.id,
            trace_id=trace_id
        ).with_meta(
            hook_type=str(node.hook_type)
        )
        
        return output_envelope
    
    async def _execute_hook(self, node: HookNode, inputs: dict[str, Any]) -> Any:
        # Hook type already validated in pre_execute
        if node.hook_type == HookType.SHELL:
            return await self._execute_shell_hook(node, inputs)
        elif node.hook_type == HookType.WEBHOOK:
            return await self._execute_webhook_hook(node, inputs)
        elif node.hook_type == HookType.PYTHON:
            return await self._execute_python_hook(node, inputs)
        elif node.hook_type == HookType.FILE:
            return await self._execute_file_hook(node, inputs)
        else:
            # This should never happen since validation occurs in pre_execute
            raise InvalidDiagramError(f"Unknown hook type: {node.hook_type}")
    
    async def _execute_shell_hook(self, node: HookNode, inputs: dict[str, Any]) -> Any:
        # Configuration already validated in pre_execute
        config = node.config
        command = config.get("command")
        
        # Prepare environment variables
        env = os.environ.copy()
        if config.get("env"):
            env.update(config["env"])
        
        # Add inputs as environment variables
        for key, value in inputs.items():
            env[f"DIPEO_INPUT_{key.upper()}"] = json.dumps(value)
        
        # Prepare command with arguments
        args = config.get("args", [])
        cmd = [command] + args
        
        # Execute command
        try:
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=config.get("cwd"),
                env=env
            )
            
            # Apply timeout if specified
            timeout = self._current_timeout or 30
            stdout, stderr = await asyncio.wait_for(
                process.communicate(),
                timeout=timeout
            )
            
            if process.returncode != 0:
                raise NodeExecutionError(
                    f"Shell command failed with code {process.returncode}: {stderr.decode()}"
                )
            
            # Try to parse output as JSON, fallback to string
            output = stdout.decode().strip()
            try:
                return json.loads(output)
            except json.JSONDecodeError:
                return output
                
        except TimeoutError:
            raise NodeExecutionError(f"Shell command timed out after {timeout} seconds")
    
    async def _execute_webhook_hook(self, node: HookNode, inputs: dict[str, Any]) -> Any:
        """Execute webhook hook - either send a request or subscribe to events.
        
        Two modes supported:
        1. Outgoing webhook: Send HTTP request to external URL
        2. Event subscription: Subscribe to webhook events from providers
        """
        config = node.config
        
        # Check if this is a subscription hook
        if config.get("subscribe_to"):
            return await self._subscribe_to_webhook_events(node, inputs)
        
        # Otherwise, it's an outgoing webhook request
        url = config.get("url")
        
        method = config.get("method", "POST")
        headers = config.get("headers", {})
        headers["Content-Type"] = "application/json"
        
        # Prepare payload with inputs
        payload = {
            "inputs": inputs,
            "hook_type": "hook_node",
            "node_id": node.label
        }
        
        timeout = aiohttp.ClientTimeout(total=self._current_timeout or 30)
        
        async with aiohttp.ClientSession(timeout=timeout) as session:
            try:
                async with session.request(
                    method=method,
                    url=url,
                    headers=headers,
                    json=payload
                ) as response:
                    response.raise_for_status()
                    return await response.json()
            except aiohttp.ClientError as e:
                raise NodeExecutionError(f"Webhook request failed: {e!s}")
    
    async def _subscribe_to_webhook_events(self, node: HookNode, inputs: dict[str, Any]) -> Any:
        """Subscribe to webhook events from providers.
        
        This allows a diagram to be triggered by incoming webhooks.
        The hook node will wait for matching events from the event bus.
        """
        config = node.config
        subscribe_config = config.get("subscribe_to", {})
        
        provider = subscribe_config.get("provider")
        event_name = subscribe_config.get("event_name")
        timeout = subscribe_config.get("timeout", 60)  # Default 60 second wait
        filter_conditions = subscribe_config.get("filters", {})
        
        if not provider:
            raise NodeExecutionError("Webhook subscription requires 'provider' in subscribe_to config")
        
        # Create an event consumer to wait for the webhook event
        received_event = None
        event_received = asyncio.Event()
        
        class WebhookEventConsumer(EventConsumer):
            async def consume(self, event: ExecutionEvent) -> None:
                nonlocal received_event
                
                # Check if this is a webhook event for our provider
                event_data = event.data
                if event_data.get("source") != "webhook":
                    return
                
                if event_data.get("provider") != provider:
                    return
                
                if event_name and event_data.get("event_name") != event_name:
                    return
                
                # Apply additional filters if specified
                payload = event_data.get("payload", {})
                for key, expected_value in filter_conditions.items():
                    if payload.get(key) != expected_value:
                        return
                
                # Event matches our criteria
                received_event = event_data
                event_received.set()
        
        # Register our consumer with the event bus (if available)
        # Note: In a real implementation, we'd need access to the event bus
        # For now, this is a placeholder showing the pattern
        
        try:
            # Wait for the event with timeout
            await asyncio.wait_for(event_received.wait(), timeout=timeout)
            
            if received_event:
                return {
                    "status": "triggered",
                    "provider": provider,
                    "event_name": received_event.get("event_name"),
                    "payload": received_event.get("payload"),
                    "headers": received_event.get("headers", {})
                }
            else:
                return {
                    "status": "timeout",
                    "provider": provider,
                    "message": f"No matching webhook event received within {timeout} seconds"
                }
                
        except asyncio.TimeoutError:
            return {
                "status": "timeout",
                "provider": provider,
                "message": f"Webhook subscription timed out after {timeout} seconds"
            }
    
    async def _execute_python_hook(self, node: HookNode, inputs: dict[str, Any]) -> Any:
        # Configuration already validated in pre_execute
        config = node.config
        script = config.get("script")
        
        function_name = config.get("function_name", "hook")
        
        # Prepare Python code to execute
        code = f"""
import json
import sys

{script}

# Execute the hook function
result = {function_name}({json.dumps(inputs)})
print(json.dumps(result))
"""
        
        # Execute Python script
        try:
            process = await asyncio.create_subprocess_exec(
                "python", "-c", code,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            
            timeout = self._current_timeout or 30
            stdout, stderr = await asyncio.wait_for(
                process.communicate(),
                timeout=timeout
            )
            
            if process.returncode != 0:
                raise NodeExecutionError(
                    f"Python script failed with code {process.returncode}: {stderr.decode()}"
                )
            
            return json.loads(stdout.decode().strip())
            
        except TimeoutError:
            raise NodeExecutionError(f"Python script timed out after {timeout} seconds")
        except json.JSONDecodeError as e:
            raise NodeExecutionError(f"Failed to parse Python script output: {e!s}")
    
    async def _execute_file_hook(self, node: HookNode, inputs: dict[str, Any]) -> Any:
        # Configuration already validated in pre_execute
        config = node.config
        file_path = config.get("file_path")
        
        format_type = config.get("format", "json")
        
        # Prepare data to write
        data = {
            "inputs": inputs,
            "node_id": node.label
        }
        
        try:
            path = Path(file_path)
            filesystem_adapter = getattr(self, '_temp_filesystem_adapter', self.filesystem_adapter)
            if not filesystem_adapter:
                raise NodeExecutionError("Filesystem adapter not available")
            
            # Create parent directories if needed
            parent_dir = path.parent
            if parent_dir != Path(".") and not filesystem_adapter.exists(parent_dir):
                filesystem_adapter.mkdir(parent_dir, parents=True)
            
            # Prepare content based on format
            if format_type == "json":
                content = json.dumps(data, indent=2)
            elif format_type == "yaml":
                import yaml
                content = yaml.dump(data, default_flow_style=False)
            else:  # text
                content = str(data)
            
            # Write file
            with filesystem_adapter.open(path, "wb") as f:
                f.write(content.encode('utf-8'))
            
            return {"status": "success", "file": str(path)}
            
        except Exception as e:
            raise NodeExecutionError(f"File operation failed: {e!s}")