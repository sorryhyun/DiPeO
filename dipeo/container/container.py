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


class Container(containers.DeclarativeContainer):
    """Main dependency injection container for DiPeO."""

    # Self reference for container injection
    __self__ = providers.Self()

    # Configuration
    config = providers.Configuration()

    # Base directory configuration
    base_dir = providers.Factory(
        lambda: Path(os.environ.get("DIPEO_BASE_DIR", get_project_base_dir()))
    )

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
        api_domain_service=domain.api_domain_service,
        file_domain_service=domain.file_domain_service,
    )
    
    # Wire domain's infrastructure dependencies
    domain.override_providers(infra=infra)
    
    # Application layer (depends on both infra and domain)
    application = providers.Container(
        ApplicationContainer,
        config=config,
        infra=infra,
        domain=domain,
    )


# Export utility functions at module level for backward compatibility
__all__ = [
    'Container',
    'init_resources', 
    'shutdown_resources',
    'validate_protocol_compliance',
    'get_project_base_dir',
]