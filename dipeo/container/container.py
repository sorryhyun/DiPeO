"""Main dependency injection container for DiPeO."""

from dependency_injector import containers, providers

from dipeo.core.constants import BASE_DIR

from .application_container import ApplicationContainer
from .core.business_container import BusinessLogicContainer
from .core.container_profiles import ContainerProfile, get_profile

# Import new containers
from .core.static_container import StaticServicesContainer
from .runtime.dynamic_container import DynamicServicesContainer
from .runtime.integration_container import IntegrationServicesContainer
from .runtime.persistence_container import PersistenceServicesContainer
from .utilities import (
    init_resources,
    shutdown_resources,
    validate_protocol_compliance,
)


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
        lambda: BASE_DIR
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
    
    @classmethod
    def with_overrides(cls, **overrides) -> type["Container"]:
        """Create a new container class with specific overrides.
        
        This helper method simplifies creating container variations by allowing
        selective overrides without manually recreating all dependent containers.
        
        Args:
            **overrides: Provider overrides (e.g., base_dir=..., persistence=...)
            
        Returns:
            New container class with overrides applied
            
        Example:
            ServerContainer = Container.with_overrides(
                base_dir=providers.Factory(lambda: SERVER_BASE_DIR),
                persistence=providers.Container(ServerPersistenceContainer, ...)
            )
        """
        class_name = f"{cls.__name__}WithOverrides"
        
        # Create new container class inheriting from the current one
        new_class = type(class_name, (cls,), overrides)
        
        # Handle dependent container updates automatically
        if "persistence" in overrides and hasattr(cls, "integration"):
            # If persistence is overridden, update containers that depend on it
            new_class.integration = providers.Container(
                IntegrationServicesContainer,
                config=cls.config,
                base_dir=overrides.get("base_dir", cls.base_dir),
                business=cls.business,
                persistence=overrides["persistence"],
            )
            
            new_class.static = providers.Container(
                StaticServicesContainer,
                config=cls.config,
                persistence=overrides["persistence"],
            )
            
            new_class.dynamic = providers.Container(
                DynamicServicesContainer,
                config=cls.config,
                static=new_class.static,
                business=cls.business,
                persistence=overrides["persistence"],
                integration=new_class.integration,
            )
            
            new_class.application = providers.Container(
                ApplicationContainer,
                config=cls.config,
                static=new_class.static,
                business=cls.business,
                dynamic=new_class.dynamic,
                persistence=overrides["persistence"],
                integration=new_class.integration,
            )
        
        return new_class
    
    def create_sub_container(
        self, 
        parent_execution_id: str,
        sub_execution_id: str,
        config_overrides: dict = None
    ) -> "Container":
        """Create a sub-container for sub-diagram execution.
        
        This implements the simplified architecture where:
        - Infrastructure layers (persistence, integration, static, business) are always shared
        - Only dynamic (execution state) is isolated
        - Conversation can optionally be isolated based on config
        
        Args:
            parent_execution_id: Parent execution ID for context
            sub_execution_id: Sub-execution ID for isolation
            config_overrides: Configuration overrides (e.g., isolation settings)
            
        Returns:
            New container instance with selective isolation
        """
        from .application_container import ApplicationContainer
        from dipeo.application.unified_service_registry import UnifiedServiceRegistry
        
        # Get sub_diagram profile as base
        sub_profile = get_profile('sub_diagram')
        
        # Merge config overrides
        if config_overrides:
            if sub_profile.config_overrides:
                sub_profile.config_overrides.update(config_overrides)
            else:
                sub_profile.config_overrides = config_overrides
        
        # Create new container instance
        sub_container = Container()
        sub_container._profile = sub_profile
        
        # Copy configuration from parent
        sub_container.config.from_dict(self.config())
        
        # Apply sub-container specific config
        if sub_profile.config_overrides:
            sub_container.config.update(sub_profile.config_overrides)
        
        # IMPORTANT: Share infrastructure containers (no isolation)
        # These are always shared per the simplified architecture
        sub_container.business.override(self.business())
        sub_container.persistence.override(self.persistence())
        sub_container.static.override(self.static())
        sub_container.integration.override(self.integration())
        
        # Create new dynamic container (always isolated)
        # This provides isolated execution state
        sub_container.dynamic.override(
            providers.Container(
                DynamicServicesContainer,
                config=sub_container.config,
                static=sub_container.static,
                business=sub_container.business,
                persistence=sub_container.persistence,
                integration=sub_container.integration,
            )
        )
        
        # Create new application container with hierarchical service registry
        # This allows selective service overrides
        parent_registry = self.application().unified_service_registry()
        
        # Create hierarchical registry for inheritance
        sub_registry = UnifiedServiceRegistry(parent=parent_registry)
        
        # Override application container with new registry
        sub_container.application.override(
            providers.Container(
                ApplicationContainer,
                config=sub_container.config,
                static=sub_container.static,
                business=sub_container.business,
                dynamic=sub_container.dynamic,
                persistence=sub_container.persistence,
                integration=sub_container.integration,
                # Use hierarchical registry for service inheritance
                unified_service_registry=providers.Factory(
                    lambda: sub_registry
                )
            )
        )
        
        # Store parent context
        sub_container.config.update({
            'parent_execution_id': parent_execution_id,
            'sub_execution_id': sub_execution_id,
            'is_sub_container': True
        })
        
        return sub_container


# Export utility functions at module level for backward compatibility
__all__ = [
    'Container',
    'init_resources', 
    'shutdown_resources',
    'validate_protocol_compliance',
]