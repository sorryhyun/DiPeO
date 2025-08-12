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
from dipeo.core.base.exceptions import InvalidDiagramError, NodeExecutionError
from dipeo.diagram_generated.generated_nodes import HookNode, NodeType
from dipeo.core.execution.node_output import TextOutput, ErrorOutput, NodeOutputProtocol
from dipeo.diagram_generated.models.hook_model import HookNodeData, HookType

if TYPE_CHECKING:
    from dipeo.core.execution.execution_context import ExecutionContext


@register_handler
class HookNodeHandler(TypedNodeHandler[HookNode]):
    """
    Clean separation of concerns:
    1. validate() - Static/structural validation (compile-time checks)
    2. pre_execute() - Runtime validation and setup
    3. execute_request() - Core execution logic
    """
    
    def __init__(self, filesystem_adapter: Optional[FileSystemPort] = None):
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
    
    async def pre_execute(self, request: ExecutionRequest[HookNode]) -> Optional[NodeOutputProtocol]:
        """Pre-execution setup: validate hook configuration and prepare resources.
        
        Moves hook validation, configuration parsing, and service resolution
        out of execute_request for cleaner separation of concerns.
        """
        node = request.node
        
        # Validate hook type
        valid_hook_types = {HookType.SHELL, HookType.WEBHOOK, HookType.PYTHON, HookType.FILE}
        if node.hook_type not in valid_hook_types:
            return ErrorOutput(
                value=f"Unknown hook type: {node.hook_type}",
                node_id=node.id,
                error_type="InvalidHookType"
            )
        
        # Validate configuration based on hook type
        config = node.config or {}
        
        if node.hook_type == HookType.SHELL:
            if not config.get("command"):
                return ErrorOutput(
                    value="Shell hook requires 'command' in config",
                    node_id=node.id,
                    error_type="MissingCommand"
                )
        elif node.hook_type == HookType.WEBHOOK:
            if not config.get("url"):
                return ErrorOutput(
                    value="Webhook hook requires 'url' in config",
                    node_id=node.id,
                    error_type="MissingURL"
                )
        elif node.hook_type == HookType.PYTHON:
            if not config.get("script"):
                return ErrorOutput(
                    value="Python hook requires 'script' in config",
                    node_id=node.id,
                    error_type="MissingScript"
                )
        elif node.hook_type == HookType.FILE:
            if not config.get("file_path"):
                return ErrorOutput(
                    value="File hook requires 'file_path' in config",
                    node_id=node.id,
                    error_type="MissingFilePath"
                )
            # Get filesystem adapter for file hooks
            from dipeo.application.registry import ServiceKey
            fs_key = ServiceKey("filesystem_adapter")
            filesystem_adapter = self.filesystem_adapter or request.services.get(fs_key)
            if not filesystem_adapter:
                return ErrorOutput(
                    value="Filesystem adapter is required for file hooks",
                    node_id=node.id,
                    error_type="MissingFilesystemAdapter"
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
    
    async def execute_request(self, request: ExecutionRequest[HookNode]) -> NodeOutputProtocol:
        """Pure execution using instance variables set in pre_execute."""
        return await self._execute_hook_node(request)
    
    async def _execute_hook_node(self, request: ExecutionRequest[HookNode]) -> NodeOutputProtocol:
        # Extract properties from request
        node = request.node
        inputs = request.inputs
        
        # Filesystem adapter already available in instance variable if needed (set in pre_execute for file hooks)
        if node.hook_type == HookType.FILE:
            self._temp_filesystem_adapter = self._current_filesystem_adapter
        
        try:
            result = await self._execute_hook(node, inputs)
            return TextOutput(
                value=str(result),
                node_id=node.id,
                metadata=json.dumps({"hook_type": node.hook_type})
            )
        except Exception as e:
            raise NodeExecutionError(f"Hook execution failed: {e!s}") from e
        finally:
            if hasattr(self, '_temp_filesystem_adapter'):
                delattr(self, '_temp_filesystem_adapter')
    
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
        # Configuration already validated in pre_execute
        config = node.config
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