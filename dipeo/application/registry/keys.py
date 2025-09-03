"""Service key definitions for DiPeO dependency injection."""

from typing import TYPE_CHECKING

from .service_registry import ServiceKey


# Type imports for service keys
if TYPE_CHECKING:
    from dipeo.domain.integrations.ports import LLMService as LLMServicePort
    from dipeo.domain.execution.state.ports import ExecutionStateRepository as StateStorePort
    from dipeo.domain.execution.state import (
        ExecutionCachePort,
        ExecutionStateRepository,
        ExecutionStateService,
    )
    from dipeo.domain.base.storage_port import BlobStorePort as FileServicePort
    from dipeo.domain.events.ports import MessageBus as MessageRouterPort
    from dipeo.domain.events import DomainEventBus, MessageBus
    from dipeo.domain.integrations.ports import APIKeyPort
    from dipeo.domain.diagram.ports import DiagramPort, DiagramCompiler, DiagramStorageSerializer
    from dipeo.domain.integrations.ports import ApiInvoker as IntegratedApiServicePort
    from dipeo.domain.integrations import ApiInvoker, ApiProvider, ApiProviderRegistry
    from dipeo.domain.diagram.ports import DiagramStorageSerializer as DiagramConverter
    from dipeo.domain.integrations.ports import ASTParserPort
    from dipeo.domain.conversation.ports import (
        ConversationRepository,
        PersonRepository,
        MemoryService,
    )
    from dipeo.domain.base.storage_port import FileSystemPort, ArtifactStorePort
    from dipeo.domain.diagram.ports import TemplateProcessorPort
    from dipeo.domain.events import EventEmitter
    from dipeo.domain.diagram.compilation import CompileTimeResolver
    from dipeo.domain.execution.resolution import TransformationEngine
    from dipeo.application.utils import PromptBuilder
    from dipeo.application.execution.handlers.condition.evaluators.expression_evaluator import ConditionEvaluator
    from dipeo.infrastructure.shared.adapters import (
        LocalBlobAdapter as BlobStoreAdapter,
        ArtifactStoreAdapter,
    )
    from dipeo.infrastructure.diagram.drivers.diagram_service import DiagramService
    from dipeo.domain.integrations.db_services import DBOperationsDomainService
    from dipeo.domain.execution.execution_context import ExecutionContext
    from dipeo.domain.diagram.models import ExecutableDiagram
    from dipeo.application.execution.use_cases import CliSessionService
    from dipeo.application.execution.use_cases import PrepareDiagramForExecutionUseCase
    from dipeo.application.execution.handler_factory import HandlerRegistry
    from dipeo.application.execution.orchestrators import ExecutionOrchestrator
    from dipeo.application.execution.use_cases.prompt_loading import PromptLoadingUseCase
    from dipeo.infrastructure.llm.adapters import LLMMemorySelectionAdapter
    from dipeo.application.diagram.use_cases import (
        CompileDiagramUseCase,
        ValidateDiagramUseCase,
        SerializeDiagramUseCase,
    )
    from dipeo.application.diagram.use_cases.load_diagram import LoadDiagramUseCase
    from typing import Any, Dict


# Core Infrastructure Services
LLM_SERVICE = ServiceKey["LLMServicePort"]("llm_service")
STATE_STORE = ServiceKey["StateStorePort"]("state_store")
FILE_SERVICE = ServiceKey["FileServicePort"]("file_service")
MESSAGE_ROUTER = ServiceKey["MessageRouterPort"]("message_router")
EVENT_BUS = ServiceKey["EventEmitter"]("event_bus")

# Execution State Services (from registry_tokens.py)
STATE_REPOSITORY = ServiceKey["ExecutionStateRepository"]("execution_state_repository")
STATE_SERVICE = ServiceKey["ExecutionStateService"]("execution_state_service")
STATE_CACHE = ServiceKey["ExecutionCachePort"]("execution_state_cache")

# Messaging Services (from registry_tokens.py)
MESSAGE_BUS = ServiceKey["MessageBus"]("message_bus")
DOMAIN_EVENT_BUS = ServiceKey["DomainEventBus"]("domain_event_bus")

# LLM Services (from registry_tokens.py)
# LLM_CLIENT = ServiceKey["LLMClient"]("llm_client")  # Removed - no longer needed
# LLM_REGISTRY = ServiceKey["dict[str, LLMClient]"]("llm_registry")  # Removed - no longer needed
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
DIAGRAM_COMPILER = ServiceKey["DiagramCompiler"]("diagram_compiler")  # From registry_tokens.py
DIAGRAM_SERIALIZER = ServiceKey["DiagramStorageSerializer"]("diagram_serializer")  # From registry_tokens.py
DIAGRAM_PORT = ServiceKey["DiagramPort"]("diagram_port")  # From registry_tokens.py

# External Integration Services
API_KEY_SERVICE = ServiceKey["APIKeyPort"]("api_key_service")
INTEGRATED_API_SERVICE = ServiceKey["IntegratedApiServicePort"]("integrated_api_service")
PROVIDER_REGISTRY = ServiceKey["Any"]("provider_registry")  # Provider registry for webhook integration
API_INVOKER = ServiceKey["ApiInvoker"]("api_invoker")  # From registry_tokens.py

# Parser Services
AST_PARSER = ServiceKey["ASTParserPort"]("ast_parser")

# Resolution Services (from registry_tokens.py)
TRANSFORMATION_ENGINE = ServiceKey["TransformationEngine"]("transformation_engine")

# Execution Context Services
DIAGRAM = ServiceKey["ExecutableDiagram"]("diagram")
EXECUTION_CONTEXT = ServiceKey["ExecutionContext"]("execution_context")
CURRENT_NODE_INFO = ServiceKey["Dict[str, Any]"]("current_node_info")
NODE_EXEC_COUNTS = ServiceKey["Dict[str, int]"]("node_exec_counts")

# Diagram Services
EXECUTION_SERVICE = ServiceKey["ExecutionService"]("execution_service")
COMPILATION_SERVICE = ServiceKey["CompilationService"]("compilation_service")
PREPARE_DIAGRAM_USE_CASE = ServiceKey["PrepareDiagramForExecutionUseCase"]("prepare_diagram_use_case")

# Diagram Use Cases
COMPILE_DIAGRAM_USE_CASE = ServiceKey["CompileDiagramUseCase"]("diagram.use_case.compile")
VALIDATE_DIAGRAM_USE_CASE = ServiceKey["ValidateDiagramUseCase"]("diagram.use_case.validate")
SERIALIZE_DIAGRAM_USE_CASE = ServiceKey["SerializeDiagramUseCase"]("diagram.use_case.serialize")
LOAD_DIAGRAM_USE_CASE = ServiceKey["LoadDiagramUseCase"]("diagram.use_case.load")

# Infrastructure Adapters
DATABASE = ServiceKey["DatabasePort"]("database")
NOTION_CLIENT = ServiceKey["NotionClientPort"]("notion_client")

# Validator Services
DIAGRAM_VALIDATOR = ServiceKey["DiagramValidator"]("diagram_validator")  # Active

# DEPRECATED: These validators are unused and will be removed
# TODO: Remove these in the next major refactor
# API_VALIDATOR = ServiceKey["APIValidator"]("api_validator")  # Implemented but unused
# FILE_VALIDATOR = ServiceKey["FileValidator"]("file_validator")  # Implemented but unused
# DATA_VALIDATOR = ServiceKey["DataValidator"]("data_validator")  # Implemented but unused
# EXECUTION_VALIDATOR = ServiceKey["ExecutionValidator"]("execution_validator")  # Implemented but unused
# NOTION_VALIDATOR = ServiceKey["NotionValidator"]("notion_validator")  # Not implemented
# LLM_VALIDATOR = ServiceKey["LLMValidator"]("llm_validator")  # Not implemented

# Business Logic Services
API_BUSINESS_LOGIC = ServiceKey["APIBusinessLogic"]("api_business_logic")
FILE_BUSINESS_LOGIC = ServiceKey["FileBusinessLogic"]("file_business_logic")
DIAGRAM_STATISTICS_SERVICE = ServiceKey["DiagramStatisticsService"]("diagram_statistics")
DIAGRAM_FORMAT_SERVICE = ServiceKey["DiagramFormatDetector"]("diagram_format_service")
LLM_DOMAIN_SERVICE = ServiceKey["LLMDomainService"]("llm_domain_service")

# Additional Services (newly added for migration)
CLI_SESSION_SERVICE = ServiceKey["CliSessionService"]("cli_session_service")

# Repository Services
API_KEY_REPOSITORY = ServiceKey["APIKeyRepository"]("api_key_repository")
CONVERSATION_REPOSITORY = ServiceKey["ConversationRepository"]("conversation_repository")
DIAGRAM_REPOSITORY = ServiceKey["DiagramRepository"]("diagram_repository")
EXECUTION_REPOSITORY = ServiceKey["ExecutionRepository"]("execution_repository")
NODE_OUTPUT_REPOSITORY = ServiceKey["NodeOutputRepository"]("node_output_repository")
PERSON_REPOSITORY = ServiceKey["PersonRepository"]("person_repository")

# Registry Services
NODE_REGISTRY = ServiceKey["HandlerRegistry"]("node_registry")
DOMAIN_SERVICE_REGISTRY = ServiceKey["Any"]("domain_service_registry")  # Currently unused
API_KEY_STORAGE = ServiceKey["Any"]("api_key_storage")  # Currently unused


__all__ = [
    # Core Infrastructure
    "LLM_SERVICE",
    "STATE_STORE",
    "FILE_SERVICE",
    "MESSAGE_ROUTER",
    "EVENT_BUS",
    
    # Execution State Services
    "STATE_REPOSITORY",
    "STATE_SERVICE",
    "STATE_CACHE",
    
    # Messaging Services
    "MESSAGE_BUS",
    "DOMAIN_EVENT_BUS",
    
    # LLM Services
    # "LLM_CLIENT",  # Removed - no longer needed
    # "LLM_REGISTRY",  # Removed - no longer needed
    "MEMORY_SERVICE",
    
    # Storage
    "BLOB_STORE",
    "FILESYSTEM_ADAPTER",
    
    # Application
    "EXECUTION_ORCHESTRATOR",
    "PROMPT_BUILDER",
    "TEMPLATE_PROCESSOR",
    "PROMPT_LOADING_SERVICE",
    "MEMORY_SELECTOR",
    
    # Domain
    "DB_OPERATIONS_SERVICE",
    "DIAGRAM_CONVERTER",
    "DIAGRAM_COMPILER",
    "DIAGRAM_SERIALIZER",
    "DIAGRAM_PORT",
    
    # External Integration
    "API_KEY_SERVICE",
    "INTEGRATED_API_SERVICE",
    "PROVIDER_REGISTRY",
    "API_INVOKER",
    
    # Parser
    "AST_PARSER",
    
    # Resolution Services
    "TRANSFORMATION_ENGINE",
    
    # Execution Context
    "DIAGRAM",
    "EXECUTION_CONTEXT",
    "CURRENT_NODE_INFO",
    "NODE_EXEC_COUNTS",
    
    # Diagram Services
    "EXECUTION_SERVICE",
    "COMPILATION_SERVICE",
    "PREPARE_DIAGRAM_USE_CASE",
    
    # Infrastructure
    "DATABASE",
    "NOTION_CLIENT",
    
    # Validators
    "DIAGRAM_VALIDATOR",
    # Deprecated - to be removed
    # "API_VALIDATOR",
    # "FILE_VALIDATOR",
    # "DATA_VALIDATOR",
    # "EXECUTION_VALIDATOR",
    # "NOTION_VALIDATOR",
    # "LLM_VALIDATOR",
    
    # Business Logic
    "API_BUSINESS_LOGIC",
    "FILE_BUSINESS_LOGIC",
    "DIAGRAM_STATISTICS_SERVICE",
    "DIAGRAM_FORMAT_SERVICE",
    "LLM_DOMAIN_SERVICE",
    
    # Additional Services
    "CLI_SESSION_SERVICE",
    
    # Repository Services
    "API_KEY_REPOSITORY",
    "CONVERSATION_REPOSITORY",
    "DIAGRAM_REPOSITORY",
    "EXECUTION_REPOSITORY",
    "NODE_OUTPUT_REPOSITORY",
    "PERSON_REPOSITORY",
    
    # Registry Services
    "NODE_REGISTRY",
    "DOMAIN_SERVICE_REGISTRY",
    "API_KEY_STORAGE",
]


