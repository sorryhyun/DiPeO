"""Conversation handling utilities for PersonJob nodes."""

import logging
from typing import Any

from dipeo.diagram_generated.domain_models import Message

logger = logging.getLogger(__name__)


class ConversationHandler:
    """Handles conversation-related operations for PersonJob execution."""

    @staticmethod
    def has_conversation_input(inputs: dict[str, Any]) -> bool:
        """Check if inputs contain conversation data.

        Args:
            inputs: Input dictionary to check

        Returns:
            True if conversation inputs are present
        """
        for key, value in inputs.items():
            # Check if key ends with _messages (standard convention)
            if key.endswith("_messages") and isinstance(value, list):
                return True
            # Also check the original structure for backwards compatibility
            if isinstance(value, dict) and "messages" in value:
                return True
        return False

    @staticmethod
    def load_conversation_from_inputs(inputs: dict[str, Any], person_id: str) -> list[Message]:
        """Extract and process conversation messages from inputs.

        This method now returns messages to be added by the handler/orchestrator,
        instead of directly adding them to the person.

        Args:
            inputs: Input dictionary containing conversation data
            person_id: ID of the person for default attribution

        Returns:
            List of processed Message objects to be added to conversation
        """
        all_messages = ConversationHandler._extract_messages_from_inputs(inputs)

        if not all_messages:
            logger.debug("load_conversation_from_inputs: No messages found in inputs")
            return []

        logger.debug(
            f"load_conversation_from_inputs: Processing {len(all_messages)} total messages"
        )

        processed_messages = []
        for i, msg in enumerate(all_messages):
            processed_msg = ConversationHandler._process_message(msg, person_id)
            if processed_msg:
                processed_messages.append(processed_msg)
                logger.debug(
                    f"  Processed message {i}: from={processed_msg.from_person_id}, "
                    f"to={processed_msg.to_person_id}, content_length={len(processed_msg.content)}"
                )

        return processed_messages

    @staticmethod
    def _extract_messages_from_inputs(inputs: dict[str, Any]) -> list[Any]:
        """Extract all messages from various input formats.

        Args:
            inputs: Input dictionary

        Returns:
            List of message objects or dicts
        """
        all_messages = []

        for _key, value in inputs.items():
            if isinstance(value, dict) and "messages" in value:
                messages = value["messages"]
                if isinstance(messages, list):
                    all_messages.extend(messages)

        return all_messages

    @staticmethod
    def _process_message(msg: Any, default_person_id: str) -> Message | None:
        """Process a message from various formats into a Message object.

        Args:
            msg: Message in various formats (Message object or dict)
            default_person_id: Default person ID to use if not specified

        Returns:
            Processed Message object or None if should be skipped
        """
        # Handle Message objects
        if isinstance(msg, Message):
            # Skip messages with conversation markers to avoid duplication
            if "[Previous conversation" not in msg.content:
                return msg
            return None

        # Handle dictionary format
        if isinstance(msg, dict):
            content = msg.get("content", "")

            # Skip messages that contain the conversation marker
            if "[Previous conversation" in content:
                return None

            return Message(
                from_person_id=msg.get("from_person_id", default_person_id),
                to_person_id=msg.get("to_person_id", default_person_id),
                content=content,
                message_type="person_to_person",
                timestamp=msg.get("timestamp"),
            )

        return None

    @staticmethod
    def needs_conversation_output(node_id: str, diagram: Any) -> bool:
        """Check if node outputs need conversation data.

        Args:
            node_id: ID of the node to check
            diagram: Diagram containing edges

        Returns:
            True if any edge from this node expects conversation output
        """
        from dipeo.diagram_generated.enums import ContentType

        if not diagram or not hasattr(diagram, "get_outgoing_edges"):
            return False

        outgoing_edges = diagram.get_outgoing_edges(node_id)
        for edge in outgoing_edges:
            # Check for explicit conversation output
            if edge.source_output == "conversation":
                return True

            # NEW: Check edge content_type
            if (
                hasattr(edge, "content_type")
                and edge.content_type == ContentType.CONVERSATION_STATE
            ):
                return True

            # Check data_transform for content_type = conversation_state (backward compatibility)
            if (
                hasattr(edge, "data_transform")
                and edge.data_transform
                and edge.data_transform.get("content_type") == "conversation_state"
            ):
                return True
        return False
