"""Base containers for immutable and mutable service separation."""

from dependency_injector import containers, providers


class ImmutableBaseContainer(containers.DeclarativeContainer):
    """Base container for immutable (stateless) services.
    
    All services in this container should be Singletons as they maintain no state
    and can be safely shared across multiple executions.
    """
    
    @classmethod
    def validate_immutable_providers(cls) -> None:
        """Validate that all providers are singletons or constants."""
        for name, provider in cls.providers.items():
            if not isinstance(provider, (providers.Singleton, providers.Callable, 
                                       providers.Configuration, providers.Factory)):
                # Factory is allowed if it returns immutable instances
                if isinstance(provider, providers.Factory):
                    continue
                raise ValueError(
                    f"Provider '{name}' in {cls.__name__} must be a Singleton or Callable. "
                    f"Got {type(provider).__name__}"
                )


class MutableBaseContainer(containers.DeclarativeContainer):
    """Base container for mutable (stateful) services.
    
    Services in this container should typically use Factory providers to ensure
    each execution gets fresh instances of stateful services.
    """
    
    @classmethod
    def validate_mutable_providers(cls) -> None:
        """Validate that stateful services use appropriate providers."""
        for name, provider in cls.providers.items():
            # Singletons are allowed for certain coordination services
            # but should be carefully reviewed
            if isinstance(provider, providers.Singleton):
                # Log warning or validate specific allowed singletons
                pass


class ContainerValidator:
    """Utilities for validating container configurations."""
    
    @staticmethod
    def validate_no_circular_dependencies(container: containers.DeclarativeContainer) -> None:
        """Check for circular dependencies in container configuration."""
        # Implementation would analyze provider dependencies
        # For now, this is a placeholder
        pass
    
    @staticmethod
    def validate_layer_boundaries(
        domain_container: containers.DeclarativeContainer,
        infrastructure_container: containers.DeclarativeContainer,
        application_container: containers.DeclarativeContainer,
    ) -> None:
        """Ensure proper layering - domain should not depend on infrastructure."""
        # Check that domain providers don't reference infrastructure providers
        # This is a placeholder for the actual implementation
        pass
    
    @staticmethod
    def categorize_services(container: containers.DeclarativeContainer) -> dict[str, str]:
        """Categorize services as immutable or mutable based on their characteristics."""
        categories = {}
        
        immutable_keywords = [
            "validator", "compiler", "processor", "transformer", "builder",
            "calculator", "analyzer", "formatter", "parser", "converter"
        ]
        
        mutable_keywords = [
            "storage", "repository", "manager", "service", "executor",
            "orchestrator", "context", "state", "cache", "session"
        ]
        
        for name, provider in container.providers.items():
            name_lower = name.lower()
            
            # Check keywords
            if any(keyword in name_lower for keyword in immutable_keywords):
                categories[name] = "immutable"
            elif any(keyword in name_lower for keyword in mutable_keywords):
                categories[name] = "mutable"
            else:
                # Default based on provider type
                if isinstance(provider, providers.Singleton):
                    categories[name] = "immutable"
                elif isinstance(provider, providers.Factory):
                    categories[name] = "mutable"
                else:
                    categories[name] = "unknown"
        
        return categories