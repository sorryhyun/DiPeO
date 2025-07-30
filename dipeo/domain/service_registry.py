"""Domain Service Registry - Unified access to domain services.

DEPRECATED: This registry violates hexagonal architecture principles.
Use dipeo.application.registry.ServiceRegistry instead.
This will be removed in a future version.
"""

import warnings
from typing import Any, Protocol

warnings.warn(
    "dipeo.domain.service_registry is deprecated. "
    "Use dipeo.application.registry.ServiceRegistry instead.",
    DeprecationWarning,
    stacklevel=2
)


class BaseValidator(Protocol):
    """Protocol for domain validators."""
    
    def validate(self, data: Any) -> bool:
        """Validate data according to domain rules."""
        ...


class BaseBusinessService(Protocol):
    """Protocol for domain business services."""
    pass


class ValueFactory(Protocol):
    """Protocol for value object factories."""
    
    def create(self, **kwargs) -> Any:
        """Create a value object."""
        ...


class DomainServiceRegistry:
    """
    Unified registry for domain services.
    
    Provides centralized access to validators, business services,
    and value object factories across all domains.
    """
    
    def __init__(self):
        """Initialize the registry."""
        self._validators: dict[str, BaseValidator] = {}
        self._business_services: dict[str, BaseBusinessService] = {}
        self._value_factories: dict[str, ValueFactory] = {}
        self._initialized = False
    
    def initialize(self) -> None:
        """Initialize all domain services."""
        if self._initialized:
            return
        
        # Import and register services lazily to avoid circular imports
        self._register_api_services()
        self._register_file_services()
        self._register_diagram_services()
        self._register_db_services()
        self._register_notion_services()
        self._register_llm_services()
        self._register_execution_services()
        
        self._initialized = True
    
    def _register_api_services(self) -> None:
        """Register API domain services."""
        from .api.services.api_business_logic import APIBusinessLogic
        from .validators import APIValidator
        
        self._validators["api"] = APIValidator()
        self._business_services["api"] = APIBusinessLogic()
    
    def _register_file_services(self) -> None:
        """Register file domain services."""
        # FileBusinessLogic removed - old file services are deprecated
        from .validators import FileValidator
        
        self._validators["file"] = FileValidator()
        # self._business_services["file"] = FileBusinessLogic()  # Removed
    
    def _register_diagram_services(self) -> None:
        """Register diagram domain services."""
        from .diagram.services.diagram_format_service import DiagramFormatService
        from .diagram.services.diagram_operations_service import DiagramOperationsService
        from .validators import DiagramValidator
        
        self._validators["diagram"] = DiagramValidator()
        self._business_services["diagram_operations"] = DiagramOperationsService()
        self._business_services["diagram_format"] = DiagramFormatService()
    
    def _register_db_services(self) -> None:
        """Register database domain services."""
        try:
            from .db.services.db_operations_service import DBOperationsDomainService
            from .validators import DataValidator
            
            self._business_services["db_operations"] = DBOperationsDomainService()
            self._validators["data"] = DataValidator()
            self._validators["db"] = DataValidator()  # Alias for compatibility
        except ImportError:
            # Service might not exist yet
            pass
    
    def _register_notion_services(self) -> None:
        """Register Notion domain services."""
        try:
            from .validators import NotionValidator
            self._validators["notion"] = NotionValidator()
        except ImportError:
            # Service might not exist yet
            pass
    
    def _register_llm_services(self) -> None:
        """Register LLM domain services."""
        from .llm.services.llm_domain_service import LLMDomainService
        
        llm_service = LLMDomainService()
        self._business_services["llm"] = llm_service
        # LLM service acts as both validator and business service
        self._validators["llm"] = llm_service  # type: ignore
    
    def _register_execution_services(self) -> None:
        """Register execution domain services."""
        from .validators import ExecutionValidator
        
        execution_validator = ExecutionValidator()
        # Only register as validator since it only provides validation
        self._validators["execution"] = execution_validator  # type: ignore
    
    def get_validator(self, domain: str) -> BaseValidator | None:
        """
        Get validator for a specific domain.
        
        Args:
            domain: Domain name (e.g., 'file', 'diagram', 'llm')
            
        Returns:
            Validator instance or None if not found
        """
        if not self._initialized:
            self.initialize()
        
        return self._validators.get(domain)
    
    def get_business_service(self, service_name: str) -> BaseBusinessService | None:
        """
        Get business service by name.
        
        Args:
            service_name: Service name (e.g., 'diagram_operations', 'llm')
            
        Returns:
            Business service instance or None if not found
        """
        if not self._initialized:
            self.initialize()
        
        return self._business_services.get(service_name)
    
    def get_value_factory(self, factory_name: str) -> ValueFactory | None:
        """
        Get value object factory by name.
        
        Args:
            factory_name: Factory name
            
        Returns:
            Value factory instance or None if not found
        """
        if not self._initialized:
            self.initialize()
        
        return self._value_factories.get(factory_name)
    
    def register_validator(self, domain: str, validator: BaseValidator) -> None:
        """
        Register a validator for a domain.
        
        Args:
            domain: Domain name
            validator: Validator instance
        """
        self._validators[domain] = validator
    
    def register_business_service(
        self,
        service_name: str,
        service: BaseBusinessService
    ) -> None:
        """
        Register a business service.
        
        Args:
            service_name: Service name
            service: Service instance
        """
        self._business_services[service_name] = service
    
    def register_value_factory(
        self,
        factory_name: str,
        factory: ValueFactory
    ) -> None:
        """
        Register a value object factory.
        
        Args:
            factory_name: Factory name
            factory: Factory instance
        """
        self._value_factories[factory_name] = factory
    
    def list_validators(self) -> dict[str, str]:
        """List all registered validators."""
        if not self._initialized:
            self.initialize()
        
        return {
            domain: type(validator).__name__
            for domain, validator in self._validators.items()
        }
    
    def list_business_services(self) -> dict[str, str]:
        """List all registered business services."""
        if not self._initialized:
            self.initialize()
        
        return {
            name: type(service).__name__
            for name, service in self._business_services.items()
        }
    
    def list_value_factories(self) -> dict[str, str]:
        """List all registered value factories."""
        if not self._initialized:
            self.initialize()
        
        return {
            name: type(factory).__name__
            for name, factory in self._value_factories.items()
        }


# Global registry instance
_registry: DomainServiceRegistry | None = None


def get_domain_service_registry() -> DomainServiceRegistry:
    """Get the global domain service registry instance.
    
    DEPRECATED: Use dipeo.application.registry.ServiceRegistry instead.
    """
    warnings.warn(
        "get_domain_service_registry() is deprecated. "
        "Use dipeo.application.registry.ServiceRegistry instead.",
        DeprecationWarning,
        stacklevel=2
    )
    global _registry
    if _registry is None:
        _registry = DomainServiceRegistry()
    return _registry