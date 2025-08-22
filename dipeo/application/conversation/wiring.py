"""Wiring module for conversation bounded context."""

import logging
from typing import TYPE_CHECKING

from dipeo.application.registry.service_registry import ServiceRegistry, ServiceKey

if TYPE_CHECKING:
    from dipeo.infrastructure.repositories.conversation import InMemoryConversationRepository
    from dipeo.infrastructure.repositories.conversation import InMemoryPersonRepository
    from dipeo.application.conversation.use_cases import ManageConversationUseCase

logger = logging.getLogger(__name__)

# Define service keys for conversation context
CONVERSATION_REPOSITORY_KEY = ServiceKey["InMemoryConversationRepository"]("conversation.repository")
PERSON_REPOSITORY_KEY = ServiceKey["InMemoryPersonRepository"]("person.repository")
MANAGE_CONVERSATION_USE_CASE = ServiceKey["ManageConversationUseCase"]("conversation.use_case.manage")


def wire_conversation(registry: ServiceRegistry) -> None:
    """Wire conversation bounded context services and use cases.
    
    This includes:
    - Conversation repository
    - Person repository
    - Use cases for conversation and memory management
    """
    # Wire conversation repository (from infrastructure)
    from dipeo.infrastructure.repositories.conversation import InMemoryConversationRepository
    
    def create_conversation_repository() -> InMemoryConversationRepository:
        """Factory for conversation repository."""
        return InMemoryConversationRepository()
    
    registry.register(CONVERSATION_REPOSITORY_KEY, create_conversation_repository)
    
    # Wire person repository (from infrastructure)
    from dipeo.infrastructure.repositories.conversation import InMemoryPersonRepository
    
    def create_person_repository() -> InMemoryPersonRepository:
        """Factory for person repository."""
        return InMemoryPersonRepository()
    
    registry.register(PERSON_REPOSITORY_KEY, create_person_repository)
    
    # Wire manage conversation use case
    from dipeo.application.conversation.use_cases import ManageConversationUseCase
    
    def create_manage_conversation_use_case() -> ManageConversationUseCase:
        """Factory for manage conversation use case."""
        conversation_repo = registry.resolve(CONVERSATION_REPOSITORY_KEY)
        return ManageConversationUseCase(
            conversation_repository=conversation_repo
        )
    
    registry.register(MANAGE_CONVERSATION_USE_CASE, create_manage_conversation_use_case)
    
