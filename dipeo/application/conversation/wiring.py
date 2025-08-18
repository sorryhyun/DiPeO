"""Wiring module for conversation bounded context."""

import logging
from typing import TYPE_CHECKING

from dipeo.application.registry.service_registry import ServiceRegistry, ServiceKey

if TYPE_CHECKING:
    from dipeo.domain.conversation import PersonManager, ConversationManager
    from dipeo.infrastructure.conversation.adapters.in_memory import InMemoryConversationRepository
    from dipeo.infrastructure.conversation.adapters.in_memory_person import InMemoryPersonRepository
    from dipeo.application.conversation.use_cases import ManageConversationUseCase, UpdateMemoryUseCase

logger = logging.getLogger(__name__)

# Define service keys for conversation context
CONVERSATION_REPOSITORY_KEY = ServiceKey["InMemoryConversationRepository"]("conversation.repository")
PERSON_REPOSITORY_KEY = ServiceKey["InMemoryPersonRepository"]("person.repository")
CONVERSATION_MANAGER_KEY = ServiceKey["ConversationManager"]("conversation.manager")
PERSON_MANAGER_KEY = ServiceKey["PersonManager"]("conversation.person_manager")
MANAGE_CONVERSATION_USE_CASE = ServiceKey["ManageConversationUseCase"]("conversation.use_case.manage")
UPDATE_MEMORY_USE_CASE = ServiceKey["UpdateMemoryUseCase"]("conversation.use_case.update_memory")


def wire_conversation(registry: ServiceRegistry) -> None:
    """Wire conversation bounded context services and use cases.
    
    This includes:
    - Person manager
    - Conversation manager
    - Conversation repository
    - Person repository
    """
    logger.info("🔧 Wiring conversation bounded context")
    
    # Wire conversation repository (from infrastructure)
    from dipeo.infrastructure.conversation.adapters.in_memory import InMemoryConversationRepository
    
    def create_conversation_repository() -> InMemoryConversationRepository:
        """Factory for conversation repository."""
        return InMemoryConversationRepository()
    
    registry.register(CONVERSATION_REPOSITORY_KEY, create_conversation_repository)
    
    # Wire person repository (from infrastructure)
    from dipeo.infrastructure.conversation.adapters.in_memory_person import InMemoryPersonRepository
    
    def create_person_repository() -> InMemoryPersonRepository:
        """Factory for person repository."""
        return InMemoryPersonRepository()
    
    registry.register(PERSON_REPOSITORY_KEY, create_person_repository)
    
    # Wire person manager (from domain)
    from dipeo.domain.conversation import PersonManager
    from dipeo.application.registry.registry_tokens import PERSON_MANAGER
    
    def create_person_manager() -> PersonManager:
        """Factory for person manager."""
        person_repo = registry.resolve(PERSON_REPOSITORY_KEY)
        return PersonManager(person_repository=person_repo)
    
    registry.register(PERSON_MANAGER, create_person_manager)
    registry.register(PERSON_MANAGER_KEY, create_person_manager)
    
    # Wire conversation manager (from domain)
    from dipeo.domain.conversation import ConversationManager
    from dipeo.application.registry.registry_tokens import CONVERSATION_MANAGER
    
    def create_conversation_manager() -> ConversationManager:
        """Factory for conversation manager."""
        conversation_repo = registry.resolve(CONVERSATION_REPOSITORY_KEY)
        person_repo = registry.resolve(PERSON_REPOSITORY_KEY)
        return ConversationManager(
            conversation_repository=conversation_repo,
            person_repository=person_repo
        )
    
    registry.register(CONVERSATION_MANAGER, create_conversation_manager)
    registry.register(CONVERSATION_MANAGER_KEY, create_conversation_manager)
    
    # Wire manage conversation use case
    from dipeo.application.conversation.use_cases import ManageConversationUseCase
    
    def create_manage_conversation_use_case() -> ManageConversationUseCase:
        """Factory for manage conversation use case."""
        conversation_repo = registry.resolve(CONVERSATION_REPOSITORY_KEY)
        conversation_manager = registry.resolve(CONVERSATION_MANAGER_KEY)
        return ManageConversationUseCase(
            conversation_repository=conversation_repo,
            conversation_manager=conversation_manager
        )
    
    registry.register(MANAGE_CONVERSATION_USE_CASE, create_manage_conversation_use_case)
    
    # Wire update memory use case
    from dipeo.application.conversation.use_cases import UpdateMemoryUseCase
    
    def create_update_memory_use_case() -> UpdateMemoryUseCase:
        """Factory for update memory use case."""
        person_repo = registry.resolve(PERSON_REPOSITORY_KEY)
        person_manager = registry.resolve(PERSON_MANAGER_KEY)
        return UpdateMemoryUseCase(
            person_repository=person_repo,
            person_manager=person_manager
        )
    
    registry.register(UPDATE_MEMORY_USE_CASE, create_update_memory_use_case)
    
    logger.info("✅ Conversation bounded context wired")