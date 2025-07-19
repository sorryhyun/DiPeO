"""Service for processing conversation inputs in PersonJob handler."""

import logging
from typing import Any, Dict, List, Optional

from dipeo.models import Message
from dipeo.core.dynamic import Person

logger = logging.getLogger(__name__)


class ConversationProcessor:
    """Handles conversation input detection and rebuilding for PersonJob execution."""
    
    # Marker to identify preprocessed conversation content
    CONVERSATION_MARKER = "[Previous conversation"
    
    @classmethod
    def has_conversation_input(cls, inputs: Dict[str, Any]) -> bool:
        """
        Check if the inputs contain conversation data.
        
        Args:
            inputs: Input dictionary from node execution
            
        Returns:
            True if conversation inputs are detected
        """
        for key, value in inputs.items():
            # Check if key ends with _messages (prompt builder pattern)
            if key.endswith('_messages') and isinstance(value, list):
                return True
            # Check legacy structure for backwards compatibility
            if isinstance(value, dict) and "messages" in value:
                return True
        return False
    
    @classmethod
    def rebuild_conversation(
        cls,
        person: Person,
        inputs: Dict[str, Any]
    ) -> None:
        """
        Rebuild conversation history from inputs.
        
        Args:
            person: Person instance to rebuild conversation for
            inputs: Input dictionary containing conversation data
        """
        all_messages = cls._extract_messages(inputs)
        
        if not all_messages:
            logger.debug("rebuild_conversation: No messages found in inputs")
            return
        
        logger.debug(f"rebuild_conversation: Processing {len(all_messages)} total messages")
        
        for i, msg in enumerate(all_messages):
            message = cls._convert_to_message(msg, person.id)
            if message and not cls._should_skip_message(message):
                person.add_message(message)
                logger.debug(
                    f"  Added message {i}: from={message.from_person_id}, "
                    f"to={message.to_person_id}, content_length={len(message.content)}"
                )
    
    @classmethod
    def _extract_messages(cls, inputs: Dict[str, Any]) -> List[Any]:
        """Extract all messages from various input formats."""
        all_messages = []
        
        for key, value in inputs.items():
            # Handle _messages pattern
            if key.endswith('_messages') and isinstance(value, list):
                all_messages.extend(value)
            # Handle legacy dict structure
            elif isinstance(value, dict) and "messages" in value:
                messages = value["messages"]
                if isinstance(messages, list):
                    all_messages.extend(messages)
        
        return all_messages
    
    @classmethod
    def _convert_to_message(
        cls,
        msg: Any,
        default_person_id: str
    ) -> Optional[Message]:
        """Convert various message formats to Message object."""
        # Already a Message object
        if isinstance(msg, Message):
            return msg
        
        # Dictionary format
        if isinstance(msg, dict):
            content = msg.get("content", "")
            
            # Skip messages with conversation marker
            if cls._contains_conversation_marker(content):
                return None
            
            return Message(
                from_person_id=msg.get("from_person_id", default_person_id),
                to_person_id=msg.get("to_person_id", default_person_id),
                content=content,
                message_type=msg.get("message_type", "person_to_person"),
                timestamp=msg.get("timestamp"),
            )
        
        logger.warning(f"Unknown message format: {type(msg)}")
        return None
    
    @classmethod
    def _should_skip_message(cls, message: Message) -> bool:
        """Check if a message should be skipped during rebuilding."""
        # Skip messages containing the conversation marker
        return cls._contains_conversation_marker(message.content)
    
    @classmethod
    def _contains_conversation_marker(cls, content: str) -> bool:
        """Check if content contains the conversation marker."""
        return cls.CONVERSATION_MARKER in content
    
    @classmethod
    def prepare_conversation_context(
        cls,
        person: Person,
        max_messages: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Prepare conversation context for prompt building.
        
        Args:
            person: Person instance
            max_messages: Maximum number of messages to include
            
        Returns:
            List of message dictionaries for prompt context
        """
        messages = person.get_messages()
        
        if max_messages and len(messages) > max_messages:
            messages = messages[-max_messages:]
        
        return [
            {
                "role": cls._get_message_role(msg, person.id),
                "content": msg.content,
                "from_person_id": msg.from_person_id,
                "to_person_id": msg.to_person_id,
            }
            for msg in messages
        ]
    
    @classmethod
    def _get_message_role(cls, message: Message, current_person_id: str) -> str:
        """Determine the role of a message relative to current person."""
        if message.from_person_id == current_person_id:
            return "assistant"
        else:
            return "user"