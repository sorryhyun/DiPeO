"""Main dependency injection container for DiPeO."""

import os
from pathlib import Path
from dependency_injector import containers, providers

from .infrastructure_container import InfrastructureContainer
from .domain_container import DomainContainer
from .application_container import ApplicationContainer
from .utilities import (
    get_project_base_dir,
    init_resources,
    shutdown_resources,
    validate_protocol_compliance,
)

# Import new containers
from .core.static_container import StaticServicesContainer
from .core.business_container import BusinessLogicContainer
from .runtime.dynamic_container import DynamicServicesContainer
from .runtime.persistence_container import PersistenceServicesContainer
from .runtime.integration_container import IntegrationServicesContainer


class Container(containers.DeclarativeContainer):
    """Main dependency injection container for DiPeO.
    
    This container integrates the new immutable/mutable separation architecture
    while maintaining backward compatibility with existing code.
    """

    # Self reference for container injection
    __self__ = providers.Self()

    # Configuration
    config = providers.Configuration()

    # Base directory configuration
    base_dir = providers.Factory(
        lambda: Path(os.environ.get("DIPEO_BASE_DIR", get_project_base_dir()))
    )

    # ===== NEW CONTAINER STRUCTURE =====
    
    # Business logic container first (no dependencies)  
    business = providers.Container(
        BusinessLogicContainer,
        config=config,
    )
    
    # Persistence container (depends on business)
    persistence = providers.Container(
        PersistenceServicesContainer,
        config=config,
        base_dir=base_dir,
        business=business,
    )
    
    # Static container (depends on persistence for api_key_service)
    static = providers.Container(
        StaticServicesContainer,
        config=config,
        persistence=persistence,
    )
    
    # Wire business container's static dependency
    business.override_providers(static=static)
    
    integration = providers.Container(
        IntegrationServicesContainer,
        config=config,
        base_dir=base_dir,
        business=business,
        persistence=persistence,
    )
    
    dynamic = providers.Container(
        DynamicServicesContainer,
        config=config,
        static=static,
        business=business,
        persistence=persistence,
        integration=integration,
    )
    
    # ===== LEGACY CONTAINERS (for backward compatibility) =====
    
    # Domain layer first (no dependencies on other layers)
    domain = providers.Container(
        DomainContainer,
        config=config,
        base_dir=base_dir,
    )
    
    # Infrastructure layer (depends on domain services)
    infra = providers.Container(
        InfrastructureContainer,
        config=config,
        base_dir=base_dir,
        api_key_service=domain.api_key_service,
        api_business_logic=domain.api_business_logic,
        file_business_logic=domain.file_business_logic,
        diagram_business_logic=domain.diagram_business_logic,
    )
    
    # Wire domain's infrastructure dependencies
    domain.override_providers(infra=infra)
    
    # Application layer (now depends on new containers)
    application = providers.Container(
        ApplicationContainer,
        config=config,
        static=static,
        business=business,
        dynamic=dynamic,
        persistence=persistence,
        integration=integration,
    )
    
    # ===== BACKWARD COMPATIBILITY ALIASES =====
    # These provide direct access to commonly used services
    
    # Infrastructure services
    @providers.Singleton
    def llm_service(self):
        """LLM service backward compatibility."""
        return self.integration.llm_service()
    
    @providers.Singleton
    def file_service(self):
        """File service backward compatibility."""
        return self.persistence.file_service()
    
    @providers.Singleton
    def api_key_service(self):
        """API key service backward compatibility."""
        return self.persistence.api_key_service()
    
    @providers.Singleton
    def notion_service(self):
        """Notion service backward compatibility."""
        return self.integration.notion_service()
    
    # Domain services
    @providers.Singleton
    def diagram_validator(self):
        """Diagram validator backward compatibility."""
        return self.static.diagram_validator()
    
    @providers.Singleton
    def conversation_manager(self):
        """Conversation manager backward compatibility."""
        return self.dynamic.conversation_manager()
    
    # Application services
    @providers.Singleton
    def service_registry(self):
        """Service registry backward compatibility."""
        return self.application.service_registry()
    
    @providers.Singleton
    def execution_service(self):
        """Execution service backward compatibility."""
        return self.application.execution_service()


# Export utility functions at module level for backward compatibility
__all__ = [
    'Container',
    'init_resources', 
    'shutdown_resources',
    'validate_protocol_compliance',
    'get_project_base_dir',
]