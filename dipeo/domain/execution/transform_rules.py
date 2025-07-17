"""Data transformation rules for node connections."""

from typing import Any

from dipeo.core.static.generated_nodes import (
    ConditionNode,
    ExecutableNode,
    PersonJobNode,
)


class DataTransformRules:
    """Defines data transformation rules between different node types."""
    
    @staticmethod
    def get_data_transform(
        source: ExecutableNode, 
        target: ExecutableNode
    ) -> dict[str, Any]:
        """Define data transformations based on node types.
        
        Returns transformation rules that describe how data should
        be transformed when flowing from source to target node.
        """
        transforms = {}
        
        # Person node with tools: extract tool results
        if isinstance(source, PersonJobNode) and source.tools:
            transforms["extract_tool_results"] = True
        
        # Condition node: mark branching behavior
        if isinstance(source, ConditionNode):
            transforms["branch_on"] = "condition_result"
        
        # Future: Add more transformation rules as needed
        # Examples:
        # - API response parsing
        # - Code execution output formatting
        # - Data type conversions
        
        return transforms
    
    @staticmethod
    def merge_transforms(
        edge_transform: dict[str, Any],
        type_based_transform: dict[str, Any]
    ) -> dict[str, Any]:
        """Merge edge-specific and type-based transformations.
        
        Edge-specific transforms take precedence over type-based ones.
        """
        return {**type_based_transform, **edge_transform}