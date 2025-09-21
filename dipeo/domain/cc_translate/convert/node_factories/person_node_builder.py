"""Person node builder for user and assistant interactions.

This module handles the creation of person_job nodes which represent
user inputs and AI assistant responses in DiPeO diagrams.
"""

from typing import Any, Optional

from ..person_registry import PersonRegistry
from .base_node_builder import BaseNodeBuilder


class PersonNodeBuilder(BaseNodeBuilder):
    """Builder for creating person (user/assistant) nodes."""

    def __init__(
        self,
        person_registry: PersonRegistry,
        position_manager: Optional[Any] = None,
    ):
        """Initialize the person node builder.

        Args:
            person_registry: Registry for managing persons
            position_manager: Optional position manager
        """
        super().__init__(position_manager)
        self.person_registry = person_registry

    def can_handle(self, tool_name: str) -> bool:
        """Person nodes are not created from tools.

        Args:
            tool_name: Name of the tool

        Returns:
            Always False as person nodes are not tool-based
        """
        return False

    def create_node(
        self,
        tool_name: str,
        tool_input: dict[str, Any],
        tool_result: Optional[dict[str, Any]] = None,
    ) -> Optional[dict[str, Any]]:
        """Person nodes are not created from tool events.

        Args:
            tool_name: Name of the tool
            tool_input: Input parameters for the tool
            tool_result: Optional tool execution result

        Returns:
            Always None as person nodes are not tool-based
        """
        return None

    def create_user_node(self, content: str) -> Optional[dict[str, Any]]:
        """Create a node for user input that Claude Code will respond to.

        Args:
            content: The user's message content

        Returns:
            The created user node or None if content is empty
        """
        # Skip creating node if content is empty or just whitespace
        if not content or not content.strip():
            return None

        label = f"Claude Responds To User {self.increment_counter()}"

        # Ensure Claude is registered
        person_id = self.person_registry.ensure_claude_registered()

        node = {
            "label": label,
            "type": "person_job",
            "position": self.get_position(),
            "props": {
                "person": person_id,  # Claude responds to the user's prompt
                "default_prompt": content,  # The user's message that Claude responds to
            },
        }
        self.nodes.append(node)
        return node

    def create_assistant_node(
        self, content: str, system_messages: Optional[list[str]] = None
    ) -> Optional[dict[str, Any]]:
        """Handle AI assistant response.

        In the Claude Code translation model, assistant responses are outputs
        of user prompt nodes, so this typically returns None unless special
        handling is needed.

        Args:
            content: The assistant's response content
            system_messages: Optional system messages for context

        Returns:
            Usually None as responses are outputs of user nodes
        """
        # Ensure Claude is registered with any system messages
        self.person_registry.ensure_claude_registered(system_messages)

        # Claude's responses are already the output from the previous user prompt node
        # We don't need to create separate nodes for pure text responses
        return None

    def create_custom_person_node(
        self,
        person_id: str,
        prompt: str,
        max_iterations: int = 1,
        system_prompt: Optional[str] = None,
    ) -> dict[str, Any]:
        """Create a node for a custom AI agent.

        Args:
            person_id: The person identifier
            prompt: The prompt for the person
            max_iterations: Maximum iterations for the person
            system_prompt: Optional system prompt

        Returns:
            The created person node
        """
        label = f"{person_id} Task {self.increment_counter()}"

        # Ensure person is registered
        if not self.person_registry.is_registered(person_id):
            raise ValueError(f"Person '{person_id}' is not registered")

        # Update system prompt if provided
        if system_prompt:
            self.person_registry.update_person(person_id, {"system_prompt": system_prompt})

        node = {
            "label": label,
            "type": "person_job",
            "position": self.get_position(),
            "props": {
                "person": person_id,
                "default_prompt": prompt,
            },
        }
        self.nodes.append(node)
        return node
