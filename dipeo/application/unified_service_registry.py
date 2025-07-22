# Unified service registry that works for both server and local execution.

from dataclasses import dataclass
from typing import Any, Generic, Optional, TypeVar, cast, TYPE_CHECKING

from dipeo.core.utils.dynamic_registry import DynamicRegistry

# Type variable for service types
T = TypeVar('T')

if TYPE_CHECKING:
    pass


@dataclass(frozen=True)
class ServiceKey(Generic[T]):
    """Type-safe key for service lookup.
    
    This provides compile-time type safety for service dependencies.
    
    Example:
        LLM_SERVICE = ServiceKey[LLMServicePort]("llm_service")
        API_KEY_SERVICE = ServiceKey[ApiKeyService]("api_key_service")
        
        # In handler:
        llm = registry.get(LLM_SERVICE)  # Type: LLMServicePort
    """
    
    name: str
    description: str = ""
    
    def __str__(self) -> str:
        return self.name
    
    def __repr__(self) -> str:
        return f"ServiceKey[{self.name}]"


# Core service keys
LLM_SERVICE = ServiceKey["LLMServicePort"]("llm_service", "LLM completion service")
STATE_STORE = ServiceKey["StateStorePort"]("state_store", "Execution state persistence")
DIAGRAM = ServiceKey["ExecutableDiagram"]("diagram", "Current executable diagram")
EXECUTION_CONTEXT = ServiceKey["ExecutionContext"]("execution_context", "Current execution context")

# Application service keys
API_KEY_SERVICE = ServiceKey["APIKeyService"]("api_key_service", "API key management")
CONVERSATION_MANAGER = ServiceKey["ConversationManager"]("conversation_manager", "Conversation state")
CONVERSATION_SERVICE = ServiceKey["ConversationManager"]("conversation_service", "Conversation management service")
PROMPT_BUILDER = ServiceKey["PromptBuilder"]("prompt_builder", "Prompt template builder")
CONDITION_EVALUATION_SERVICE = ServiceKey["ConditionEvaluator"]("condition_evaluation_service", "Condition expression evaluator")

# Infrastructure service keys
FILE_SERVICE = ServiceKey["FileServicePort"]("file_service", "File operations service")
API_SERVICE = ServiceKey["APIService"]("api_service", "HTTP API client service")
NOTION_SERVICE = ServiceKey["NotionServicePort"]("notion_service", "Notion API service")
DIAGRAM_STORAGE_SERVICE = ServiceKey["DiagramStorageAdapter"]("diagram_storage_service", "Diagram file storage and retrieval")
DB_OPERATIONS_SERVICE = ServiceKey["DBOperationsDomainService"]("db_operations_service", "Database operations service")

# Runtime service keys
MESSAGE_ROUTER = ServiceKey[Any]("message_router", "Message routing service")
CURRENT_NODE_INFO = ServiceKey["Dict[str, Any]"]("current_node_info", "Current node execution information")
NODE_EXEC_COUNTS = ServiceKey["Dict[str, int]"]("node_exec_counts", "Node execution counter tracking")


class UnifiedServiceRegistry(DynamicRegistry):
    # Unified service registry that supports both static and dynamic service registration.
    # Can be used in server, local/CLI, and test modes.
    
    def __init__(self, parent: Optional["UnifiedServiceRegistry"] = None, **services):
        # Initialize with optional services.
        super().__init__()
        self._parent = parent
        
        # Register any provided services
        for name, service in services.items():
            self.register(name, service)
    
    @classmethod
    def from_context(cls, context: Any) -> "UnifiedServiceRegistry":
        # Create registry from an ApplicationContext.
        registry = cls()
        
        # Map of service names to context attributes
        # Primary mappings use _service suffix consistently
        service_mapping = {
            # Core services
            "llm_service": "llm_service",
            "api_key_service": "api_key_service",
            "file_service": "file_service",
            "conversation_service": "conversation_service",
            "conversation_manager": "conversation_manager",
            "notion_service": "notion_service",
            
            # Infrastructure services
            "diagram_loader": "diagram_loader",
            "state_store": "state_store",
            "message_router": "message_router",
            
            # Domain services
            "diagram_storage_service": "diagram_storage_service",
            "integrated_diagram_service": "integrated_diagram_service",
            "api_integration_service": "api_integration_service",
            "db_operations_service": "db_operations_service",
            "code_execution_service": "code_execution_service",
            
            # Execution domain services
            "execution_flow_service": "execution_flow_service",
            # "input_resolution_service" removed - using typed version directly
        }
        
        # Register services from context
        for service_name, context_attr in service_mapping.items():
            if hasattr(context, context_attr):
                service = getattr(context, context_attr)
                if service is not None:
                    registry.register(service_name, service)
                    # Debug logging
                    import logging
                    logging.debug(f"Registered service: {service_name} -> {type(service).__name__}")
            else:
                # Debug logging for missing attributes
                import logging
                logging.debug(f"Context missing attribute: {context_attr}")
        
        
        # Add context itself for handlers that need it
        registry.register("context", context)
        registry.register("app_context", context)
        
        return registry
    
    @classmethod
    def from_container(cls, container: Any) -> "UnifiedServiceRegistry":
        """Create registry by automatically discovering services from a container.
        
        This method introspects the container's sub-containers and providers
        to automatically register services, reducing manual configuration.
        
        Args:
            container: A dependency_injector Container with sub-containers
            
        Returns:
            UnifiedServiceRegistry with all discovered services registered
        """
        from dependency_injector import containers, providers
        
        registry = cls()
        
        # Service name mapping for consistent naming
        # Maps provider names to standardized service names
        name_mappings = {
            # Keep consistent with existing names
            "llm_service": "llm_service",
            "notion_service": "notion_service", 
            "api_service": "api_service",
            "file_service": "file_service",
            "template_processor": "template_service",
            "conversation_manager": "conversation_manager",
            # Add more mappings as needed
        }
        
        # Legacy aliases that should be registered
        legacy_aliases = {
            "file_service": ["file"],  # file_service also registered as "file"
            "template_processor": ["template"],  # template_processor also as "template"
            "conversation_manager": ["conversation_service"],  # Also register as conversation_service
        }
        
        # Sub-containers to process in order
        sub_container_names = [
            "integration",
            "persistence", 
            "business",
            "static",
            "dynamic"
        ]
        
        # Process each sub-container
        for container_name in sub_container_names:
            if hasattr(container, container_name):
                sub_container_provider = getattr(container, container_name)
                
                # Get the actual container instance
                if isinstance(sub_container_provider, providers.Container):
                    try:
                        sub_container = sub_container_provider()
                        
                        # Process providers in the sub-container
                        if hasattr(sub_container, 'providers'):
                            for provider_name, provider in sub_container.providers.items():
                                # Skip special providers
                                if provider_name.startswith('_') or provider_name == 'config':
                                    continue
                                
                                # Try to get the service instance
                                try:
                                    if isinstance(provider, (providers.Singleton, providers.Factory)):
                                        service = provider()
                                        
                                        # Determine the service name
                                        service_name = name_mappings.get(provider_name, provider_name)
                                        
                                        # Register the service
                                        registry.register(service_name, service)
                                        
                                        # Register legacy aliases if any
                                        if provider_name in legacy_aliases:
                                            for alias in legacy_aliases[provider_name]:
                                                registry.register(alias, service)
                                                
                                except Exception:
                                    # Skip services that fail to instantiate
                                    # This might happen for services with unmet dependencies
                                    pass
                                    
                    except Exception:
                        # Skip containers that fail to instantiate
                        pass
        
        return registry
    
    @property
    def parent(self) -> Optional["UnifiedServiceRegistry"]:
        """Get parent registry."""
        return self._parent
    
    def get(self, key: ServiceKey[T] | str, default: Optional[T] = None) -> Optional[T]:
        """Get a service by typed key or string.
        
        First checks local registry, then traverses up parent chain.
        
        Args:
            key: Either a ServiceKey[T] or string name
            default: Default value if not found
            
        Returns:
            The service instance or default
        """
        name = key.name if isinstance(key, ServiceKey) else key
        
        # Check local registry first
        if name in self._items:
            result = self._items[name]
        # Check parent if available
        elif self._parent is not None:
            return self._parent.get(key, default)
        else:
            result = None
        
        if isinstance(key, ServiceKey):
            return cast(Optional[T], result if result is not None else default)
        return result if result is not None else default
    
    def require(self, key: ServiceKey[T] | str) -> T:
        """Get a required service, raising error if not found.
        
        Args:
            key: Either a ServiceKey[T] or string name
            
        Returns:
            The service instance
            
        Raises:
            ValueError: If service not found
        """
        name = key.name if isinstance(key, ServiceKey) else key
        service = self.get(name)
        
        if service is None:
            raise ValueError(f"Required service '{name}' not found")
            
        if isinstance(key, ServiceKey):
            return cast(T, service)
        return service
    
    def has(self, key: ServiceKey[T] | str) -> bool:
        """Check if a service exists.
        
        Args:
            key: Either a ServiceKey[T] or string name
            
        Returns:
            True if service exists
        """
        name = key.name if isinstance(key, ServiceKey) else key
        return name in self._items
    
    def register_typed(self, key: ServiceKey[T], service: T) -> None:
        """Register a service with a typed key.
        
        Args:
            key: The service key
            service: The service instance
        """
        self.register(key.name, service)
    
    def get_handler_services(self, required_services: list[str]) -> dict[str, Any]:
        # Get services required by a handler.
        services = {}
        
        for service_name in required_services:
            service = self.get(service_name)
            if service is None:
                # Special case: "diagram" is injected at runtime by execution engine
                if service_name == "diagram":
                    continue
                raise ValueError(f"Required service '{service_name}' not found in registry")
            services[service_name] = service
        
        return services
    
    def validate_required_services(self, required_services: list[str]) -> dict[str, bool]:
        # Validate that required services are registered and available.
        validation_results = {}
        for service_name in required_services:
            service = self.get(service_name)
            validation_results[service_name] = service is not None
        return validation_results
    
    def has_local(self, key: ServiceKey[T] | str) -> bool:
        """Check if service exists in local registry only.
        
        Does not check parent registries.
        
        Args:
            key: Service key or name
            
        Returns:
            True if exists locally
        """
        name = key.name if isinstance(key, ServiceKey) else key
        return name in self._items
        
    def override(self, key: ServiceKey[T] | str, service: T) -> None:
        """Override a service in the local registry.
        
        This allows child registries to override parent services
        without modifying the parent.
        
        Args:
            key: Service key or name
            service: Service instance
        """
        name = key.name if isinstance(key, ServiceKey) else key
        self.register(name, service)
        
    def get_ancestry_chain(self) -> list["UnifiedServiceRegistry"]:
        """Get full ancestry chain from this registry to root.
        
        Returns:
            List of registries from self to root
        """
        chain = [self]
        current = self._parent
        
        while current is not None:
            chain.append(current)
            current = current._parent
            
        return chain
        
    def get_all_services(self) -> dict[str, Any]:
        """Get all services including inherited ones.
        
        Services from child registries override parent services.
        
        Returns:
            Combined service dictionary
        """
        # Start with parent services
        if self._parent:
            all_services = self._parent.get_all_services()
        else:
            all_services = {}
            
        # Override with local services
        all_services.update(self._items)
        
        return all_services
        
    def create_child(self, **services) -> "UnifiedServiceRegistry":
        """Create a child registry inheriting from this one.
        
        Args:
            **services: Initial services for child
            
        Returns:
            New child registry
        """
        return UnifiedServiceRegistry(parent=self, **services)
    
    def __repr__(self) -> str:
        # String representation of the registry.
        services = list(self._items.keys())
        return f"UnifiedServiceRegistry({', '.join(services)})"


# Re-export common service keys for convenience
__all__ = [
    'UnifiedServiceRegistry',
    'ServiceKey',
    'LLM_SERVICE',
    'STATE_STORE',
    'DIAGRAM',
    'EXECUTION_CONTEXT',
    'API_KEY_SERVICE',
    'CONVERSATION_MANAGER',
    'CONVERSATION_SERVICE',
    'PROMPT_BUILDER',
    'CONDITION_EVALUATION_SERVICE',
    'FILE_SERVICE',
    'API_SERVICE',
    'NOTION_SERVICE',
    'DIAGRAM_STORAGE_SERVICE',
    'DB_OPERATIONS_SERVICE',
    'MESSAGE_ROUTER',
    'CURRENT_NODE_INFO',
    'NODE_EXEC_COUNTS',
]