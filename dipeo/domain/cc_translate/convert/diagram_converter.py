"""Main diagram converter for Claude Code translation.

This module handles the conversion phase: transforming preprocessed session
data into DiPeO diagram structures with nodes, connections, and persons.
"""

from typing import Any

from dipeo.infrastructure.claude_code import ConversationTurn, SessionEvent

from ..preprocess import PreprocessedSession
from .connection_builder import ConnectionBuilder
from .diagram_assembler import DiagramAssembler
from .node_builders import NodeBuilder


class DiagramConverter:
    """Converts preprocessed session data into DiPeO diagram structures."""

    def __init__(self):
        """Initialize the diagram converter."""
        self.node_builder = NodeBuilder()
        self.connection_builder = ConnectionBuilder()
        self.assembler = DiagramAssembler()
        self.node_map: dict[str, str] = {}  # Maps event UUID to node label

    def convert(self, preprocessed_session: PreprocessedSession) -> dict[str, Any]:
        """
        Convert preprocessed session into a light format diagram.

        Args:
            preprocessed_session: The preprocessed session data

        Returns:
            Light format diagram dictionary
        """
        # Reset state for new conversion
        self._reset_state()

        # Create start node
        start_node_label = self._create_start_node(
            preprocessed_session.metadata["session_id"],
            preprocessed_session.metadata["initial_prompt"],
        )

        # Process conversation flow
        prev_node_label = start_node_label

        for turn in preprocessed_session.conversation_flow:
            # Create nodes for this conversation turn
            turn_node_labels = self._process_conversation_turn(
                turn, preprocessed_session.system_messages
            )

            # Connect to previous node
            self.connection_builder.connect_to_previous(prev_node_label, turn_node_labels)

            # Connect nodes within the turn
            self.connection_builder.connect_sequential_nodes(turn_node_labels)

            # Update previous node for next iteration
            if turn_node_labels:
                prev_node_label = turn_node_labels[-1]

        # Assemble the final diagram
        diagram = self.assembler.assemble_light_diagram(
            nodes=self.node_builder.nodes,
            connections=self.connection_builder.get_connections(),
            persons=self.node_builder.persons,
        )

        # Add processing metadata
        diagram = self.assembler.add_processing_metadata(
            diagram=diagram,
            preprocessing_report=preprocessed_session.pruning_report,
            conversion_stats=self._get_conversion_stats(),
        )

        return diagram

    def _reset_state(self) -> None:
        """Reset converter state for new conversion."""
        self.node_builder.reset()
        self.connection_builder.reset()
        self.node_map = {}

    def _create_start_node(self, session_id: str, initial_prompt: str) -> str:
        """Create the start node for the diagram."""
        node = self.node_builder.create_start_node(session_id, initial_prompt)
        return node["label"]

    def _process_conversation_turn(
        self, turn: ConversationTurn, system_messages: list[str]
    ) -> list[str]:
        """Process a conversation turn and create corresponding nodes."""
        node_labels = []

        # Skip user event if this turn has tool events (user event is just showing tool results)
        if turn.user_event and not turn.tool_events:
            user_node_label = self._create_user_node(turn.user_event)
            # Only add the user node if it has meaningful content
            if user_node_label:
                node_labels.append(user_node_label)

        # Process assistant response and tool events
        if turn.assistant_event:
            # Check if there are tool events in this turn
            if turn.tool_events:
                # Create tool nodes for each tool use
                for tool_event in turn.tool_events:
                    tool_node_labels = self._create_tool_nodes(tool_event)
                    node_labels.extend(tool_node_labels)
            else:
                # Create person job node for AI response
                assistant_node_label = self._create_assistant_node(
                    turn.assistant_event, system_messages
                )
                node_labels.append(assistant_node_label)

        return node_labels

    def _create_user_node(self, event: SessionEvent) -> str | None:
        """Create a node for user input, or None if no meaningful input."""
        node = self.node_builder.create_user_node(
            self.node_builder.text_processor.extract_text_content(
                event.message.get("content", ""), skip_read_results=True
            )
        )
        if node:
            self.node_map[event.uuid] = node["label"]
            return node["label"]
        return None

    def _create_assistant_node(self, event: SessionEvent, system_messages: list[str]) -> str:
        """Create a node for AI assistant response."""
        content = self.node_builder.text_processor.extract_text_content(
            event.message.get("content", ""), skip_read_results=True
        )

        node = self.node_builder.create_assistant_node(content, system_messages)
        self.node_map[event.uuid] = node["label"]
        return node["label"]

    def _create_tool_nodes(self, event: SessionEvent) -> list[str]:
        """Create nodes for tool usage."""
        node_labels = []

        tool_name = event.tool_name
        tool_input = event.tool_input or {}

        # Create appropriate node for the tool
        node = self.node_builder.create_tool_node(tool_name, tool_input, event.tool_use_result)

        if node:
            node_labels.append(node["label"])
            self.node_map[event.uuid] = node["label"]

        return node_labels

    def _get_conversion_stats(self) -> dict[str, Any]:
        """Get conversion statistics."""
        return {
            "total_nodes": len(self.node_builder.nodes),
            "total_connections": len(self.connection_builder.get_connections()),
            "total_persons": len(self.node_builder.persons),
            "node_types": self._count_node_types(),
        }

    def _count_node_types(self) -> dict[str, int]:
        """Count nodes by type."""
        type_counts = {}
        for node in self.node_builder.nodes:
            node_type = node.get("type", "unknown")
            type_counts[node_type] = type_counts.get(node_type, 0) + 1
        return type_counts
