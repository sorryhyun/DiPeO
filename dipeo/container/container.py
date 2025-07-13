"""Main dependency injection container for DiPeO."""

import os
from pathlib import Path
from dependency_injector import containers, providers

from .application_container import ApplicationContainer
from .utilities import (
    get_project_base_dir,
    init_resources,
    shutdown_resources,
    validate_protocol_compliance,
)
from .core.container_profiles import ContainerProfile, get_profile

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
    
    # Profile management
    _profile: ContainerProfile = None

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
    
    @classmethod
    def set_profile(cls, profile_name: str) -> None:
        """Set the container profile for initialization."""
        cls._profile = get_profile(profile_name)
    
    @classmethod
    def get_profile(cls) -> ContainerProfile:
        """Get the current container profile."""
        if cls._profile is None:
            cls._profile = get_profile('full')  # Default profile
        return cls._profile


# Export utility functions at module level for backward compatibility
__all__ = [
    'Container',
    'init_resources', 
    'shutdown_resources',
    'validate_protocol_compliance',
    'get_project_base_dir',
]