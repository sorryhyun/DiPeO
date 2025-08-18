"""Service key definitions for DiPeO dependency injection."""

from typing import TYPE_CHECKING

from .service_registry import ServiceKey


# Type imports for service keys
if TYPE_CHECKING:
    from dipeo.application.compat_imports import (
        LLMServicePort,
        StateStorePort,
        FileServicePort,
        MessageRouterPort,
        DiagramConverter,
        ExecutionObserver,
        APIKeyPort,
        DiagramPort,
        IntegratedApiServicePort,
    )
    from dipeo.domain.parsers.ports import ASTParserPort
    from dipeo.domain.ports import (
        APIKeyRepository,
        ConversationRepository,
        DiagramRepository,
        ExecutionRepository,
        NodeOutputRepository,
        PersonRepository,
    )
    from dipeo.domain.ports.storage import FileSystemPort
    from dipeo.domain.ports.template import TemplateProcessorPort
    from dipeo.domain.events import EventEmitter
    from dipeo.application.utils import PromptBuilder
    from dipeo.application.execution.handlers.condition.evaluators.expression_evaluator import ConditionEvaluator
    from dipeo.infrastructure.shared.adapters import (
        LocalBlobAdapter as BlobStoreAdapter,
        ArtifactStoreAdapter,
    )
    from dipeo.infrastructure.services.diagram import DiagramService
    from dipeo.domain.integrations.db_services import DBOperationsDomainService
    from dipeo.domain.execution.execution_context import ExecutionContext
    from dipeo.domain.diagram.models import ExecutableDiagram
    from dipeo.application.execution.use_cases import CliSessionService
    from dipeo.application.execution.use_cases import PrepareDiagramForExecutionUseCase
    from dipeo.application.execution.handler_factory import HandlerRegistry
    from typing import Any, Dict


# Core Infrastructure Services
LLM_SERVICE = ServiceKey["LLMServicePort"]("llm_service")
STATE_STORE = ServiceKey["StateStorePort"]("state_store")
FILE_SERVICE = ServiceKey["FileServicePort"]("file_service")
MESSAGE_ROUTER = ServiceKey["MessageRouterPort"]("message_router")
EVENT_BUS = ServiceKey["EventEmitter"]("event_bus")

# Storage Services
BLOB_STORE = ServiceKey["BlobStoreAdapter"]("blob_store")
ARTIFACT_STORE = ServiceKey["ArtifactStoreAdapter"]("artifact_store")
FILESYSTEM_ADAPTER = ServiceKey["FileSystemPort"]("filesystem_adapter")

# Application Services
CONVERSATION_MANAGER = ServiceKey["ConversationManagerImpl"]("conversation_manager")
CONVERSATION_SERVICE = ServiceKey["ConversationManagerImpl"]("conversation_service")  # Alias
PROMPT_BUILDER = ServiceKey["PromptBuilder"]("prompt_builder")
PERSON_MANAGER = ServiceKey["PersonManagerImpl"]("person_manager")
TEMPLATE_PROCESSOR = ServiceKey["TemplateProcessorPort"]("template_processor")

# Domain Services
DB_OPERATIONS_SERVICE = ServiceKey["DBOperationsDomainService"]("db_operations_service")
DIAGRAM_CONVERTER = ServiceKey["DiagramConverter"]("diagram_converter")

# External Integration Services
API_SERVICE = ServiceKey["APIService"]("api_service")
API_KEY_SERVICE = ServiceKey["APIKeyPort"]("api_key_service")
INTEGRATED_API_SERVICE = ServiceKey["IntegratedApiServicePort"]("integrated_api_service")
PROVIDER_REGISTRY = ServiceKey["Any"]("provider_registry")  # Provider registry for webhook integration

# Parser Services
AST_PARSER = ServiceKey["ASTParserPort"]("ast_parser")

# Execution Context Services
DIAGRAM = ServiceKey["ExecutableDiagram"]("diagram")
EXECUTION_CONTEXT = ServiceKey["ExecutionContext"]("execution_context")
CURRENT_NODE_INFO = ServiceKey["Dict[str, Any]"]("current_node_info")
NODE_EXEC_COUNTS = ServiceKey["Dict[str, int]"]("node_exec_counts")

# Diagram Services
DIAGRAM_SERVICE = ServiceKey["DiagramService"]("diagram_service")
EXECUTION_SERVICE = ServiceKey["ExecutionService"]("execution_service")
COMPILATION_SERVICE = ServiceKey["CompilationService"]("compilation_service")
PREPARE_DIAGRAM_USE_CASE = ServiceKey["PrepareDiagramForExecutionUseCase"]("prepare_diagram_use_case")

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
    
    # Storage
    "BLOB_STORE",
    "ARTIFACT_STORE",
    "FILESYSTEM_ADAPTER",
    
    # Application
    "CONVERSATION_MANAGER",
    "CONVERSATION_SERVICE",
    "PROMPT_BUILDER",
    "PERSON_MANAGER",
    "TEMPLATE_PROCESSOR",
    
    # Domain
    "DB_OPERATIONS_SERVICE",
    "DIAGRAM_CONVERTER",
    
    # External Integration
    "API_SERVICE",
    "API_KEY_SERVICE",
    "INTEGRATED_API_SERVICE",
    "PROVIDER_REGISTRY",
    
    # Parser
    "AST_PARSER",
    
    # Execution Context
    "DIAGRAM",
    "EXECUTION_CONTEXT",
    "CURRENT_NODE_INFO",
    "NODE_EXEC_COUNTS",
    
    # Diagram Services
    "DIAGRAM_SERVICE",
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