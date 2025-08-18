"""Registry tokens for domain services and infrastructure adapters."""

from typing import TYPE_CHECKING

from .service_registry import ServiceKey

if TYPE_CHECKING:
    from dipeo.domain.execution.state import (
        ExecutionCachePort,
        ExecutionStateRepository,
        ExecutionStateService,
    )
    from dipeo.domain.integrations import ApiInvoker, ApiProvider, ApiProviderRegistry
    from dipeo.domain.llm import LLMClient, LLMService, MemoryService
    from dipeo.domain.events import DomainEventBus, MessageBus
    from dipeo.domain.storage import (
        ArtifactStorePort,
        BlobStorePort,
        FileSystemPort,
    )
    from dipeo.domain.diagram.ports import (
        DiagramCompiler,
        DiagramStorageSerializer,
        DiagramPort,
    )
    from dipeo.domain.diagram.resolution.interfaces import (
        CompileTimeResolverV2,
        RuntimeInputResolverV2,
        TransformationEngineV2,
    )


# Execution State Tokens
STATE_REPOSITORY = ServiceKey["ExecutionStateRepository"]("execution_state_repository")
STATE_SERVICE = ServiceKey["ExecutionStateService"]("execution_state_service")
STATE_CACHE = ServiceKey["ExecutionCachePort"]("execution_state_cache")

# Messaging Tokens
MESSAGE_BUS = ServiceKey["MessageBus"]("message_bus")
DOMAIN_EVENT_BUS = ServiceKey["DomainEventBus"]("domain_event_bus")

# LLM Tokens
LLM_CLIENT = ServiceKey["LLMClient"]("llm_client")
LLM_SERVICE = ServiceKey["LLMService"]("llm_service")
LLM_REGISTRY = ServiceKey["dict[str, LLMClient]"]("llm_registry")
MEMORY_SERVICE = ServiceKey["MemoryService"]("memory_service")

# Integration Tokens
API_PROVIDER_REGISTRY = ServiceKey["ApiProviderRegistry"]("api_provider_registry")
API_INVOKER = ServiceKey["ApiInvoker"]("api_invoker")

# Storage Tokens (domain ports)
FILE_SYSTEM = ServiceKey["FileSystemPort"]("file_system")
ARTIFACT_STORE = ServiceKey["ArtifactStorePort"]("artifact_store")
BLOB_STORAGE = ServiceKey["BlobStorePort"]("blob_storage")

# Diagram Processing Tokens
DIAGRAM_COMPILER = ServiceKey["DiagramCompiler"]("diagram_compiler")
DIAGRAM_SERIALIZER = ServiceKey["DiagramStorageSerializer"]("diagram_serializer")
DIAGRAM_PORT = ServiceKey["DiagramPort"]("diagram_port")

# Resolution Tokens
COMPILE_TIME_RESOLVER = ServiceKey["CompileTimeResolverV2"]("compile_time_resolver")
RUNTIME_RESOLVER = ServiceKey["RuntimeInputResolverV2"]("runtime_resolver")
TRANSFORMATION_ENGINE = ServiceKey["TransformationEngineV2"]("transformation_engine")

# AST Parser Token
AST_PARSER = ServiceKey["AstParser"]("ast_parser")

# Conversation & Person Tokens
CONVERSATION_MANAGER = ServiceKey["ConversationManager"]("conversation_manager")
PERSON_MANAGER = ServiceKey["PersonManager"]("person_manager")

# API Key Service Token
API_KEY_SERVICE = ServiceKey["ApiKeyService"]("api_key_service")