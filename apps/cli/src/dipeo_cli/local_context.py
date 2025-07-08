"""Local application context for CLI execution."""

import logging
from typing import Any

from dipeo.container import Container, init_resources
from dipeo.container.adapters import AppContextAdapter
from dipeo.core import (
    SupportsAPIKey,
    SupportsDiagram,
    SupportsExecution,
    SupportsFile,
    SupportsLLM,
    SupportsMemory,
    SupportsNotion,
)

logger = logging.getLogger(__name__)


class LocalAppContext:
    """Application context for CLI local execution using the DI container."""

    def __init__(self):
        # Create container and adapter
        self._container = Container()
        self._adapter = AppContextAdapter(self._container)

    def __getattr__(self, name: str) -> Any:
        """Delegate all attribute access to the adapter."""
        return getattr(self._adapter, name)

    async def initialize_for_local(self):
        """Initialize container services for local execution."""
        # Initialize all container resources
        await init_resources(self._container)

        # Initialize execution service specifically for local mode
        # Local execution will use the LocalExecutionService which creates
        # its own service registry from this context

        logger.info("Local context initialized using DI container")
