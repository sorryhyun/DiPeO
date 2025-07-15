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
    
    def __init__(self, **services):
        # Initialize with optional services.
        super().__init__()
        
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
            "api_integration_service": "api_integration_service",
            "text_processing_service": "text_processing_service",
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
    
    def get(self, key: ServiceKey[T] | str, default: Optional[T] = None) -> Optional[T]:
        """Get a service by typed key or string.
        
        Args:
            key: Either a ServiceKey[T] or string name
            default: Default value if not found
            
        Returns:
            The service instance or default
        """
        name = key.name if isinstance(key, ServiceKey) else key
        result = super().get(name)
        
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