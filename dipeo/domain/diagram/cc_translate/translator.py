"""Main translator for converting Claude Code sessions into DiPeO diagrams."""

from typing import Any, Optional

from dipeo.infrastructure.claude_code import ClaudeCodeSession, ConversationTurn, SessionEvent

from .node_builders import NodeBuilder
from .text_utils import TextProcessor


class ClaudeCodeTranslator:
    """Translates Claude Code sessions into DiPeO light format diagrams."""

    def __init__(self) -> None:
        """Initialize the translator."""
        self.node_builder = NodeBuilder()
        self.text_processor = TextProcessor()
        self.nodes: list[dict[str, Any]] = []
        self.connections: list[dict[str, Any]] = []
        self.node_map: dict[str, str] = {}  # Maps event UUID to node label

    def translate(self, session: ClaudeCodeSession) -> dict[str, Any]:
        """
        Translate a Claude Code session into a light format diagram.

        Args:
            session: Parsed Claude Code session

        Returns:
            Light format diagram dictionary
        """
        # Reset state
        self._reset_state()

        # Create start node
        start_node_label = self._create_start_node(session)

        # Process conversation flow
        conversation_flow = session.get_conversation_flow()
        prev_node_label = start_node_label

        for turn in conversation_flow:
            # Create nodes for this conversation turn
            turn_node_labels = self._process_conversation_turn(turn)

            # Connect to previous node
            if turn_node_labels and prev_node_label:
                self._add_connection(prev_node_label, turn_node_labels[0])

            # Connect nodes within the turn
            for i in range(len(turn_node_labels) - 1):
                self._add_connection(turn_node_labels[i], turn_node_labels[i + 1])

            # Update previous node for next iteration
            if turn_node_labels:
                prev_node_label = turn_node_labels[-1]

        # Build light format diagram
        diagram = self._build_light_diagram()

        return diagram

    def _reset_state(self) -> None:
        """Reset translator state for new translation."""
        self.node_builder.reset()
        self.text_processor = TextProcessor()
        self.nodes = []
        self.connections = []
        self.node_map = {}

    def _create_start_node(self, session: ClaudeCodeSession) -> str:
        """Create the start node for the diagram."""
        # Extract first user message as the start trigger
        first_user_message = ""
        for event in session.events:
            if event.type == "user":
                if "content" in event.message:
                    first_user_message = self.text_processor.extract_text_content(
                        event.message["content"]
                    )
                    break

        # Get session ID
        session_id = session.session_id if hasattr(session, "session_id") else "unknown"

        # Create start node
        node = self.node_builder.create_start_node(session_id, first_user_message)
        self.nodes.append(node)
        return node["label"]

    def _process_conversation_turn(self, turn: ConversationTurn) -> list[str]:
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
                assistant_node_label = self._create_assistant_node(turn.assistant_event)
                node_labels.append(assistant_node_label)

        return node_labels

    def _create_user_node(self, event: SessionEvent) -> str | None:
        """Create a node for user input, or None if no meaningful input."""
        # Skip tool results in user messages - they flow through connections
        content = self.text_processor.extract_text_content(
            event.message.get("content", ""), skip_read_results=True
        )

        # Create user node
        node = self.node_builder.create_user_node(content)
        if node:
            self.nodes.append(node)
            self.node_map[event.uuid] = node["label"]
            return node["label"]
        return None

    def _create_assistant_node(self, event: SessionEvent) -> str:
        """Create a node for AI assistant response."""
        # Skip Read tool results in assistant responses - they flow through db node connections
        content = self.text_processor.extract_text_content(
            event.message.get("content", ""), skip_read_results=True
        )

        # Create assistant node
        node = self.node_builder.create_assistant_node(content)
        self.nodes.append(node)
        self.node_map[event.uuid] = node["label"]
        return node["label"]

    def _create_tool_nodes(self, event: SessionEvent) -> list[str]:
        """Create nodes for tool usage."""
        node_labels = []

        tool_name = event.tool_name
        tool_input = event.tool_input or {}

        # Create appropriate node for the tool
        node = self.node_builder.create_tool_node(tool_name, tool_input)

        if node:
            self.nodes.append(node)
            node_labels.append(node["label"])
            self.node_map[event.uuid] = node["label"]

        return node_labels

    def _add_connection(
        self, source: str, target: str, content_type: str = "raw_text", label: str = ""
    ) -> None:
        """Add a connection between two nodes in light format."""
        connection = {"from": source, "to": target, "content_type": content_type}
        if label:
            connection["label"] = label
        self.connections.append(connection)

    def _build_light_diagram(self) -> dict[str, Any]:
        """Build the light format diagram structure."""
        # Build the light format diagram
        diagram = {"version": "light"}

        # Add nodes
        if self.nodes:
            diagram["nodes"] = self.nodes

        # Add connections
        if self.connections:
            diagram["connections"] = self.connections

        # Add persons section if we have AI agents
        if self.node_builder.persons:
            diagram["persons"] = self.node_builder.persons

        return diagram
