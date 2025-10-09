import asyncio
import json
import os
import subprocess
from typing import Any

from dipeo.application.execution.engine.request import ExecutionRequest
from dipeo.diagram_generated.unified_nodes.hook_node import HookNode
from dipeo.domain.base.exceptions import NodeExecutionError


async def execute_shell_hook(
    node: HookNode, inputs: dict[str, Any], request: ExecutionRequest[HookNode]
) -> Any:
    """Execute a shell command with environment variables from inputs.

    Args:
        node: The hook node configuration
        inputs: Input data to pass as environment variables
        request: The execution request containing state

    Returns:
        Command output (JSON if parseable, otherwise raw text)

    Raises:
        NodeExecutionError: If the command fails or times out
    """
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
