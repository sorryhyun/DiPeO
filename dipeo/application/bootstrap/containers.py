"""2-container architecture:
- InfrastructureContainer: External adapters (storage, LLM, etc.)
- ApplicationContainer: Use cases and orchestration (includes domain services)
"""

from .infrastructure_container import InfrastructureContainer
from .application_container import ApplicationContainer

from typing import Any

from dipeo.application.registry import ServiceRegistry, ServiceKey
from dipeo.application.registry.keys import (
    API_KEY_SERVICE,
)
from dipeo.core.bak.config import Config

class Container:
    """Main container orchestrating the 2-container architecture."""
    
    def __init__(self, config: Config | None = None):
        self.config = config or Config.from_env()
        self.registry = ServiceRegistry()
        
        # Infrastructure must be initialized before Application
        # as Application depends on infrastructure services
        self.infrastructure = InfrastructureContainer(self.registry, self.config)
        self.application = ApplicationContainer(self.registry)
    
    def get_service(self, key: str | ServiceKey) -> Any:
        if isinstance(key, str):
            service_key = ServiceKey(key)
        else:
            service_key = key
        return self.registry.resolve(service_key)
    
    async def initialize(self):
        api_key_service = self.registry.resolve(API_KEY_SERVICE)
        if api_key_service and hasattr(api_key_service, 'initialize'):
            await api_key_service.initialize()
        
        from dipeo.application.registry.registry_tokens import DIAGRAM_COMPILER
        compiler = self.registry.resolve(DIAGRAM_COMPILER)
        if compiler and hasattr(compiler, 'initialize'):
            await compiler.initialize()
        
        from dipeo.application.registry.registry_tokens import DIAGRAM_SERIALIZER
        diagram_serializer = self.registry.resolve(DIAGRAM_SERIALIZER)
        if diagram_serializer and hasattr(diagram_serializer, 'initialize'):
            await diagram_serializer.initialize()
        
        from dipeo.application.registry.keys import DIAGRAM_SERVICE
        diagram_service = self.registry.resolve(DIAGRAM_SERVICE)
        if diagram_service and hasattr(diagram_service, 'initialize'):
            await diagram_service.initialize()
    
    async def shutdown(self):
        pass
    
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