"""Backward compatibility adapter for conversation services."""

from typing import Any

from dipeo.application.services.conversation import ConversationMemoryService


def create_conversation_service(memory_service: Any, conversation_manager: Any | None = None) -> ConversationMemoryService:
    """Factory function to create appropriate conversation service.
    
    This function provides backward compatibility by:
    1. If conversation_manager is provided, returns the enhanced V2 service
    2. Otherwise, returns the legacy ConversationMemoryService
    
    Args:
        memory_service: The underlying memory service
        conversation_manager: Optional conversation manager
        
    Returns:
        Either ConversationMemoryService or ConversationMemoryServiceV2
    """
    if conversation_manager is not None:
        from .memory_service_v2 import ConversationMemoryServiceV2
        return ConversationMemoryServiceV2(memory_service, conversation_manager)
    else:
        return ConversationMemoryService(memory_service)


def upgrade_conversation_service(
    existing_service: ConversationMemoryService,
    conversation_manager: Any
) -> Any:
    """Upgrade an existing ConversationMemoryService to V2.
    
    This allows gradual migration of existing code.
    
    Args:
        existing_service: The existing conversation service
        conversation_manager: The conversation manager to use
        
    Returns:
        ConversationMemoryServiceV2 instance
    """
    from .memory_service_v2 import ConversationMemoryServiceV2
    
    # Extract the memory service from the existing service
    memory_service = existing_service.memory_service
    
    # Create V2 service
    v2_service = ConversationMemoryServiceV2(memory_service, conversation_manager)
    
    # Transfer current execution ID if set
    if hasattr(existing_service, 'current_execution_id'):
        v2_service.current_execution_id = existing_service.current_execution_id
    
    return v2_service


class ConversationServiceAdapter:
    """Adapter that makes ConversationManager look like a conversation service.
    
    This adapter allows code expecting a conversation service to work with
    the new ConversationManager protocol.
    """
    
    def __init__(self, conversation_manager: Any):
        """Initialize with a ConversationManager."""
        self.conversation_manager = conversation_manager
        self.current_execution_id: str | None = None
    
    def add_message(self, person_id: str, role: str, content: str) -> None:
        """Add message using ConversationManager."""
        from datetime import datetime

        from dipeo.models import Message, PersonID
        
        # Convert role-based message to Message object
        if role == "system":
            from_person_id = "system"
            to_person_id = PersonID(person_id)
            message_type = "system_to_person"
        elif role == "assistant":
            from_person_id = PersonID(person_id)
            to_person_id = "system"
            message_type = "person_to_system"
        else:  # user
            from_person_id = "system"
            to_person_id = PersonID(person_id)
            message_type = "system_to_person"
        
        message = Message(
            from_person_id=from_person_id,
            to_person_id=to_person_id,
            content=content,
            message_type=message_type,
            timestamp=datetime.utcnow().isoformat()
        )
        
        self.conversation_manager.add_message(
            person_id=person_id,
            message=message,
            execution_id=self.current_execution_id or "",
            node_id=None
        )
    
    def get_messages(self, person_id: str) -> list[dict[str, str]]:
        """Get messages from ConversationManager."""
        conversation = self.conversation_manager.get_conversation(person_id)
        messages = []
        
        for msg in conversation.messages:
            # Convert to role-based format
            if msg.from_person_id == person_id:
                role = "assistant"
            elif msg.from_person_id == "system":
                role = "system"
            else:
                role = "user"
            
            messages.append({
                "role": role,
                "content": msg.content
            })
        
        return messages
    
    def forget_for_person(self, person_id: str, execution_id: str | None = None) -> None:
        """Clear conversation using ConversationManager."""
        self.conversation_manager.clear_conversation(
            person_id=person_id,
            execution_id=execution_id or self.current_execution_id
        )
    
    def get_messages_with_person_id(
        self, 
        person_id: str, 
        forget_mode: str | None = None
    ) -> list[dict[str, Any]]:
        """Get messages with person_id attached."""
        messages = self.get_messages(person_id)
        
        # Add person_id to each message
        return [
            {**msg, "person_id": person_id}
            for msg in messages
        ]


# Migration utilities

def is_using_legacy_conversation_service(service: Any) -> bool:
    """Check if a service is using the legacy ConversationMemoryService.
    
    Args:
        service: The service to check
        
    Returns:
        True if it's the legacy service, False if it's V2 or ConversationManager
    """
    from .memory_service import ConversationMemoryService
    from .memory_service_v2 import ConversationMemoryServiceV2
    
    return (
        isinstance(service, ConversationMemoryService) and
        not isinstance(service, ConversationMemoryServiceV2)
    )


def migrate_to_conversation_manager(container: Any) -> None:
    """Helper to migrate a dependency injection container to use ConversationManager.
    
    This function updates the container's conversation_service to use the V2
    implementation with ConversationManager.
    
    Args:
        container: The dependency injection container
    """
    if hasattr(container, 'conversation_service') and hasattr(container, 'conversation_manager'):
        # Get existing services
        memory_service = container.memory_service()
        conversation_manager = container.conversation_manager()
        
        # Override conversation service with V2
        from .memory_service_v2 import ConversationMemoryServiceV2
        container.conversation_service.override(
            lambda: ConversationMemoryServiceV2(memory_service, conversation_manager)
        )