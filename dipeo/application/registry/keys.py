"""Service key definitions for DiPeO dependency injection."""

from typing import TYPE_CHECKING

from .service_registry import ServiceKey

if TYPE_CHECKING:
    pass


# Core Infrastructure Services
LLM_SERVICE = ServiceKey["LLMServicePort"]("llm_service")
STATE_STORE = ServiceKey["StateStorePort"]("state_store")
FILE_SERVICE = ServiceKey["FileServicePort"]("file_service")
MESSAGE_ROUTER = ServiceKey["MessageRouterPort"]("message_router")

# Unified Event Bus - replaces EVENT_BUS, MESSAGE_BUS, and DOMAIN_EVENT_BUS
EVENT_BUS = ServiceKey["EventBus"]("event_bus")

# Legacy aliases for backward compatibility (will be removed in v1.0)
MESSAGE_BUS = EVENT_BUS
DOMAIN_EVENT_BUS = EVENT_BUS

# Execution State Services
STATE_REPOSITORY = ServiceKey["ExecutionStateRepository"]("execution_state_repository")
STATE_SERVICE = ServiceKey["ExecutionStateService"]("execution_state_service")
STATE_CACHE = ServiceKey["ExecutionCachePort"]("execution_state_cache")

MEMORY_SERVICE = ServiceKey["MemoryService"]("memory_service")

# Storage Services
BLOB_STORE = ServiceKey["BlobStoreAdapter"]("blob_store")
FILESYSTEM_ADAPTER = ServiceKey["FileSystemPort"]("filesystem_adapter")

# Application Services
EXECUTION_ORCHESTRATOR = ServiceKey["ExecutionOrchestrator"]("execution_orchestrator")
PROMPT_BUILDER = ServiceKey["PromptBuilder"]("prompt_builder")
TEMPLATE_PROCESSOR = ServiceKey["TemplateProcessorPort"]("template_processor")
PROMPT_LOADING_SERVICE = ServiceKey["PromptLoadingUseCase"]("prompt_loading_service")
MEMORY_SELECTOR = ServiceKey["LLMMemorySelectionAdapter"]("memory_selector")

# Domain Services
DB_OPERATIONS_SERVICE = ServiceKey["DBOperationsDomainService"]("db_operations_service")
DIAGRAM_CONVERTER = ServiceKey["DiagramConverter"]("diagram_converter")
DIAGRAM_COMPILER = ServiceKey["DiagramCompiler"]("diagram_compiler")
DIAGRAM_SERIALIZER = ServiceKey["DiagramStorageSerializer"]("diagram_serializer")
DIAGRAM_PORT = ServiceKey["DiagramPort"]("diagram_port")

# External Integration Services
API_KEY_SERVICE = ServiceKey["APIKeyPort"]("api_key_service")
INTEGRATED_API_SERVICE = ServiceKey["IntegratedApiServicePort"]("integrated_api_service")
PROVIDER_REGISTRY = ServiceKey["Any"]("provider_registry")
API_INVOKER = ServiceKey["ApiInvoker"]("api_invoker")

# Parser Services
AST_PARSER = ServiceKey["ASTParserPort"]("ast_parser")

# Resolution Services
TRANSFORMATION_ENGINE = ServiceKey["TransformationEngine"]("transformation_engine")

# Execution Context Services
DIAGRAM = ServiceKey["ExecutableDiagram"]("diagram")
EXECUTION_CONTEXT = ServiceKey["ExecutionContext"]("execution_context")
CURRENT_NODE_INFO = ServiceKey["Dict[str, Any]"]("current_node_info")
NODE_EXEC_COUNTS = ServiceKey["Dict[str, int]"]("node_exec_counts")

# Diagram Services
EXECUTION_SERVICE = ServiceKey["ExecutionService"]("execution_service")
COMPILATION_SERVICE = ServiceKey["CompilationService"]("compilation_service")
PREPARE_DIAGRAM_USE_CASE = ServiceKey["PrepareDiagramForExecutionUseCase"](
    "prepare_diagram_use_case"
)

# Diagram Use Cases
COMPILE_DIAGRAM_USE_CASE = ServiceKey["CompileDiagramUseCase"]("diagram.use_case.compile")
VALIDATE_DIAGRAM_USE_CASE = ServiceKey["ValidateDiagramUseCase"]("diagram.use_case.validate")
SERIALIZE_DIAGRAM_USE_CASE = ServiceKey["SerializeDiagramUseCase"]("diagram.use_case.serialize")
LOAD_DIAGRAM_USE_CASE = ServiceKey["LoadDiagramUseCase"]("diagram.use_case.load")

# Infrastructure Adapters
DATABASE = ServiceKey["DatabasePort"]("database")
NOTION_CLIENT = ServiceKey["NotionClientPort"]("notion_client")

# Validator Services
DIAGRAM_VALIDATOR = ServiceKey["DiagramValidator"]("diagram_validator")

# Business Logic Services
API_BUSINESS_LOGIC = ServiceKey["APIBusinessLogic"]("api_business_logic")
FILE_BUSINESS_LOGIC = ServiceKey["FileBusinessLogic"]("file_business_logic")
DIAGRAM_STATISTICS_SERVICE = ServiceKey["DiagramStatisticsService"]("diagram_statistics")
DIAGRAM_FORMAT_SERVICE = ServiceKey["DiagramFormatDetector"]("diagram_format_service")
LLM_DOMAIN_SERVICE = ServiceKey["LLMDomainService"]("llm_domain_service")

# Additional Services
CLI_SESSION_SERVICE = ServiceKey["CliSessionService"]("cli_session_service")

# Repository Services
API_KEY_REPOSITORY = ServiceKey["APIKeyRepository"]("api_key_repository")
CONVERSATION_REPOSITORY = ServiceKey["ConversationRepository"]("conversation_repository")
DIAGRAM_REPOSITORY = ServiceKey["DiagramRepository"]("diagram_repository")
EXECUTION_REPOSITORY = ServiceKey["ExecutionRepository"]("execution_repository")
PERSON_REPOSITORY = ServiceKey["PersonRepository"]("person_repository")

# Registry Services
NODE_REGISTRY = ServiceKey["HandlerRegistry"]("node_registry")


__all__ = [
    "API_BUSINESS_LOGIC",
    "API_INVOKER",
    "API_KEY_REPOSITORY",
    "API_KEY_SERVICE",
    "AST_PARSER",
    "BLOB_STORE",
    "CLI_SESSION_SERVICE",
    "COMPILATION_SERVICE",
    "CONVERSATION_REPOSITORY",
    "CURRENT_NODE_INFO",
    "DATABASE",
    "DB_OPERATIONS_SERVICE",
    "DIAGRAM",
    "DIAGRAM_COMPILER",
    "DIAGRAM_CONVERTER",
    "DIAGRAM_FORMAT_SERVICE",
    "DIAGRAM_PORT",
    "DIAGRAM_REPOSITORY",
    "DIAGRAM_SERIALIZER",
    "DIAGRAM_STATISTICS_SERVICE",
    "DIAGRAM_VALIDATOR",
    "DOMAIN_EVENT_BUS",
    "EVENT_BUS",
    "EXECUTION_CONTEXT",
    "EXECUTION_ORCHESTRATOR",
    "EXECUTION_REPOSITORY",
    "EXECUTION_SERVICE",
    "FILESYSTEM_ADAPTER",
    "FILE_BUSINESS_LOGIC",
    "FILE_SERVICE",
    "INTEGRATED_API_SERVICE",
    "LLM_DOMAIN_SERVICE",
    "LLM_SERVICE",
    "MEMORY_SELECTOR",
    "MEMORY_SERVICE",
    "MESSAGE_BUS",
    "MESSAGE_ROUTER",
    "NODE_EXEC_COUNTS",
    "NODE_REGISTRY",
    "NOTION_CLIENT",
    "PERSON_REPOSITORY",
    "PREPARE_DIAGRAM_USE_CASE",
    "PROMPT_BUILDER",
    "PROMPT_LOADING_SERVICE",
    "PROVIDER_REGISTRY",
    "STATE_CACHE",
    "STATE_REPOSITORY",
    "STATE_SERVICE",
    "STATE_STORE",
    "TEMPLATE_PROCESSOR",
    "TRANSFORMATION_ENGINE",
]
