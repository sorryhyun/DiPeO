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

    # Guard against duplicate registration
    if not registry.has(CONVERSATION_REPOSITORY):
        registry.register(CONVERSATION_REPOSITORY, create_conversation_repository)
    else:
        logger.debug("CONVERSATION_REPOSITORY already registered, skipping")

    from dipeo.infrastructure.repositories.conversation import InMemoryPersonRepository

    def create_person_repository() -> InMemoryPersonRepository:
        return InMemoryPersonRepository()

    # Guard against duplicate registration
    if not registry.has(PERSON_REPOSITORY):
        registry.register(PERSON_REPOSITORY, create_person_repository)
    else:
        logger.debug("PERSON_REPOSITORY already registered, skipping")

    from dipeo.application.conversation.use_cases import ManageConversationUseCase

    def create_manage_conversation_use_case() -> ManageConversationUseCase:
        conversation_repo = registry.resolve(CONVERSATION_REPOSITORY)
        return ManageConversationUseCase(conversation_repository=conversation_repo)

    # Guard against duplicate registration
    if not registry.has(MANAGE_CONVERSATION_USE_CASE):
        registry.register(MANAGE_CONVERSATION_USE_CASE, create_manage_conversation_use_case)
    else:
        logger.debug("MANAGE_CONVERSATION_USE_CASE already registered, skipping")
