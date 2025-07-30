# Unified service registry that works for both server and local execution.
#
# NOTE: This implementation is being consolidated into dipeo.application.registry.ServiceRegistry
# for better type safety and cleaner architecture. New code should use the registry module.

from dataclasses import dataclass
from typing import Any, Generic, Optional, TypeVar, cast

from dipeo.core.utils.dynamic_registry import DynamicRegistry

# Type variable for service types
T = TypeVar('T')


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
# FILE_SERVICE removed - use FILESYSTEM_ADAPTER instead
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
        self._overrides = {}  # Track services that override parent
        self._isolated = set()  # Track services that are isolated from parent
        
        # Register any provided services
        for name, service in services.items():
            self.register(name, service)
    
    
    @property
    def parent(self) -> Optional["UnifiedServiceRegistry"]:
        """Get parent registry."""
        return self._parent
    
    def get(self, key: ServiceKey[T] | str, default: Optional[T] = None) -> Optional[T]:
        """Get a service by typed key or string.
        
        First checks overrides, then local registry, then parent chain
        (unless isolated).
        
        Args:
            key: Either a ServiceKey[T] or string name
            default: Default value if not found
            
        Returns:
            The service instance or default
        """
        name = key.name if isinstance(key, ServiceKey) else key
        
        # Check if service is isolated (blocked from parent)
        if name in self._isolated:
            # Only check local registry, not parent
            result = self._items.get(name)
        # Check overrides first (explicit overrides of parent services)
        elif name in self._overrides:
            result = self._overrides[name]
        # Check local registry
        elif name in self._items:
            result = self._items[name]
        # Check parent if available and not isolated
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
        self._overrides[name] = service
        # Also register in local items for backward compatibility
        self.register(name, service)
        
    def isolate(self, key: ServiceKey[T] | str) -> None:
        """Isolate a service, preventing access to parent's version.
        
        This is useful when you want to ensure a service is not
        inherited from the parent registry, effectively blocking it.
        
        Args:
            key: Service key or name to isolate
        """
        name = key.name if isinstance(key, ServiceKey) else key
        self._isolated.add(name)
        # Optionally set to None to explicitly block
        self._overrides[name] = None
        
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
        Isolated services are excluded from parent inheritance.
        
        Returns:
            Combined service dictionary
        """
        # Start with parent services if not isolated
        all_services = {}
        if self._parent:
            parent_services = self._parent.get_all_services()
            # Only include parent services that are not isolated
            for name, service in parent_services.items():
                if name not in self._isolated:
                    all_services[name] = service
            
        # Override with local services
        all_services.update(self._items)
        
        # Apply explicit overrides (including None values for blocked services)
        for name, service in self._overrides.items():
            if service is None and name in all_services:
                # Remove blocked services
                del all_services[name]
            else:
                all_services[name] = service
        
        return all_services
        
    def create_child(self, **services) -> "UnifiedServiceRegistry":
        """Create a child registry inheriting from this one.
        
        The child registry will:
        - Inherit all non-isolated services from parent
        - Start with empty overrides and isolation sets
        - Can selectively override or isolate parent services
        
        Args:
            **services: Initial services for child
            
        Returns:
            New child registry with parent inheritance
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
    'API_SERVICE',
    'NOTION_SERVICE',
    'DIAGRAM_STORAGE_SERVICE',
    'DB_OPERATIONS_SERVICE',
    'MESSAGE_ROUTER',
    'CURRENT_NODE_INFO',
    'NODE_EXEC_COUNTS',
]