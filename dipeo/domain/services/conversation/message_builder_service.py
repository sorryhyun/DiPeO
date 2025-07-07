"""Domain service for building conversation messages."""

from typing import Any


class MessageBuilderService:
    """Service for building conversation messages with fluent interface."""
    
    def __init__(self, conversation_service: Any, person_id: str, execution_id: str):
        """Initialize the message builder.
        
        Args:
            conversation_service: Service for managing conversations
            person_id: ID of the person/agent
            execution_id: ID of the current execution
        """
        self.service = conversation_service
        self.person_id = person_id
        self.execution_id = execution_id
    
    def add(self, role: str, content: str) -> 'MessageBuilderService':
        """Add a message and return self for chaining.
        
        Business logic:
        - Adds message to conversation with proper attribution
        - Maintains execution context
        """
        self.service.add_message_to_conversation(
            person_id=self.person_id,
            execution_id=self.execution_id,
            role=role,
            content=content,
            current_person_id=self.person_id
        )
        return self
    
    def user(self, content: str) -> 'MessageBuilderService':
        """Add user message."""
        return self.add("user", content)
    
    def assistant(self, content: str) -> 'MessageBuilderService':
        """Add assistant message."""
        return self.add("assistant", content)
    
    def external(self, key: str, value: str) -> 'MessageBuilderService':
        """Add external input message with source attribution."""
        return self.add("external", f"[Input from {key}]: {value}")
    
    def developer(self, prompt: str) -> 'MessageBuilderService':
        """Add developer prompt with special formatting."""
        return self.add("user", f"[developer]: {prompt}")