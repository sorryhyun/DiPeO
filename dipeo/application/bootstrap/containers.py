"""Simplified container system for DiPeO monorepo.

This module provides a clean 3-container architecture:
- CoreContainer: Immutable domain services (no external dependencies)
- InfrastructureContainer: External adapters (storage, LLM, etc.)
- ApplicationContainer: Use cases and orchestration
"""

from .core_container import CoreContainer
from .infrastructure_container import InfrastructureContainer
from .application_container import ApplicationContainer

from pathlib import Path
from typing import Any

from dipeo.application.registry import ServiceRegistry, ServiceKey
from dipeo.application.registry.keys import (
    API_KEY_SERVICE,
)

# Define additional service keys that aren't in the main registry yet
TEMPLATE_PROCESSOR = ServiceKey("template_processor")
NODE_REGISTRY = ServiceKey("node_registry")
DOMAIN_SERVICE_REGISTRY = ServiceKey("domain_service_registry")
FILESYSTEM_ADAPTER = ServiceKey("filesystem_adapter")
API_KEY_STORAGE = ServiceKey("api_key_storage")
from dipeo.core.config import Config

class Container:
    """Main container orchestrating the 3-container architecture.
    
    This simplified design removes profiles and complex initialization,
    making it easier to understand and maintain in a monorepo context.
    """
    
    def __init__(self, config: Config | None = None):
        # Use provided config or load from environment
        self.config = config or Config.from_env()
        
        # Single shared registry for all containers
        self.registry = ServiceRegistry()
        
        # Initialize containers in dependency order
        self.core = CoreContainer(self.registry)
        self.infrastructure = InfrastructureContainer(self.registry, self.config)
        self.application = ApplicationContainer(self.registry)
    
    def get_service(self, key: str | ServiceKey) -> Any:
        """Get a service by key from the registry.
        
        Args:
            key: Service key (string or ServiceKey object)
            
        Returns:
            The service instance
        """
        if isinstance(key, str):
            # Create a ServiceKey from string for backward compatibility
            service_key = ServiceKey(key)
        else:
            service_key = key
        return self.registry.resolve(service_key)
    
    async def initialize(self):
        """Initialize async resources if needed."""
        # Initialize APIKeyService to load keys from file
        api_key_service = self.registry.resolve(API_KEY_SERVICE)
        if api_key_service and hasattr(api_key_service, 'initialize'):
            await api_key_service.initialize()
        
        # Initialize CompilationService
        from dipeo.application.registry.keys import COMPILATION_SERVICE
        compilation_service = self.registry.resolve(COMPILATION_SERVICE)
        if compilation_service and hasattr(compilation_service, 'initialize'):
            await compilation_service.initialize()
        
        # Initialize DiagramConverterService
        from dipeo.application.registry.keys import DIAGRAM_CONVERTER
        diagram_converter = self.registry.resolve(DIAGRAM_CONVERTER)
        if diagram_converter and hasattr(diagram_converter, 'initialize'):
            await diagram_converter.initialize()
    
    async def shutdown(self):
        """Clean up resources on shutdown."""
        # Clean up any open connections, files, etc.
        pass
    
    def create_sub_container(self, execution_id: str) -> "Container":
        """Create a sub-container for isolated execution.
        
        In this simplified design:
        - Core services are always shared (immutable)
        - Infrastructure is shared (connection pooling)
        - Only execution context is isolated
        
        Args:
            execution_id: The execution ID for the sub-container (reserved for future use)
        """
        # For now, return self - can add isolation later if needed
        # The execution service handles its own state isolation
        return self


# Convenience functions for backward compatibility
async def init_resources(container: Container):
    """Initialize container resources."""
    await container.initialize()


async def shutdown_resources(container: Container):
    """Shutdown container resources."""
    await container.shutdown()