"""Data transformation rules for node connections."""

from typing import Any

from dipeo.diagram_generated.generated_nodes import (
    ExecutableNode,
    PersonJobNode,
)


class DataTransformRules:
    @staticmethod
    def get_data_transform(source: ExecutableNode, target: ExecutableNode) -> dict[str, Any]:
        """Returns transformation rules for data flow between nodes."""
        transforms = {}

        if isinstance(source, PersonJobNode) and source.tools:
            transforms["extract_tool_results"] = True

        return transforms

    @staticmethod
    def merge_transforms(
        edge_transform: dict[str, Any], type_based_transform: dict[str, Any]
    ) -> dict[str, Any]:
        """Edge-specific transforms take precedence."""
        return {**type_based_transform, **edge_transform}
