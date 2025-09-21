"""Event turn processor for Claude Code session conversion.

This module handles processing of conversation turns, converting domain events
into diagram nodes with appropriate handling for different event types.
"""

from typing import Optional

from ..models.event import DomainEvent, EventType
from ..models.preprocessed import PreprocessedData


class EventTurnProcessor:
    """Processes conversation turns and creates nodes from events."""

    def __init__(self, node_builder):
        """Initialize the processor with a node builder.

        Args:
            node_builder: NodeBuilder instance for creating nodes
        """
        self.node_builder = node_builder
        self.node_map: dict[str, str] = {}  # Maps event UUID to node label

        # Tools whose results are automatically appended to the next node
        self.tools_with_auto_appended_results = [
            "Bash",
            "Read",
            "Grep",
            "Glob",
            "NotebookRead",
            "BashOutput",
            "WebFetch",
            "WebSearch",
        ]

    def reset(self) -> None:
        """Reset processor state for new conversion."""
        self.node_map = {}

    def process_turn(
        self, turn_events: list[DomainEvent], preprocessed_data: PreprocessedData
    ) -> list[str]:
        """Process a turn of events and create corresponding nodes.

        Args:
            turn_events: List of events in this conversation turn
            preprocessed_data: The preprocessed session data for context

        Returns:
            List of node labels created from the events
        """
        node_labels = []

        # Extract system messages from preprocessed data
        system_messages = self._extract_system_messages(preprocessed_data)

        # Track tool usage by UUID to handle TOOL_RESULT events
        tool_by_uuid = {}  # Maps event UUID to tool name
        last_tool_with_auto_append = None  # Track tools whose results are auto-appended

        for event in turn_events:
            if event.is_user_event():
                # Skip meta events and events without content
                if not event.is_meta:
                    user_node_label = self._create_user_node(event)
                    if user_node_label:
                        node_labels.append(user_node_label)

            elif event.is_assistant_event():
                # Check if this assistant event has tool usage
                if event.has_tool_use():
                    tool_node_labels = self._create_tool_nodes(event)
                    node_labels.extend(tool_node_labels)

                    # Track this tool use by UUID for handling TOOL_RESULT events
                    if event.tool_info:
                        tool_by_uuid[event.uuid] = event.tool_info.name
                        # Track if this tool's results will be auto-appended
                        if event.tool_info.name in self.tools_with_auto_appended_results:
                            last_tool_with_auto_append = event.tool_info.name
                else:
                    # Skip assistant responses that are just displaying results from Read/Grep/Bash
                    if last_tool_with_auto_append:
                        last_tool_with_auto_append = None  # Reset after skipping
                    else:
                        # Pure assistant responses don't create nodes (they're outputs of user prompts)
                        # Still call create_assistant_node to register the claude_code person if needed
                        assistant_node_label = self._create_assistant_node(event, system_messages)
                        if assistant_node_label:
                            node_labels.append(assistant_node_label)

            elif event.type == EventType.TOOL_USE:
                # Create the tool node
                tool_node_labels = self._create_tool_nodes(event)
                node_labels.extend(tool_node_labels)

                # Track this tool use by UUID
                if event.tool_info:
                    tool_by_uuid[event.uuid] = event.tool_info.name
                    # Track if this tool's results will be auto-appended
                    if event.tool_info.name in self.tools_with_auto_appended_results:
                        last_tool_with_auto_append = event.tool_info.name

            elif event.type == EventType.TOOL_RESULT:
                # Check if this result is from a tool with auto-appended results
                parent_tool_name = None
                if event.parent_uuid and event.parent_uuid in tool_by_uuid:
                    parent_tool_name = tool_by_uuid[event.parent_uuid]

                if parent_tool_name and parent_tool_name in self.tools_with_auto_appended_results:
                    # Skip TOOL_RESULT for tools whose results are auto-appended
                    pass
                else:
                    # Create node for other TOOL_RESULT events (e.g., API responses)
                    tool_node_labels = self._create_tool_nodes(event)
                    node_labels.extend(tool_node_labels)

        return node_labels

    def _create_user_node(self, event: DomainEvent) -> Optional[str]:
        """Create a node for user input from domain event.

        Args:
            event: The user event to process

        Returns:
            Node label if created, None otherwise
        """
        content = event.content.text or ""

        # Skip empty content
        if not content.strip():
            return None

        node = self.node_builder.create_user_node(content)
        if node:
            self.node_map[event.uuid] = node["label"]
            return node["label"]
        return None

    def _create_assistant_node(
        self, event: DomainEvent, system_messages: list[str]
    ) -> Optional[str]:
        """Handle AI assistant response from domain event - typically returns None.

        Args:
            event: The assistant event to process
            system_messages: System messages for context

        Returns:
            Node label if created (rare), None otherwise
        """
        content = event.content.text or ""

        if not content.strip():
            return None

        # Call create_assistant_node which now returns None for pure text responses
        node = self.node_builder.create_assistant_node(content, system_messages)
        if node:
            self.node_map[event.uuid] = node["label"]
            return node["label"]

        # Most assistant responses won't create nodes since they're outputs of user prompts
        return None

    def _create_tool_nodes(self, event: DomainEvent) -> list[str]:
        """Create nodes for tool usage from domain event.

        Args:
            event: The tool-related event to process

        Returns:
            List of node labels created
        """
        node_labels = []

        if not event.tool_info:
            return node_labels

        tool_name = event.tool_info.name
        tool_input = event.tool_info.input_params
        tool_results = event.tool_info.results if event.tool_info.results else None

        # Create appropriate node for the tool
        node = self.node_builder.create_tool_node(tool_name, tool_input, tool_results)

        if node:
            node_labels.append(node["label"])
            self.node_map[event.uuid] = node["label"]

        return node_labels

    def _extract_system_messages(self, preprocessed_data: PreprocessedData) -> list[str]:
        """Extract system messages from preprocessed data.

        Args:
            preprocessed_data: The preprocessed session data

        Returns:
            List of system messages (limited to first 5)
        """
        system_messages = []

        # Extract from events
        for event in preprocessed_data.processed_events:
            if event.is_system_event() and event.content.text:
                system_messages.append(event.content.text)

        # Also check conversation context
        if "system_messages" in preprocessed_data.conversation_context:
            additional_messages = preprocessed_data.conversation_context["system_messages"]
            if isinstance(additional_messages, list):
                system_messages.extend(additional_messages)

        return system_messages[:5]  # Limit to first 5 messages

    def get_node_map(self) -> dict[str, str]:
        """Get the mapping of event UUIDs to node labels.

        Returns:
            Dictionary mapping event UUIDs to their corresponding node labels
        """
        return self.node_map.copy()
