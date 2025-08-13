"""Service key definitions for DiPeO dependency injection."""

from typing import TYPE_CHECKING

from .service_registry import ServiceKey


# Type imports for service keys
if TYPE_CHECKING:
    from dipeo.core.ports import (
        LLMServicePort,
        StateStorePort,
        FileServicePort,
        MessageRouterPort,
        DiagramConverter,
        ExecutionObserver,
        APIKeyPort,
        DiagramPort,
        ASTParserPort,
        IntegratedApiServicePort,
    )
    from dipeo.domain.ports.storage import FileSystemPort
    from dipeo.domain.ports.template import TemplateProcessorPort
    from dipeo.core.events import EventEmitter
    from dipeo.application.services import (
        ConversationManagerImpl,
        PromptBuilder,
        ConditionEvaluator,
        PersonManagerImpl,
    )
    from dipeo.infrastructure.adapters.storage import (
        BlobStoreAdapter,
        ArtifactStoreAdapter,
    )
    from dipeo.infrastructure.services.diagram import DiagramService, DiagramConverterService
    from dipeo.domain.db.services import DBOperationsDomainService
    from dipeo.core.execution import ExecutionContext
    from dipeo.domain.diagram.models import ExecutableDiagram
    from dipeo.application.services.cli_session_service import CliSessionService
    from dipeo.application.execution.use_cases import PrepareDiagramForExecutionUseCase
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
DIAGRAM_CONVERTER_SERVICE = ServiceKey["DiagramConverterService"]("diagram_converter")
DIAGRAM_SERVICE_NEW = ServiceKey["DiagramService"]("diagram_service")

# External Integration Services
API_SERVICE = ServiceKey["APIService"]("api_service")
API_KEY_SERVICE = ServiceKey["APIKeyPort"]("api_key_service")
INTEGRATED_API_SERVICE = ServiceKey["IntegratedApiServicePort"]("integrated_api_service")

# Parser Services
AST_PARSER = ServiceKey["ASTParserPort"]("ast_parser")

# Execution Context Services
DIAGRAM = ServiceKey["ExecutableDiagram"]("diagram")
EXECUTION_CONTEXT = ServiceKey["ExecutionContext"]("execution_context")
CURRENT_NODE_INFO = ServiceKey["Dict[str, Any]"]("current_node_info")
NODE_EXEC_COUNTS = ServiceKey["Dict[str, int]"]("node_exec_counts")

# Diagram Services
DIAGRAM_SERVICE = ServiceKey["DiagramPort"]("diagram_service")
EXECUTION_SERVICE = ServiceKey["ExecutionService"]("execution_service")
COMPILATION_SERVICE = ServiceKey["CompilationService"]("compilation_service")
PREPARE_DIAGRAM_USE_CASE = ServiceKey["PrepareDiagramForExecutionUseCase"]("prepare_diagram_use_case")

# Infrastructure Adapters
DATABASE = ServiceKey["DatabasePort"]("database")
NOTION_CLIENT = ServiceKey["NotionClientPort"]("notion_client")

# Validator Services (to be removed in later phases)
API_VALIDATOR = ServiceKey["APIValidator"]("api_validator")
FILE_VALIDATOR = ServiceKey["FileValidator"]("file_validator")
DIAGRAM_VALIDATOR = ServiceKey["DiagramValidator"]("diagram_validator")
DATA_VALIDATOR = ServiceKey["DataValidator"]("data_validator")
NOTION_VALIDATOR = ServiceKey["NotionValidator"]("notion_validator")
LLM_VALIDATOR = ServiceKey["LLMValidator"]("llm_validator")
EXECUTION_VALIDATOR = ServiceKey["ExecutionValidator"]("execution_validator")

# Business Logic Services
API_BUSINESS_LOGIC = ServiceKey["APIBusinessLogic"]("api_business_logic")
FILE_BUSINESS_LOGIC = ServiceKey["FileBusinessLogic"]("file_business_logic")
DIAGRAM_STATISTICS_SERVICE = ServiceKey["DiagramStatisticsService"]("diagram_statistics")
DIAGRAM_FORMAT_SERVICE = ServiceKey["DiagramFormatDetector"]("diagram_format")
LLM_DOMAIN_SERVICE = ServiceKey["LLMDomainService"]("llm")

# Additional Services (newly added for migration)
CLI_SESSION_SERVICE = ServiceKey["CliSessionService"]("cli_session_service")


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
    "DIAGRAM_CONVERTER_SERVICE",
    "DIAGRAM_SERVICE_NEW",
    
    # External Integration
    "API_SERVICE",
    "API_KEY_SERVICE",
    "INTEGRATED_API_SERVICE",
    
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
    
    # Validators (deprecated)
    "API_VALIDATOR",
    "FILE_VALIDATOR",
    "DIAGRAM_VALIDATOR",
    "DATA_VALIDATOR",
    "NOTION_VALIDATOR",
    "LLM_VALIDATOR",
    "EXECUTION_VALIDATOR",
    
    # Business Logic
    "API_BUSINESS_LOGIC",
    "FILE_BUSINESS_LOGIC",
    "DIAGRAM_STATISTICS_SERVICE",
    "DIAGRAM_FORMAT_SERVICE",
    "LLM_DOMAIN_SERVICE",
    
    # Additional Services
    "CLI_SESSION_SERVICE",
]