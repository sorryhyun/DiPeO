"""Start node builder for DiPeO diagrams.

This module handles the creation of start nodes which initiate
diagram execution in Claude Code translations.
"""

from typing import Any, Optional

from .base_node_builder import BaseNodeBuilder


class StartNodeBuilder(BaseNodeBuilder):
    """Builder for creating start nodes in DiPeO diagrams."""

    def can_handle(self, tool_name: str) -> bool:
        """Start nodes are not created from tools.

        Args:
            tool_name: Name of the tool

        Returns:
            Always False as start nodes are not tool-based
        """
        return False

    def create_node(
        self,
        tool_name: str,
        tool_input: dict[str, Any],
        tool_result: dict[str, Any] | None = None,
    ) -> dict[str, Any] | None:
        """Start nodes are not created from tool events.

        Args:
            tool_name: Name of the tool
            tool_input: Input parameters for the tool
            tool_result: Optional tool execution result

        Returns:
            Always None as start nodes are not tool-based
        """
        return None

    def create_start_node(self, session_id: str, initial_prompt: str) -> dict[str, Any]:
        """Create the start node for the diagram.

        Args:
            session_id: The Claude Code session ID
            initial_prompt: The initial user prompt that started the session

        Returns:
            The created start node
        """
        # Start node always at fixed position
        position = self.position_manager.get_start_position()

        node = {
            "label": "Start",
            "type": "start",
            "position": position,
            "props": {
                "trigger_mode": "manual",
                "custom_data": {
                    "session_id": session_id,
                    "initial_prompt": initial_prompt[:200]
                    if initial_prompt
                    else "Claude Code Session",
                },
            },
        }
        self.nodes.append(node)
        return node
