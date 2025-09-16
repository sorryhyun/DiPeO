import logging

from dipeo.application.registry.enhanced_service_registry import EnhancedServiceRegistry
from dipeo.config import AppSettings

logger = logging.getLogger(__name__)


class InfrastructureContainer:
    """External integration adapters.

    Contains all I/O operations, external service integrations,
    and infrastructure concerns. Configured based on environment.

    Note: All service registration is now handled by bootstrap_services() in wiring.py
    This container only holds references to registry and config for compatibility.
    """

    def __init__(self, registry: EnhancedServiceRegistry, config: AppSettings):
        self.registry = registry
        self.config = config
        # Services are set up by bootstrap_services() in wiring.py
