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

        # Validate dependencies before initialization
        missing_dependencies = self.registry.validate_dependencies()
        if missing_dependencies:
            for missing_dep in missing_dependencies:
                logger.error(f"Missing dependency: {missing_dep}")
            if self.config.env == "production":
                raise RuntimeError(
                    f"Service dependency validation failed in production: {missing_dependencies}"
                )
            else:
                logger.warning("Continuing with missing dependencies in non-production environment")

        # Log audit trail and service statistics
        audit_trail = self.registry.get_audit_trail()
        logger.info(f"Registry initialized with {len(audit_trail)} service registrations")

        # Log services by type for monitoring
        by_type = {}
        for entry in audit_trail:
            # Get the service_type from the registry's _service_keys dict
            service_type = "UNKNOWN"
            if (
                hasattr(self.registry, "_service_keys")
                and entry.service_key in self.registry._service_keys
            ):
                key = self.registry._service_keys[entry.service_key]
                if hasattr(key, "service_type") and key.service_type:
                    service_type = (
                        key.service_type.value
                        if hasattr(key.service_type, "value")
                        else str(key.service_type)
                    )
            by_type[service_type] = by_type.get(service_type, 0) + 1

        for stype, count in sorted(by_type.items()):
            logger.info(f"  {stype}: {count} services")

        # Verify critical services are protected
        from dipeo.application.registry.keys import EVENT_BUS, STATE_STORE

        critical_services = [EVENT_BUS, STATE_STORE, API_KEY_SERVICE]
        for service_key in critical_services:
            if not self.registry.has(service_key):
                raise RuntimeError(f"Critical service missing: {service_key}")
            logger.debug(f"Critical service verified: {service_key}")

        for service_name in self.registry.list_services():
            try:
                service = self.registry.resolve(ServiceKey[Any](service_name))
                if isinstance(service, Lifecycle | InitializeOnly):
                    await service.initialize()
                    # logger.info(f"Initialized service: {service_name}")
            except Exception as e:
                logger.error(f"Failed to initialize service {service_name}: {e}")
                # Continue initializing other services even if one fails

        # Freeze registry after bootstrap to prevent accidental modifications
        if self.config.dependency_injection.freeze_after_boot or (
            self.config.dependency_injection.auto_freeze_in_production
            and self.config.env == "production"
        ):
            self.registry.freeze()
            logger.info("Registry frozen for production safety")

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


async def init_resources(container: Container):
    await container.initialize()


async def shutdown_resources(container: Container):
    await container.shutdown()
