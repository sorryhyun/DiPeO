from pathlib import Path
from typing import Any

from dipeo.application.execution.execution_request import ExecutionRequest
from dipeo.application.execution.handlers.utils import serialize_data
from dipeo.diagram_generated.unified_nodes.hook_node import HookNode
from dipeo.domain.base.exceptions import NodeExecutionError


async def execute_file_hook(
    node: HookNode, inputs: dict[str, Any], request: ExecutionRequest[HookNode]
) -> Any:
    """Execute file hook - write data to a file.

    Args:
        node: The hook node configuration
        inputs: Input data to write to file
        request: The execution request containing state

    Returns:
        Status dictionary with file path

    Raises:
        NodeExecutionError: If file operation fails or filesystem adapter unavailable
    """
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
