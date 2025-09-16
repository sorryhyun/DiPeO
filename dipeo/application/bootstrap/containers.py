"""2-container architecture:
- InfrastructureContainer: External adapters (storage, LLM, etc.)
- ApplicationContainer: Use cases and orchestration (includes domain services)
"""

from typing import Any

from dipeo.application.registry import ServiceKey
from dipeo.application.registry.enhanced_service_registry import EnhancedServiceRegistry
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
        self.registry = EnhancedServiceRegistry()

        self.infrastructure = InfrastructureContainer(self.registry, self.config)
        self.application = ApplicationContainer(self.registry)

    def get_service(self, key: str | ServiceKey) -> Any:
        service_key = ServiceKey(key) if isinstance(key, str) else key
        return self.registry.resolve(service_key)

    async def initialize(self):
        """Initialize all services implementing Lifecycle protocol."""
        import logging

        from .lifecycle import InitializeOnly, Lifecycle

        logger = logging.getLogger(__name__)

        for service_name in self.registry.list_services():
            try:
                service = self.registry.resolve(ServiceKey[Any](service_name))
                if isinstance(service, Lifecycle | InitializeOnly):
                    await service.initialize()
                    logger.info(f"Initialized service: {service_name}")
            except Exception as e:
                logger.error(f"Failed to initialize service {service_name}: {e}")
                # Continue initializing other services even if one fails

        # Freeze registry after bootstrap to prevent accidental modifications
        if self.config.dependency_injection.freeze_after_boot or (
            self.config.dependency_injection.auto_freeze_in_production
            and self.config.env == "production"
        ):
            self.registry.freeze()

    async def shutdown(self):
        """Shutdown all services in reverse order."""
        import logging

        from .lifecycle import Lifecycle, ShutdownOnly

        logger = logging.getLogger(__name__)

        # Shutdown all services that implement lifecycle protocols in reverse order
        services = list(self.registry.list_services())
        for service_name in reversed(services):
            try:
                service = self.registry.resolve(ServiceKey[Any](service_name))
                if isinstance(service, Lifecycle | ShutdownOnly):
                    await service.shutdown()
                    logger.info(f"Shutdown service: {service_name}")
            except Exception as e:
                logger.error(f"Error shutting down {service_name}: {e}")

        # Shutdown warm pools (specific legacy cleanup)
        try:
            from dipeo.infrastructure.llm.providers.claude_code.transport.session_pool import (
                shutdown_global_session_manager,
            )

            await shutdown_global_session_manager()
        except ImportError:
            pass
        except Exception as e:
            logger.error(f"Error shutting down warm pool manager: {e}")

    def create_sub_container(self, execution_id: str) -> "Container":
        """Create a sub-container for isolated execution.

        Infrastructure services are shared, only execution context is isolated.
        """
        return self


async def init_resources(container: Container):
    await container.initialize()


async def shutdown_resources(container: Container):
    await container.shutdown()
