"""Service key definitions for DiPeO dependency injection.

This module defines all service keys used throughout the DiPeO application
for dependency injection. Keys are organized hierarchically and include
metadata for enhanced safety and documentation.
"""

from typing import TYPE_CHECKING

from .enhanced_service_registry import (
    EnhancedServiceKey as ServiceKey,
)
from .enhanced_service_registry import (
    ServiceType,
)

if TYPE_CHECKING:
    pass


# =============================================================================
# CORE INFRASTRUCTURE SERVICES
# =============================================================================

# Critical services
EVENT_BUS = ServiceKey["EventBus"](
    "event_bus",
    service_type=ServiceType.CORE,
    description="Central event distribution system for async communication",
)

STATE_STORE = ServiceKey["StateStorePort"](
    "state_store",
    service_type=ServiceType.CORE,
    description="Persistent state storage with caching",
)

# Core infrastructure services
LLM_SERVICE = ServiceKey["LLMServicePort"](
    "llm_service", service_type=ServiceType.CORE, description="LLM service for AI interactions"
)

FILE_SERVICE = ServiceKey["FileServicePort"](
    "file_service", service_type=ServiceType.CORE, description="File system operations service"
)

MESSAGE_ROUTER = ServiceKey["MessageRouterPort"](
    "message_router",
    service_type=ServiceType.CORE,
    description="Message routing for inter-process communication",
)

NODE_REGISTRY = ServiceKey["HandlerRegistry"](
    "node_registry", service_type=ServiceType.CORE, description="Registry for node handlers"
)

PROVIDER_REGISTRY = ServiceKey["Any"](
    "provider_registry",
    service_type=ServiceType.CORE,
    description="Registry for integrated API providers",
)

# =============================================================================
# STATE MANAGEMENT SERVICES (Hierarchical)
# =============================================================================

STATE_REPOSITORY = ServiceKey["ExecutionStateRepository"](
    "state.repository",
    service_type=ServiceType.REPOSITORY,
    description="Repository for execution state persistence",
)

STATE_SERVICE = ServiceKey["ExecutionStateService"](
    "state.service",
    service_type=ServiceType.APPLICATION,
    description="Application service for state management",
    dependencies=("state.repository",),
)

STATE_CACHE = ServiceKey["ExecutionCachePort"](
    "state.cache", service_type=ServiceType.CORE, description="Cache layer for execution state"
)

# =============================================================================
# EXECUTION & ORCHESTRATION SERVICES
# =============================================================================

EXECUTION_ORCHESTRATOR = ServiceKey["ExecutionOrchestrator"](
    "execution.orchestrator",
    service_type=ServiceType.APPLICATION,
    description="Central orchestrator for execution concerns",
    dependencies=("llm_service", "state.service"),
)

EXECUTION_SERVICE = ServiceKey["ExecutionService"](
    "execution.service",
    service_type=ServiceType.APPLICATION,
    description="Service for diagram execution",
)

EXECUTION_CONTEXT = ServiceKey["ExecutionContext"](
    "execution.context",
    service_type=ServiceType.APPLICATION,
    description="Context object for execution runtime",
)

MEMORY_SERVICE = ServiceKey["MemoryService"](
    "execution.memory_service",
    service_type=ServiceType.APPLICATION,
    description="Service for conversation memory management",
)

MEMORY_SELECTOR = ServiceKey["LLMMemorySelectionAdapter"](
    "execution.memory_selector",
    service_type=ServiceType.ADAPTER,
    description="AI-powered memory selection adapter",
)

# Execution context details
DIAGRAM = ServiceKey["ExecutableDiagram"](
    "execution.diagram",
    service_type=ServiceType.APPLICATION,
    description="Currently executing diagram",
)

CURRENT_NODE_INFO = ServiceKey["Dict[str, Any]"](
    "execution.current_node_info",
    service_type=ServiceType.APPLICATION,
    description="Information about currently executing node",
)

NODE_EXEC_COUNTS = ServiceKey["Dict[str, int]"](
    "execution.node_exec_counts",
    service_type=ServiceType.APPLICATION,
    description="Execution counts for nodes",
)

# =============================================================================
# DIAGRAM OPERATIONS (Hierarchical Use Cases)
# =============================================================================

DIAGRAM_PORT = ServiceKey["DiagramPort"](
    "diagram.port", service_type=ServiceType.DOMAIN, description="Port for diagram operations"
)

DIAGRAM_COMPILER = ServiceKey["DiagramCompiler"](
    "diagram.compiler",
    service_type=ServiceType.DOMAIN,
    description="Compiler for diagram compilation",
)

DIAGRAM_SERIALIZER = ServiceKey["DiagramStorageSerializer"](
    "diagram.serializer",
    service_type=ServiceType.DOMAIN,
    description="Serializer for diagram storage",
)

# Diagram use cases (explicit nesting)
COMPILE_DIAGRAM_USE_CASE = ServiceKey["CompileDiagramUseCase"](
    "diagram.use_case.compile",
    service_type=ServiceType.APPLICATION,
    description="Use case for compiling diagrams",
    dependencies=("diagram.compiler",),
)

VALIDATE_DIAGRAM_USE_CASE = ServiceKey["ValidateDiagramUseCase"](
    "diagram.use_case.validate",
    service_type=ServiceType.APPLICATION,
    description="Use case for validating diagram structure",
)

SERIALIZE_DIAGRAM_USE_CASE = ServiceKey["SerializeDiagramUseCase"](
    "diagram.use_case.serialize",
    service_type=ServiceType.APPLICATION,
    description="Use case for serializing diagrams",
    dependencies=("diagram.serializer",),
)

LOAD_DIAGRAM_USE_CASE = ServiceKey["LoadDiagramUseCase"](
    "diagram.use_case.load",
    service_type=ServiceType.APPLICATION,
    description="Use case for loading diagrams from various sources",
)

PREPARE_DIAGRAM_USE_CASE = ServiceKey["PrepareDiagramForExecutionUseCase"](
    "diagram.use_case.prepare",
    service_type=ServiceType.APPLICATION,
    description="Use case for preparing diagrams for execution",
    dependencies=("diagram.use_case.load", "diagram.use_case.validate", "diagram.use_case.compile"),
)

# =============================================================================
# STORAGE & FILESYSTEM SERVICES
# =============================================================================

BLOB_STORE = ServiceKey["BlobStoreAdapter"](
    "storage.blob_store",
    service_type=ServiceType.ADAPTER,
    description="Adapter for blob storage operations",
)

FILESYSTEM_ADAPTER = ServiceKey["FileSystemPort"](
    "storage.filesystem",
    service_type=ServiceType.ADAPTER,
    description="Adapter for filesystem operations",
)

DATABASE = ServiceKey["DatabasePort"](
    "storage.database",
    service_type=ServiceType.ADAPTER,
    description="Database adapter for persistence",
)

# =============================================================================
# EXTERNAL INTEGRATION SERVICES
# =============================================================================

API_KEY_SERVICE = ServiceKey["APIKeyPort"](
    "integration.api_key_service",
    service_type=ServiceType.ADAPTER,
    description="Service for managing API keys",
)

INTEGRATED_API_SERVICE = ServiceKey["IntegratedApiServicePort"](
    "integration.integrated_api",
    service_type=ServiceType.ADAPTER,
    description="Service for integrated API operations",
)

API_INVOKER = ServiceKey["ApiInvoker"](
    "integration.api_invoker",
    service_type=ServiceType.APPLICATION,
    description="Service for invoking external APIs",
)

NOTION_CLIENT = ServiceKey["NotionClientPort"](
    "integration.notion_client",
    service_type=ServiceType.ADAPTER,
    description="Client for Notion API integration",
)

# =============================================================================
# PROCESSING SERVICES
# =============================================================================

TEMPLATE_PROCESSOR = ServiceKey["TemplateProcessorPort"](
    "processing.template",
    service_type=ServiceType.APPLICATION,
    description="Service for processing templates",
)

PROMPT_BUILDER = ServiceKey["PromptBuilder"](
    "processing.prompt_builder",
    service_type=ServiceType.APPLICATION,
    description="Service for building prompts with template substitution",
    dependencies=("processing.template",),
)

AST_PARSER = ServiceKey["ASTParserPort"](
    "processing.ast_parser",
    service_type=ServiceType.APPLICATION,
    description="Parser for abstract syntax trees",
)

TRANSFORMATION_ENGINE = ServiceKey["TransformationEngine"](
    "processing.transformation",
    service_type=ServiceType.DOMAIN,
    description="Engine for data transformations",
)

PROMPT_LOADING_SERVICE = ServiceKey["PromptLoadingUseCase"](
    "processing.prompt_loading",
    service_type=ServiceType.APPLICATION,
    description="Service for loading and processing prompts",
)

# =============================================================================
# DOMAIN SERVICES
# =============================================================================

DB_OPERATIONS_SERVICE = ServiceKey["DBOperationsDomainService"](
    "domain.db_operations",
    service_type=ServiceType.DOMAIN,
    description="Domain service for database operations",
)

DIAGRAM_VALIDATOR = ServiceKey["DiagramValidator"](
    "domain.diagram_validator",
    service_type=ServiceType.DOMAIN,
    description="Service for validating diagram structure and integrity",
)

# =============================================================================
# REPOSITORY SERVICES
# =============================================================================

API_KEY_REPOSITORY = ServiceKey["APIKeyRepository"](
    "repository.api_key",
    service_type=ServiceType.REPOSITORY,
    description="Repository for API key management",
)

CONVERSATION_REPOSITORY = ServiceKey["ConversationRepository"](
    "repository.conversation",
    service_type=ServiceType.REPOSITORY,
    description="Repository for conversation persistence",
)

DIAGRAM_REPOSITORY = ServiceKey["DiagramRepository"](
    "repository.diagram",
    service_type=ServiceType.REPOSITORY,
    description="Repository for diagram storage",
)

EXECUTION_REPOSITORY = ServiceKey["ExecutionRepository"](
    "repository.execution",
    service_type=ServiceType.REPOSITORY,
    description="Repository for execution state",
)

PERSON_REPOSITORY = ServiceKey["PersonRepository"](
    "repository.person",
    service_type=ServiceType.REPOSITORY,
    description="Repository for person/agent management",
)

# =============================================================================
# APPLICATION SERVICES
# =============================================================================

CLI_SESSION_SERVICE = ServiceKey["CliSessionService"](
    "application.cli_session",
    service_type=ServiceType.APPLICATION,
    description="Service for CLI session management",
)


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
    "API_INVOKER",
    # Repository
    "API_KEY_REPOSITORY",
    # External Integration
    "API_KEY_SERVICE",
    "AST_PARSER",
    # Storage & Filesystem
    "BLOB_STORE",
    # Application
    "CLI_SESSION_SERVICE",
    "COMPILE_DIAGRAM_USE_CASE",
    "CONVERSATION_REPOSITORY",
    "CURRENT_NODE_INFO",
    "DATABASE",
    # Domain
    "DB_OPERATIONS_SERVICE",
    "DIAGRAM",
    "DIAGRAM_COMPILER",
    # Diagram Operations
    "DIAGRAM_PORT",
    "DIAGRAM_REPOSITORY",
    "DIAGRAM_SERIALIZER",
    "DIAGRAM_VALIDATOR",
    # Core Infrastructure
    "EVENT_BUS",
    "EXECUTION_CONTEXT",
    # Execution & Orchestration
    "EXECUTION_ORCHESTRATOR",
    "EXECUTION_REPOSITORY",
    "EXECUTION_SERVICE",
    "FILESYSTEM_ADAPTER",
    "FILE_SERVICE",
    "INTEGRATED_API_SERVICE",
    "LLM_SERVICE",
    "LOAD_DIAGRAM_USE_CASE",
    "MEMORY_SELECTOR",
    "MEMORY_SERVICE",
    "MESSAGE_ROUTER",
    "NODE_EXEC_COUNTS",
    "NODE_REGISTRY",
    "NOTION_CLIENT",
    "PERSON_REPOSITORY",
    "PREPARE_DIAGRAM_USE_CASE",
    "PROMPT_BUILDER",
    "PROMPT_LOADING_SERVICE",
    "PROVIDER_REGISTRY",
    "SERIALIZE_DIAGRAM_USE_CASE",
    "STATE_CACHE",
    # State Management
    "STATE_REPOSITORY",
    "STATE_SERVICE",
    "STATE_STORE",
    # Processing
    "TEMPLATE_PROCESSOR",
    "TRANSFORMATION_ENGINE",
    "VALIDATE_DIAGRAM_USE_CASE",
]
