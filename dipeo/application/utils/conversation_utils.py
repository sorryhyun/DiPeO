"""Utility methods for conversation handling."""

from typing import Any
from dipeo.core.utils import is_conversation as core_is_conversation, has_nested_conversation as core_has_nested_conversation, contains_conversation as core_contains_conversation


class InputDetector:
    """Simplified input detection utilities."""
    
    @staticmethod
    def is_conversation(value: Any) -> bool:
        """Check if value is a conversation (list of messages)."""
        return core_is_conversation(value)
    
    @staticmethod
    def has_nested_conversation(inputs: dict[str, Any]) -> bool:
        """Check if inputs contain nested conversation structures."""
        for key, value in inputs.items():
            # Direct conversation
            if InputDetector.is_conversation(value):
                return True
                
            # Single-nested
            if isinstance(value, dict) and 'default' in value:
                nested = value['default']
                if InputDetector.is_conversation(nested):
                    return True
                
                # Double-nested
                if isinstance(nested, dict) and 'default' in nested:
                    double_nested = nested['default']
                    if InputDetector.is_conversation(double_nested):
                        return True
        
        return False
    
    @staticmethod
    def contains_conversation(inputs: dict[str, Any]) -> bool:
        """Check if the inputs contain any conversation data."""
        return core_contains_conversation(inputs)


class MessageBuilder:
    """Builder pattern for cleaner message handling."""
    
    def __init__(self, conversation_service: Any, person_id: str, execution_id: str):
        self.service = conversation_service
        self.person_id = person_id
        self.execution_id = execution_id
    
    def add(self, role: str, content: str) -> 'MessageBuilder':
        """Add a message and return self for chaining."""
        self.service.add_message_to_conversation(
            person_id=self.person_id,
            execution_id=self.execution_id,
            role=role,
            content=content,
            current_person_id=self.person_id
        )
        return self
    
    def user(self, content: str) -> 'MessageBuilder':
        """Add user message."""
        return self.add("user", content)
    
    def assistant(self, content: str) -> 'MessageBuilder':
        """Add assistant message."""
        return self.add("assistant", content)
    
    def external(self, key: str, value: str) -> 'MessageBuilder':
        """Add external input message."""
        return self.add("external", f"[Input from {key}]: {value}")
    
    def developer(self, prompt: str) -> 'MessageBuilder':
        """Add developer prompt."""
        return self.add("user", f"[developer]: {prompt}")