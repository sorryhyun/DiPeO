"""Compatibility classes for migration from StaticDiagramCompiler."""

from typing import Any
from dipeo.diagram_generated import NodeID, NodeType


class ExecutableNodeImpl:
    """Compatibility wrapper for nodes used by ArrowTransformer.

    This provides a uniform interface for accessing node properties
    regardless of the underlying node implementation.
    """

    def __init__(
            self,
            id: NodeID,
            type: NodeType,
            position: Any,
            data: dict[str, Any]
    ):
        self.id = id
        self.type = type
        self.position = position
        self.data = data

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "type": self.type.value,
            "position": {
                "x": self.position.x,
                "y": self.position.y
            },
            "data": self.data
        }