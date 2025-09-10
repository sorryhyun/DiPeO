"""2-container architecture:
- InfrastructureContainer: External adapters (storage, LLM, etc.)
- ApplicationContainer: Use cases and orchestration (includes domain services)
"""

from typing import Any

from dipeo.application.registry import ServiceKey, ServiceRegistry
from dipeo.application.registry.keys import (
    API_KEY_SERVICE,
)
from dipeo.config import AppSettings, get_settings

from .application_container import ApplicationContainer
from .infrastructure_container import InfrastructureContainer


class Container:
    """Main container orchestrating the 2-container architecture."""

    def __init__(self, config: AppSettings | None = None):
        self.config = config or get_settings()
        self.registry = ServiceRegistry()

        # Infrastructure must be initialized before Application
        # as Application depends on infrastructure services
        self.infrastructure = InfrastructureContainer(self.registry, self.config)
        self.application = ApplicationContainer(self.registry)

    def get_service(self, key: str | ServiceKey) -> Any:
        service_key = ServiceKey(key) if isinstance(key, str) else key
        return self.registry.resolve(service_key)

    async def initialize(self):
        from .lifecycle import initialize_service

        api_key_service = self.registry.resolve(API_KEY_SERVICE)
        if api_key_service:
            await initialize_service(api_key_service)

        from dipeo.application.registry.keys import DIAGRAM_COMPILER

        compiler = self.registry.resolve(DIAGRAM_COMPILER)
        if compiler:
            await initialize_service(compiler)

        from dipeo.application.registry.keys import DIAGRAM_SERIALIZER

        diagram_serializer = self.registry.resolve(DIAGRAM_SERIALIZER)
        if diagram_serializer:
            await initialize_service(diagram_serializer)

        from dipeo.application.registry.keys import DIAGRAM_PORT

        diagram_service = self.registry.resolve(DIAGRAM_PORT)
        if diagram_service:
            await initialize_service(diagram_service)

    async def shutdown(self):
        """Shutdown resources including warm pools."""
        # Shutdown Claude Code warm pool if it's being used
        try:
            from dipeo.infrastructure.llm.providers.claude_code.transport.session_pool import (
                shutdown_global_session_manager,
            )

            await shutdown_global_session_manager()
        except ImportError:
            # Claude Code SDK not installed, skip
            pass
        except Exception as e:
            # Log error but don't fail shutdown
            import logging

            logger = logging.getLogger(__name__)
            logger.error(f"Error shutting down warm pool manager: {e}")

    def create_sub_container(self, execution_id: str) -> "Container":
        """Create a sub-container for isolated execution.

        Infrastructure services are shared (connection pooling),
        application services are shared, only execution context is isolated.
        """
        return self


async def init_resources(container: Container):
    await container.initialize()


async def shutdown_resources(container: Container):
    await container.shutdown()
