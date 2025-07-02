"""Re-export domains from dipeo_domain package.

This module exists for backward compatibility. All domain logic has been moved to
the dipeo_domain package to follow clean architecture principles.
"""

# Re-export everything from dipeo_domain.domains
from dipeo_domain.domains import *  # noqa: F403
from dipeo_domain.domains import (
    api,
    apikey,
    conversation,
    db,
    diagram,
    execution,
    file,
    ports,
    text,
    validation,
)

__all__ = [
    "api",
    "apikey",
    "conversation",
    "db",
    "diagram",
    "execution",
    "file",
    "ports",
    "text",
    "validation",
]
