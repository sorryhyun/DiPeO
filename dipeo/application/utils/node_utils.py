# Node utility functions

from typing import Any, Dict


def create_node_output(
    value: Dict[str, Any] | None = None,
    metadata: Dict[str, Any] | None = None,
    node_id: str | None = None,
    executed_nodes: list[str] | None = None,
) -> Any:
    from dipeo.models import NodeOutput

    return NodeOutput(
        value=value or {}, 
        metadata=metadata,
        node_id=node_id,
        executed_nodes=executed_nodes
    )