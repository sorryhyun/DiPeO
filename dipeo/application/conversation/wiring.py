"""Wiring module for conversation bounded context."""

import logging
from typing import TYPE_CHECKING

from dipeo.application.registry.enhanced_service_registry import (
    EnhancedServiceRegistry as ServiceRegistry,
)
from dipeo.application.registry.keys import (
    CONVERSATION_REPOSITORY,
    MANAGE_CONVERSATION_USE_CASE,
    PERSON_REPOSITORY,
)

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)


def wire_conversation(registry: ServiceRegistry) -> None:
    """Wire conversation bounded context services and use cases."""
    from dipeo.infrastructure.repositories.conversation import InMemoryConversationRepository

    def create_conversation_repository() -> InMemoryConversationRepository:
        return InMemoryConversationRepository()

    registry.register(CONVERSATION_REPOSITORY, create_conversation_repository)

    from dipeo.infrastructure.repositories.conversation import InMemoryPersonRepository

    def create_person_repository() -> InMemoryPersonRepository:
        return InMemoryPersonRepository()

    registry.register(PERSON_REPOSITORY, create_person_repository)

    from dipeo.application.conversation.use_cases import ManageConversationUseCase

    def create_manage_conversation_use_case() -> ManageConversationUseCase:
        conversation_repo = registry.resolve(CONVERSATION_REPOSITORY)
        return ManageConversationUseCase(conversation_repository=conversation_repo)

    registry.register(MANAGE_CONVERSATION_USE_CASE, create_manage_conversation_use_case)
