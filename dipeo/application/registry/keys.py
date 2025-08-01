"""Service key definitions for DiPeO dependency injection."""

from typing import TYPE_CHECKING

from .service_registry import ServiceKey


# Type imports for service keys
if TYPE_CHECKING:
    from dipeo.core.ports import (
        LLMServicePort,
        StateStorePort,
        FileServicePort,
        NotionServicePort,
        MessageRouterPort,
        DiagramConverter,
        ExecutionObserver,
        APIKeyPort,
        DiagramPort,
        ASTParserPort,
    )
    from dipeo.application.services import (
        ConversationManagerImpl,
        PromptBuilder,
        ConditionEvaluator,
        PersonManagerImpl,
    )
    from dipeo.infrastructure.adapters.storage import (
        DiagramStorageAdapter,
        BlobStoreAdapter,
        ArtifactStoreAdapter,
    )
    from dipeo.domain.ports.storage import DiagramStoragePort
    from dipeo.infrastructure.services.diagram import DiagramService, DiagramConverterService
    from dipeo.domain.db.services import DBOperationsDomainService
    from dipeo.core.dynamic import ExecutionContext
    from dipeo.core.static import ExecutableDiagram
    from dipeo.application.services.cli_session_service import CliSessionService
    from dipeo.application.execution.execution_runtime import ExecutionRuntime
    from typing import Any, Dict


# Core Infrastructure Services
LLM_SERVICE = ServiceKey["LLMServicePort"]("llm_service")
STATE_STORE = ServiceKey["StateStorePort"]("state_store")
FILE_SERVICE = ServiceKey["FileServicePort"]("file_service")
MESSAGE_ROUTER = ServiceKey["MessageRouterPort"]("message_router")

# Storage Services
BLOB_STORE = ServiceKey["BlobStoreAdapter"]("blob_store")
ARTIFACT_STORE = ServiceKey["ArtifactStoreAdapter"]("artifact_store")
DIAGRAM_STORAGE_SERVICE = ServiceKey["DiagramStorageAdapter"]("diagram_storage_service")
DIAGRAM_STORAGE = ServiceKey["DiagramStoragePort"]("diagram_storage_adapter")
FILESYSTEM_ADAPTER = ServiceKey["FileSystemPort"]("filesystem_adapter")

# Application Services
CONVERSATION_MANAGER = ServiceKey["ConversationManagerImpl"]("conversation_manager")
CONVERSATION_SERVICE = ServiceKey["ConversationManagerImpl"]("conversation_service")  # Alias
PROMPT_BUILDER = ServiceKey["PromptBuilder"]("prompt_builder")
CONDITION_EVALUATION_SERVICE = ServiceKey["ConditionEvaluator"]("condition_evaluation_service")
PERSON_MANAGER = ServiceKey["PersonManagerImpl"]("person_manager")

# Domain Services
DB_OPERATIONS_SERVICE = ServiceKey["DBOperationsDomainService"]("db_operations_service")
DIAGRAM_CONVERTER = ServiceKey["DiagramConverter"]("diagram_converter")
DIAGRAM_CONVERTER_SERVICE = ServiceKey["DiagramConverterService"]("diagram_converter")
DIAGRAM_SERVICE_NEW = ServiceKey["DiagramService"]("diagram_service")

# External Integration Services
API_SERVICE = ServiceKey["APIService"]("api_service")
NOTION_SERVICE = ServiceKey["NotionServicePort"]("notion_service")
API_KEY_SERVICE = ServiceKey["APIKeyPort"]("api_key_service")

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
DIAGRAM_OPERATIONS_SERVICE = ServiceKey["DiagramOperationsService"]("diagram_operations")
DIAGRAM_FORMAT_SERVICE = ServiceKey["DiagramFormatService"]("diagram_format")
LLM_DOMAIN_SERVICE = ServiceKey["LLMDomainService"]("llm")

# Additional Services (newly added for migration)
CLI_SESSION_SERVICE = ServiceKey["CliSessionService"]("cli_session_service")
EXECUTION_RUNTIME = ServiceKey["ExecutionRuntime"]("execution_runtime")


__all__ = [
    # Core Infrastructure
    "LLM_SERVICE",
    "STATE_STORE",
    "FILE_SERVICE",
    "MESSAGE_ROUTER",
    
    # Storage
    "BLOB_STORE",
    "ARTIFACT_STORE",
    "DIAGRAM_STORAGE_SERVICE",
    "DIAGRAM_STORAGE",
    "FILESYSTEM_ADAPTER",
    
    # Application
    "CONVERSATION_MANAGER",
    "CONVERSATION_SERVICE",
    "PROMPT_BUILDER",
    "CONDITION_EVALUATION_SERVICE",
    "PERSON_MANAGER",
    
    # Domain
    "DB_OPERATIONS_SERVICE",
    "DIAGRAM_CONVERTER",
    "DIAGRAM_CONVERTER_SERVICE",
    "DIAGRAM_SERVICE_NEW",
    
    # External Integration
    "API_SERVICE",
    "NOTION_SERVICE",
    "API_KEY_SERVICE",
    
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
    "DIAGRAM_OPERATIONS_SERVICE",
    "DIAGRAM_FORMAT_SERVICE",
    "LLM_DOMAIN_SERVICE",
    
    # Additional Services
    "CLI_SESSION_SERVICE",
    "EXECUTION_RUNTIME",
]