"""Base node builder with common functionality for all node types.

This module provides the abstract base class and common functionality
for all specialized node builders in the DiPeO diagram conversion.
"""

from abc import ABC, abstractmethod
from typing import Any, Optional

from ..position_manager import PositionManager


class BaseNodeBuilder(ABC):
    """Abstract base class for all node builders."""

    def __init__(self, position_manager: PositionManager | None = None):
        """Initialize the base node builder.

        Args:
            position_manager: Optional position manager for node layout
        """
        self.position_manager = position_manager or PositionManager()
        self.nodes: list[dict[str, Any]] = []
        self._node_counter = 0

    def reset(self):
        """Reset the builder state."""
        self.nodes = []
        self._node_counter = 0
        self.position_manager.reset()

    def increment_counter(self) -> int:
        """Increment and return the node counter.

        Returns:
            The incremented counter value
        """
        self._node_counter += 1
        return self._node_counter

    def get_position(self) -> dict[str, int]:
        """Get the position for the next node.

        Returns:
            Dictionary with x and y coordinates
        """
        return self.position_manager.get_next_position()

    def create_base_node(
        self,
        label: str,
        node_type: str,
        props: dict[str, Any],
        position: dict[str, int] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Create a base node structure.

        Args:
            label: The node label
            node_type: The type of node (e.g., "start", "person_job", "db")
            props: Node properties
            position: Optional position override
            metadata: Optional metadata

        Returns:
            The created node dictionary
        """
        node = {
            "label": label,
            "type": node_type,
            "position": position or self.get_position(),
            "props": props,
        }

        if metadata:
            node["metadata"] = metadata

        self.nodes.append(node)
        return node

    @abstractmethod
    def can_handle(self, tool_name: str) -> bool:
        """Check if this builder can handle the given tool.

        Args:
            tool_name: Name of the tool

        Returns:
            True if this builder can handle the tool
        """
        pass

    @abstractmethod
    def create_node(
        self,
        tool_name: str,
        tool_input: dict[str, Any],
        tool_result: dict[str, Any] | None = None,
    ) -> dict[str, Any] | None:
        """Create a node for the given tool.

        Args:
            tool_name: Name of the tool
            tool_input: Input parameters for the tool
            tool_result: Optional tool execution result

        Returns:
            The created node or None if not applicable
        """
        pass

    def validate_node(self, node: dict[str, Any]) -> list[str]:
        """Validate a node structure.

        Args:
            node: The node to validate

        Returns:
            List of validation errors (empty if valid)
        """
        errors = []

        # Check required fields
        required_fields = ["type", "label", "position"]
        for field in required_fields:
            if field not in node:
                errors.append(f"Missing required field: {field}")

        # Validate position structure
        if "position" in node:
            position = node["position"]
            if not isinstance(position, dict):
                errors.append("Position must be a dictionary")
            elif "x" not in position or "y" not in position:
                errors.append("Position must have x and y coordinates")

        # Validate props if present
        if "props" in node and not isinstance(node["props"], dict):
            errors.append("Node props must be a dictionary")

        return errors

    def get_nodes(self) -> list[dict[str, Any]]:
        """Get all created nodes.

        Returns:
            List of all nodes created by this builder
        """
        return self.nodes.copy()

    def get_node_count(self) -> int:
        """Get the count of nodes created.

        Returns:
            Number of nodes created
        """
        return len(self.nodes)


class SimpleNodeBuilder(BaseNodeBuilder):
    """Simple concrete implementation for basic node types."""

    def __init__(
        self,
        supported_tools: list[str],
        node_type: str,
        position_manager: PositionManager | None = None,
    ):
        """Initialize a simple node builder.

        Args:
            supported_tools: List of tool names this builder handles
            node_type: The type of node to create
            position_manager: Optional position manager
        """
        super().__init__(position_manager)
        self.supported_tools = supported_tools
        self.node_type = node_type

    def can_handle(self, tool_name: str) -> bool:
        """Check if this builder can handle the given tool.

        Args:
            tool_name: Name of the tool

        Returns:
            True if this builder can handle the tool
        """
        return tool_name in self.supported_tools

    def create_node(
        self,
        tool_name: str,
        tool_input: dict[str, Any],
        tool_result: dict[str, Any] | None = None,
    ) -> dict[str, Any] | None:
        """Create a node for the given tool.

        Args:
            tool_name: Name of the tool
            tool_input: Input parameters for the tool
            tool_result: Optional tool execution result

        Returns:
            The created node or None if not applicable
        """
        if not self.can_handle(tool_name):
            return None

        label = f"{tool_name} {self.increment_counter()}"
        props = self._build_props(tool_name, tool_input, tool_result)

        return self.create_base_node(
            label=label,
            node_type=self.node_type,
            props=props,
        )

    def _build_props(
        self,
        tool_name: str,
        tool_input: dict[str, Any],
        tool_result: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Build node properties.

        Args:
            tool_name: Name of the tool
            tool_input: Input parameters
            tool_result: Optional tool result

        Returns:
            Dictionary of node properties
        """
        # Default implementation - override in subclasses
        return {
            "tool": tool_name,
            **tool_input,
        }
