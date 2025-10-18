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
        self.node_counter = self.factory.increment_counter()
        return self.node_counter

    def get_position(self) -> dict[str, int]:
        return self.position_manager.get_next_position()

    def create_start_node(self, session_id: str, initial_prompt: str) -> dict[str, Any]:
        return self.factory.create_start_node(session_id, initial_prompt)

    def create_user_node(self, content: str) -> dict[str, Any] | None:
        return self.factory.create_user_node(content)

    def create_assistant_node(
        self, content: str, system_messages: list[str] | None = None
    ) -> dict[str, Any] | None:
        return self.factory.create_assistant_node(content, system_messages)

    def create_tool_node(
        self,
        tool_name: str,
        tool_input: dict[str, Any],
        tool_use_result: dict[str, Any] | None = None,
    ) -> dict[str, Any] | None:
        self.text_processor.set_last_tool(tool_name)
        return self.factory.create_tool_node(tool_name, tool_input, tool_use_result)

    # Compatibility methods for direct access
    def create_read_node(self, tool_input: dict[str, Any]) -> dict[str, Any]:
        return self.factory.create_tool_node("Read", tool_input)

    def create_write_node(
        self, tool_input: dict[str, Any], tool_use_result: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        return self.factory.create_tool_node("Write", tool_input, tool_use_result)

    def create_edit_node(
        self, tool_name: str, tool_input: dict[str, Any], original_content: str | None = None
    ) -> dict[str, Any]:
        return self.factory.create_tool_node(tool_name, tool_input)

    def create_edit_node_with_result(
        self,
        tool_name: str,
        tool_input: dict[str, Any],
        tool_use_result: dict[str, Any] | None = None,
    ) -> dict[str, Any] | None:
        return self.factory.create_tool_node(tool_name, tool_input, tool_use_result)

    def create_bash_node(self, tool_input: dict[str, Any]) -> dict[str, Any]:
        return self.factory.create_tool_node("Bash", tool_input)

    def create_todo_node(self, tool_input: dict[str, Any]) -> dict[str, Any]:
        return self.factory.create_tool_node("TodoWrite", tool_input)

    def create_search_node(self, tool_name: str, tool_input: dict[str, Any]) -> dict[str, Any]:
        return self.factory.create_tool_node(tool_name, tool_input)

    def create_generic_tool_node(
        self, tool_name: str, tool_input: dict[str, Any]
    ) -> dict[str, Any]:
        return self.factory.create_tool_node(tool_name, tool_input)

    def get_nodes(self) -> list[dict[str, Any]]:
        return self.factory.get_all_nodes()

    def get_persons(self) -> dict[str, dict[str, Any]]:
        self.persons = self.factory.get_persons()
        return self.persons

    @property
    def nodes(self) -> list[dict[str, Any]]:
        return self.factory.get_all_nodes()
