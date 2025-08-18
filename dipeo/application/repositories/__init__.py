"""Repository implementations for domain entities.

DEPRECATED: Repositories have been moved to infrastructure layer.
Import from dipeo.infrastructure.conversation.adapters instead.
"""

import warnings

# Provide backward compatibility with deprecation warnings
from dipeo.infrastructure.conversation.adapters import (
    InMemoryConversationRepository,
    InMemoryPersonRepository,
)

warnings.warn(
    "Import repositories from dipeo.infrastructure.conversation.adapters instead of dipeo.application.repositories",
    DeprecationWarning,
    stacklevel=2
)

__all__ = [
    "InMemoryConversationRepository",
    "InMemoryPersonRepository",
]