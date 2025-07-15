"""Type-safe service key system for dependency injection."""

from dataclasses import dataclass
from typing import Any, Generic, Optional, Protocol, TypeVar, cast

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
        llm = services.get(LLM_SERVICE)  # Type: LLMServicePort
    """
    
    name: str
    description: str = ""
    
    def __str__(self) -> str:
        return self.name
    
    def __repr__(self) -> str:
        return f"ServiceKey[{self.name}]"


# Common service keys
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from dipeo.core.ports import LLMServicePort, StateStorePort
    from dipeo.core.static.executable_diagram import ExecutableDiagram
    from dipeo.infra.persistence.keys import ApiKeyService
    from dipeo.application.utils.template import PromptBuilder


# Define standard service keys
LLM_SERVICE = ServiceKey[Any]("llm_service", "LLM completion service")
API_KEY_SERVICE = ServiceKey[Any]("api_key_service", "API key management")
STATE_STORE = ServiceKey[Any]("state_store", "Execution state persistence")
DIAGRAM = ServiceKey[Any]("diagram", "Current executable diagram")
CONVERSATION_MANAGER = ServiceKey[Any]("conversation_manager", "Conversation state")
PROMPT_BUILDER = ServiceKey[Any]("prompt_builder", "Prompt template builder")
MESSAGE_ROUTER = ServiceKey[Any]("message_router", "Message routing service")

# Additional service keys
FILE_SERVICE = ServiceKey[Any]("file", "File operations service")
API_SERVICE = ServiceKey[Any]("api_service", "HTTP API client service")
NOTION_SERVICE = ServiceKey[Any]("notion_service", "Notion API service")
CONVERSATION_SERVICE = ServiceKey[Any]("conversation_service", "Conversation management service")
CONDITION_EVALUATION_SERVICE = ServiceKey[Any]("condition_evaluation_service", "Condition expression evaluator")
EXECUTION_CONTEXT = ServiceKey[Any]("execution_context", "Current execution context")


class TypedServiceRegistry:
    """Type-safe service registry with ServiceKey support."""
    
    def __init__(self, services: Optional[dict[str, Any]] = None):
        self._services: dict[str, Any] = services or {}
        self._legacy_mode = True  # Support string keys by default
    
    def register(self, key: ServiceKey[T], service: T) -> None:
        """Register a service with a typed key."""
        self._services[key.name] = service
    
    def get(self, key: ServiceKey[T], default: Optional[T] = None) -> Optional[T]:
        """Get a service by typed key."""
        return cast(Optional[T], self._services.get(key.name, default))
    
    def require(self, key: ServiceKey[T]) -> T:
        """Get a required service, raising if not found."""
        if key.name not in self._services:
            raise ValueError(f"Required service '{key.name}' not found")
        return cast(T, self._services[key.name])
    
    def has(self, key: ServiceKey[T]) -> bool:
        """Check if a service is registered."""
        return key.name in self._services
    
    # Legacy string-based access for backward compatibility
    def get_by_name(self, name: str, default: Any = None) -> Any:
        """Get a service by string name (legacy)."""
        if not self._legacy_mode:
            raise ValueError("Legacy string access disabled")
        return self._services.get(name, default)
    
    def register_by_name(self, name: str, service: Any) -> None:
        """Register a service by string name (legacy)."""
        if not self._legacy_mode:
            raise ValueError("Legacy string access disabled")
        self._services[name] = service
    
    def disable_legacy_mode(self) -> None:
        """Disable string-based access (for migration)."""
        self._legacy_mode = False
    
    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for legacy compatibility."""
        return self._services.copy()


class ServiceKeyAdapter:
    """Adapter to use ServiceKey with legacy string-based registries."""
    
    def __init__(self, legacy_registry: dict[str, Any]):
        self._registry = legacy_registry
    
    def get(self, key: ServiceKey[T], default: Optional[T] = None) -> Optional[T]:
        """Get a service by typed key from legacy registry."""
        return cast(Optional[T], self._registry.get(key.name, default))
    
    def require(self, key: ServiceKey[T]) -> T:
        """Get a required service from legacy registry."""
        if key.name not in self._registry:
            raise ValueError(f"Required service '{key.name}' not found")
        return cast(T, self._registry[key.name])
    
    def has(self, key: ServiceKey[T]) -> bool:
        """Check if a service exists in legacy registry."""
        return key.name in self._registry


def migrate_to_typed_services(
    legacy_services: dict[str, Any]
) -> TypedServiceRegistry:
    """Migrate legacy string-based services to typed registry."""
    registry = TypedServiceRegistry()
    
    # Map known services to typed keys
    service_mappings = [
        ("llm_service", LLM_SERVICE),
        ("api_key_service", API_KEY_SERVICE),
        ("state_store", STATE_STORE),
        ("diagram", DIAGRAM),
        ("conversation_manager", CONVERSATION_MANAGER),
        ("prompt_builder", PROMPT_BUILDER),
        ("message_router", MESSAGE_ROUTER),
        ("file", FILE_SERVICE),
        ("api_service", API_SERVICE),
        ("notion_service", NOTION_SERVICE),
        ("conversation_service", CONVERSATION_SERVICE),
        ("condition_evaluation_service", CONDITION_EVALUATION_SERVICE),
        ("execution_context", EXECUTION_CONTEXT),
    ]
    
    for name, key in service_mappings:
        if name in legacy_services:
            registry.register(key, legacy_services[name])
    
    # Register any unknown services by name (legacy)
    for name, service in legacy_services.items():
        if name not in registry._services:
            registry.register_by_name(name, service)
    
    return registry