import asyncio
import json
import os
import subprocess
from pathlib import Path
from typing import TYPE_CHECKING, Any

import aiohttp
from pydantic import BaseModel

from dipeo.application.execution.handler_factory import register_handler
from dipeo.application.execution.handler_base import TypedNodeHandler
from dipeo.core.base.exceptions import InvalidDiagramError, NodeExecutionError
from dipeo.diagram_generated.nodes.hook_node import HookNode
from dipeo.core.execution.node_output import TextOutput, NodeOutputProtocol
from dipeo.diagram_generated import HookNodeData, HookType, NodeType

if TYPE_CHECKING:
    from dipeo.application.execution.execution_runtime import ExecutionRuntime
    from dipeo.core.dynamic.execution_context import ExecutionContext


@register_handler
class HookNodeHandler(TypedNodeHandler[HookNode]):
    
    def __init__(self):
        pass

    
    @property
    def node_class(self) -> type[HookNode]:
        return HookNode
    
    @property
    def node_type(self) -> str:
        return NodeType.hook.value
    
    @property
    def schema(self) -> type[BaseModel]:
        return HookNodeData
    
    
    @property
    def description(self) -> str:
        return "Execute external hooks (shell commands, webhooks, Python scripts, or file operations)"
    
    async def execute(
        self,
        node: HookNode,
        context: "ExecutionContext",
        inputs: dict[str, Any],
        services: dict[str, Any]
    ) -> NodeOutputProtocol:
        return await self._execute_hook_node(node, context, inputs, services)
    
    async def _execute_hook_node(
        self,
        node: HookNode,
        context: "ExecutionContext",
        inputs: dict[str, Any],
        services: dict[str, Any]
    ) -> NodeOutputProtocol:
        try:
            result = await self._execute_hook(node, inputs)
            return TextOutput(
                value=str(result),
                node_id=node.id,
                metadata={"hook_type": node.hook_type}
            )
        except Exception as e:
            raise NodeExecutionError(f"Hook execution failed: {e!s}") from e
    
    async def _execute_hook(self, node: HookNode, inputs: dict[str, Any]) -> Any:
        if node.hook_type == HookType.shell:
            return await self._execute_shell_hook(node, inputs)
        elif node.hook_type == HookType.webhook:
            return await self._execute_webhook_hook(node, inputs)
        elif node.hook_type == HookType.python:
            return await self._execute_python_hook(node, inputs)
        elif node.hook_type == HookType.file:
            return await self._execute_file_hook(node, inputs)
        else:
            raise InvalidDiagramError(f"Unknown hook type: {node.hook_type}")
    
    async def _execute_shell_hook(self, node: HookNode, inputs: dict[str, Any]) -> Any:
        config = node.config
        command = config.get("command")
        if not command:
            raise InvalidDiagramError("Shell hook requires 'command' in config")
        
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
            timeout = node.timeout or 30
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
        config = node.config
        url = config.get("url")
        if not url:
            raise InvalidDiagramError("Webhook hook requires 'url' in config")
        
        method = config.get("method", "POST")
        headers = config.get("headers", {})
        headers["Content-Type"] = "application/json"
        
        # Prepare payload with inputs
        payload = {
            "inputs": inputs,
            "hook_type": "hook_node",
            "node_id": node.label
        }
        
        timeout = aiohttp.ClientTimeout(total=node.timeout or 30)
        
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
        config = node.config
        script = config.get("script")
        if not script:
            raise InvalidDiagramError("Python hook requires 'script' in config")
        
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
            
            timeout = node.timeout or 30
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
        config = node.config
        file_path = config.get("file_path")
        if not file_path:
            raise InvalidDiagramError("File hook requires 'file_path' in config")
        
        format_type = config.get("format", "json")
        
        # Prepare data to write
        data = {
            "inputs": inputs,
            "node_id": node.label
        }
        
        try:
            path = Path(file_path)
            path.parent.mkdir(parents=True, exist_ok=True)
            
            if format_type == "json":
                with open(path, "w") as f:
                    json.dump(data, f, indent=2)
            elif format_type == "yaml":
                import yaml
                with open(path, "w") as f:
                    yaml.dump(data, f, default_flow_style=False)
            else:  # text
                with open(path, "w") as f:
                    f.write(str(data))
            
            return {"status": "success", "file": str(path)}
            
        except Exception as e:
            raise NodeExecutionError(f"File operation failed: {e!s}")