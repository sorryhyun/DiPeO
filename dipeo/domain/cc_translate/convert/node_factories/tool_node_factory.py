"""Tool node factory for creating nodes based on tool events.

This module provides a factory that delegates node creation to
specialized builders based on the tool type.
"""

from typing import Any, Optional

from ..payload_processor import PayloadProcessor
from ..person_registry import PersonRegistry
from ..position_manager import PositionManager
from .api_node_builder import ApiNodeBuilder
from .code_node_builder import CodeNodeBuilder
from .db_node_builder import DbNodeBuilder
from .file_node_builder import FileNodeBuilder
from .person_node_builder import PersonNodeBuilder
from .start_node_builder import StartNodeBuilder


class ToolNodeFactory:
    """Factory for creating nodes based on tool events."""

    def __init__(
        self,
        person_registry: Optional[PersonRegistry] = None,
        position_manager: Optional[PositionManager] = None,
        payload_processor: Optional[PayloadProcessor] = None,
    ):
        """Initialize the tool node factory.

        Args:
            person_registry: Optional person registry
            position_manager: Optional position manager
            payload_processor: Optional payload processor
        """
        # Create shared resources
        self.person_registry = person_registry or PersonRegistry()
        self.position_manager = position_manager or PositionManager()
        self.payload_processor = payload_processor or PayloadProcessor()

        # Initialize specialized builders
        self.start_builder = StartNodeBuilder(self.position_manager)
        self.person_builder = PersonNodeBuilder(self.person_registry, self.position_manager)
        self.file_builder = FileNodeBuilder(self.payload_processor, self.position_manager)
        self.code_builder = CodeNodeBuilder(self.position_manager)
        self.db_builder = DbNodeBuilder(self.position_manager)
        self.api_builder = ApiNodeBuilder(self.position_manager)

        # Order matters - more specific builders should come first
        self.builders = [
            self.file_builder,
            self.code_builder,
            self.db_builder,
            self.api_builder,  # API builder last as it handles unknown tools
        ]

        # Track all nodes created
        self._all_nodes: list[dict[str, Any]] = []

    def reset(self):
        """Reset all builders and shared resources."""
        self.person_registry.reset()
        self.position_manager.reset()

        # Reset all builders
        for builder in [
            self.start_builder,
            self.person_builder,
            self.file_builder,
            self.code_builder,
            self.db_builder,
            self.api_builder,
        ]:
            builder.reset()

        self._all_nodes = []

    def create_start_node(self, session_id: str, initial_prompt: str) -> dict[str, Any]:
        """Create the start node for the diagram.

        Args:
            session_id: The Claude Code session ID
            initial_prompt: The initial user prompt

        Returns:
            The created start node
        """
        node = self.start_builder.create_start_node(session_id, initial_prompt)
        self._all_nodes.append(node)
        return node

    def create_user_node(self, content: str) -> Optional[dict[str, Any]]:
        """Create a node for user input.

        Args:
            content: The user's message content

        Returns:
            The created user node or None if content is empty
        """
        node = self.person_builder.create_user_node(content)
        if node:
            self._all_nodes.append(node)
        return node

    def create_assistant_node(
        self, content: str, system_messages: Optional[list[str]] = None
    ) -> Optional[dict[str, Any]]:
        """Handle AI assistant response.

        Args:
            content: The assistant's response content
            system_messages: Optional system messages for context

        Returns:
            Usually None as responses are outputs of user nodes
        """
        node = self.person_builder.create_assistant_node(content, system_messages)
        if node:
            self._all_nodes.append(node)
        return node

    def create_tool_node(
        self,
        tool_name: str,
        tool_input: dict[str, Any],
        tool_use_result: Optional[dict[str, Any]] = None,
    ) -> Optional[dict[str, Any]]:
        """Create appropriate node based on tool name.

        Args:
            tool_name: Name of the tool
            tool_input: Input parameters for the tool
            tool_use_result: Optional tool execution result

        Returns:
            The created node or None if not applicable
        """
        # Defensive handling for None or missing tool_name
        if not tool_name:
            print("Warning: Missing tool name, skipping node creation")
            return None

        # Ensure tool_input is a dict
        if tool_input is None:
            tool_input = {}
        elif not isinstance(tool_input, dict):
            print(f"Warning: Invalid tool_input type for {tool_name}, using empty dict")
            tool_input = {}

        try:
            # Find the appropriate builder
            for builder in self.builders:
                if builder.can_handle(tool_name):
                    node = builder.create_node(tool_name, tool_input, tool_use_result)
                    if node:
                        self._all_nodes.append(node)
                    return node

            # If no builder handles it, use API builder as fallback
            node = self.api_builder.create_generic_api_node(tool_name, tool_input)
            if node:
                self._all_nodes.append(node)
            return node

        except Exception as e:
            print(f"Warning: Error creating {tool_name} node: {e}")
            # Fallback to generic node on error
            node = self.api_builder.create_generic_api_node(tool_name, tool_input)
            if node:
                self._all_nodes.append(node)
            return node

    def get_all_nodes(self) -> list[dict[str, Any]]:
        """Get all nodes created by the factory.

        Returns:
            List of all created nodes
        """
        return self._all_nodes.copy()

    def get_persons(self) -> dict[str, dict[str, Any]]:
        """Get all registered persons.

        Returns:
            Dictionary of person configurations
        """
        return self.person_registry.get_all_persons()

    def get_node_count(self) -> int:
        """Get the total count of nodes created.

        Returns:
            Number of nodes created
        """
        return len(self._all_nodes)

    def increment_counter(self) -> int:
        """Increment and return the node counter.

        Returns:
            The incremented counter value
        """
        return self.position_manager.increment_counter()
