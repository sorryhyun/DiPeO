"""Refactored node builder using the factory pattern.

This module provides a simplified NodeBuilder interface that delegates
to specialized builders through the ToolNodeFactory.
"""

from typing import Any, Optional

from .node_factories.tool_node_factory import ToolNodeFactory
from .payload_processor import PayloadProcessor
from .person_registry import PersonRegistry
from .position_manager import PositionManager


class NodeBuilder:
    """Refactored NodeBuilder using factory pattern for better separation of concerns."""

    def __init__(self):
        """Initialize the refactored node builder."""
        self.person_registry = PersonRegistry()
        self.position_manager = PositionManager()
        self.payload_processor = PayloadProcessor()

        self.factory = ToolNodeFactory(
            person_registry=self.person_registry,
            position_manager=self.position_manager,
            payload_processor=self.payload_processor,
        )

        # For compatibility, expose some properties
        self.node_counter = 0
        self.persons = {}

        # Import utilities for backward compatibility
        from .utils import DiffGenerator, TextProcessor

        self.text_processor = TextProcessor()
        self.diff_generator = DiffGenerator()

    def reset(self):
        """Reset the node builder state."""
        from .utils import TextProcessor

        self.factory.reset()
        self.node_counter = 0
        self.persons = {}
        self.text_processor = TextProcessor()

    def increment_counter(self) -> int:
        """Increment and return the node counter.

        Returns:
            The incremented counter value
        """
        self.node_counter = self.factory.increment_counter()
        return self.node_counter

    def get_position(self) -> dict[str, int]:
        """Calculate node position based on current counter.

        Returns:
            Dictionary with x and y coordinates
        """
        return self.position_manager.get_next_position()

    def create_start_node(self, session_id: str, initial_prompt: str) -> dict[str, Any]:
        """Create the start node for the diagram.

        Args:
            session_id: The Claude Code session ID
            initial_prompt: The initial user prompt

        Returns:
            The created start node
        """
        return self.factory.create_start_node(session_id, initial_prompt)

    def create_user_node(self, content: str) -> dict[str, Any] | None:
        """Create a node for user input that Claude Code will respond to.

        Args:
            content: The user's message content

        Returns:
            The created user node or None if content is empty
        """
        return self.factory.create_user_node(content)

    def create_assistant_node(
        self, content: str, system_messages: list[str] | None = None
    ) -> dict[str, Any] | None:
        """Handle AI assistant response.

        Args:
            content: The assistant's response content
            system_messages: Optional system messages for context

        Returns:
            Usually None as responses are outputs of user nodes
        """
        return self.factory.create_assistant_node(content, system_messages)

    def create_tool_node(
        self,
        tool_name: str,
        tool_input: dict[str, Any],
        tool_use_result: dict[str, Any] | None = None,
    ) -> dict[str, Any] | None:
        """Create appropriate node based on tool name.

        Args:
            tool_name: Name of the tool
            tool_input: Input parameters for the tool
            tool_use_result: Optional tool execution result

        Returns:
            The created node or None if not applicable
        """
        self.text_processor.set_last_tool(tool_name)
        return self.factory.create_tool_node(tool_name, tool_input, tool_use_result)

    # Compatibility methods for direct access
    def create_read_node(self, tool_input: dict[str, Any]) -> dict[str, Any]:
        """Create a DB node for file read operation."""
        return self.factory.create_tool_node("Read", tool_input)

    def create_write_node(
        self, tool_input: dict[str, Any], tool_use_result: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """Create a DB node for file write operation."""
        return self.factory.create_tool_node("Write", tool_input, tool_use_result)

    def create_edit_node(
        self, tool_name: str, tool_input: dict[str, Any], original_content: str | None = None
    ) -> dict[str, Any]:
        """Create a diff_patch node for file edit operation."""
        return self.factory.create_tool_node(tool_name, tool_input)

    def create_edit_node_with_result(
        self,
        tool_name: str,
        tool_input: dict[str, Any],
        tool_use_result: dict[str, Any] | None = None,
    ) -> dict[str, Any] | None:
        """Create a diff_patch node using tool_use_result for better diff generation."""
        return self.factory.create_tool_node(tool_name, tool_input, tool_use_result)

    def create_bash_node(self, tool_input: dict[str, Any]) -> dict[str, Any]:
        """Create a code_job node for bash command execution."""
        return self.factory.create_tool_node("Bash", tool_input)

    def create_todo_node(self, tool_input: dict[str, Any]) -> dict[str, Any]:
        """Create a DB node for TodoWrite operation."""
        return self.factory.create_tool_node("TodoWrite", tool_input)

    def create_search_node(self, tool_name: str, tool_input: dict[str, Any]) -> dict[str, Any]:
        """Create a code_job node for search operations."""
        return self.factory.create_tool_node(tool_name, tool_input)

    def create_generic_tool_node(
        self, tool_name: str, tool_input: dict[str, Any]
    ) -> dict[str, Any]:
        """Create a generic API node for unknown tools."""
        return self.factory.create_tool_node(tool_name, tool_input)

    def get_nodes(self) -> list[dict[str, Any]]:
        """Get all created nodes.

        Returns:
            List of all nodes created by this builder
        """
        return self.factory.get_all_nodes()

    def get_persons(self) -> dict[str, dict[str, Any]]:
        """Get all registered persons.

        Returns:
            Dictionary of person configurations
        """
        self.persons = self.factory.get_persons()
        return self.persons

    @property
    def nodes(self) -> list[dict[str, Any]]:
        """Property for backward compatibility with direct nodes access."""
        return self.factory.get_all_nodes()
