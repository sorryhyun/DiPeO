"""Migration adapter to transition from UnifiedServiceRegistry to new ServiceRegistry."""

from typing import Any, Optional

from dipeo.application.unified_service_registry import UnifiedServiceRegistry
from .service_registry import ServiceRegistry, ServiceKey


class MigrationServiceRegistry(UnifiedServiceRegistry):
    """Adapter that wraps the new ServiceRegistry to provide backward compatibility.
    
    This allows existing code using UnifiedServiceRegistry to work with the new
    ServiceRegistry implementation during the migration period.
    """
    
    def __init__(self, parent: Optional["MigrationServiceRegistry"] = None, **services):
        # Initialize the UnifiedServiceRegistry part
        super().__init__(parent=parent, **services)
        
        # Create internal new registry
        self._new_registry = ServiceRegistry()
        
        # Register initial services in new registry
        for name, service in services.items():
            key = type("ServiceKey", (), {"name": name})()
            self._new_registry.register(key, service)
    
    def register(self, name: str, service: Any) -> None:
        """Register a service in both registries."""
        # Register in old registry
        super().register(name, service)
        
        # Register in new registry
        key = type("ServiceKey", (), {"name": name})()
        self._new_registry.register(key, service)
    
    def register_typed(self, key: ServiceKey[Any], service: Any) -> None:
        """Register a service with a typed key (new API)."""
        # Register in both registries
        self.register(key.name, service)
    
    def get_new_registry(self) -> ServiceRegistry:
        """Get the underlying new registry for migration."""
        return self._new_registry
    
    def migrate_to_new_registry(self) -> ServiceRegistry:
        """Migrate all services to a new ServiceRegistry instance."""
        new_registry = ServiceRegistry()
        
        # Migrate all services from the old registry
        all_services = self.get_all_services()
        for name, service in all_services.items():
            key = type("ServiceKey", (), {"name": name})()
            new_registry.register(key, service)
        
        return new_registry


def create_unified_service_registry_from_dependencies(
    static, business, dynamic, persistence, integration
) -> MigrationServiceRegistry:
    """Factory for MigrationServiceRegistry using automatic service discovery.
    
    This is a drop-in replacement for the existing factory function that
    creates a migration-compatible registry.
    """
    import logging
    
    logger = logging.getLogger(__name__)
    registry = MigrationServiceRegistry()
    
    # Define container mappings with their service configurations
    container_configs = {
        "persistence": {
            "container": persistence,
            "services": [
                "state_store",
                "message_router",
                "file_service",
                "api_key_service",
                "diagram_storage_service",
                "diagram_storage_adapter",
                "diagram_loader",
                "db_operations_service",
            ],
            "aliases": {
                "file": "file_service",  # Legacy alias
                "apikey_service": "api_key_service",  # GraphQL expects this name
            }
        },
        "integration": {
            "container": integration,
            "services": [
                "llm_service",
                "api_service",
                "notion_service",
                "integrated_diagram_service",
                "typescript_parser",
            ],
            "optional_services": [
                "api_integration_service",
                "code_execution_service",
            ]
        },
        "business": {
            "container": business,
            "services": [
                "condition_evaluator",
                "api_business_logic",
                "file_business_logic",
                "diagram_business_logic",
                "db_validator",
                "validation_service",
                "prompt_builder",
            ],
            "aliases": {
                "condition_evaluation_service": "condition_evaluator",
                "file_domain_service": "file_business_logic",
            }
        },
        "static": {
            "container": static,
            "services": [
                "diagram_validator",
                "diagram_compiler",
                "template_processor",
            ],
            "aliases": {
                "template_service": "template_processor",
                "template": "template_processor",  # Legacy alias
            }
        },
        "dynamic": {
            "container": dynamic,
            "services": [
                "conversation_manager",
                "person_manager",
            ],
            "optional_services": [
                "execution_flow_service",
            ],
            "aliases": {
                "conversation_service": "conversation_manager",
            }
        }
    }
    
    # Register services from each container
    for container_name, config in container_configs.items():
        container = config["container"]
        if not container:
            continue
            
        try:
            # Register required services
            for service_name in config.get("services", []):
                if hasattr(container, service_name):
                    service = getattr(container, service_name)()
                    registry.register(service_name, service)
            
            # Register optional services
            for service_name in config.get("optional_services", []):
                if hasattr(container, service_name):
                    service = getattr(container, service_name)()
                    registry.register(service_name, service)
            
            # Register aliases
            for alias, target in config.get("aliases", {}).items():
                if hasattr(container, target):
                    service = getattr(container, target)()
                    registry.register(alias, service)

        except Exception as e:
            logger.error(f"Failed to register {container_name} services: {e}")
    
    return registry