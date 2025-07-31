"""Simplified container system for DiPeO monorepo.

This module provides a clean 3-container architecture:
- CoreContainer: Immutable domain services (no external dependencies)
- InfrastructureContainer: External adapters (storage, LLM, etc.)
- ApplicationContainer: Use cases and orchestration
"""

from pathlib import Path
from typing import Any

from dipeo.application.registry import ServiceRegistry, ServiceKey
from dipeo.application.registry.keys import (
    API_KEY_SERVICE,
    API_SERVICE,
    ARTIFACT_STORE,
    AST_PARSER,
    BLOB_STORE,
    COMPILATION_SERVICE,
    CONDITION_EVALUATION_SERVICE,
    CONVERSATION_MANAGER,
    DB_OPERATIONS_SERVICE,
    DIAGRAM_CONVERTER,
    DIAGRAM_STORAGE,
    DIAGRAM_STORAGE_SERVICE,
    DIAGRAM_VALIDATOR,
    EXECUTION_SERVICE,
    LLM_SERVICE,
    MESSAGE_ROUTER,
    NOTION_SERVICE,
    PERSON_MANAGER,
    PROMPT_BUILDER,
    STATE_STORE,
)

# Define additional service keys that aren't in the main registry yet
TEMPLATE_PROCESSOR = ServiceKey("template_processor")
NODE_REGISTRY = ServiceKey("node_registry")
DOMAIN_SERVICE_REGISTRY = ServiceKey("domain_service_registry")
FILESYSTEM_ADAPTER = ServiceKey("filesystem_adapter")
API_KEY_STORAGE = ServiceKey("api_key_storage")
from dipeo.core.config import Config


class CoreContainer:
    """Immutable core services with no external dependencies.
    
    Contains pure domain logic, validators, and business rules.
    These services can be safely shared across all execution contexts.
    """
    
    def __init__(self, registry: ServiceRegistry):
        self.registry = registry
        self._setup_domain_services()
    
    def _setup_domain_services(self):
        """Register pure domain services."""
        # Domain validators (pure logic, no I/O)
        # DiagramValidator needs api_key_service, so we use a factory
        from dipeo.domain.validators import DiagramValidator
        self.registry.register(
            DIAGRAM_VALIDATOR,
            lambda: DiagramValidator(
                api_key_service=self.registry.resolve(API_KEY_SERVICE)
            )
        )
        
        # Template processing (pure transformations)
        from dipeo.application.utils.template import TemplateProcessor
        self.registry.register(
            TEMPLATE_PROCESSOR,
            TemplateProcessor()
        )
        
        # Prompt building (pure logic)
        from dipeo.application.utils import PromptBuilder
        self.registry.register(
            PROMPT_BUILDER,
            PromptBuilder()
        )
        
        # Node registry (handler mapping)
        from dipeo.application import get_global_registry
        self.registry.register(
            NODE_REGISTRY,
            get_global_registry()
        )


class InfrastructureContainer:
    """External integration adapters.
    
    Contains all I/O operations, external service integrations,
    and infrastructure concerns. Configured based on environment.
    """
    
    def __init__(self, registry: ServiceRegistry, config: Config):
        self.registry = registry
        self.config = config
        self._setup_adapters()
    
    def _setup_adapters(self):
        """Register infrastructure adapters based on configuration."""
        # Storage adapters
        self._setup_storage_adapters()
        
        # LLM service
        self._setup_llm_adapter()
        
        # Additional infrastructure services
        self._setup_infrastructure_services()
    
    def _setup_storage_adapters(self):
        """Configure storage adapters based on environment."""
        # Use existing infrastructure implementations
        from dipeo.infrastructure.adapters.storage import LocalFileSystemAdapter
        
        # Create filesystem adapter (always needed)
        filesystem_adapter = LocalFileSystemAdapter(base_path=Path(self.config.base_dir))
        self.registry.register(FILESYSTEM_ADAPTER, filesystem_adapter)
        
        # API key storage - APIKeyService handles its own file storage
        
        # API key service with file-based storage
        from dipeo.application.services.apikey_service import APIKeyService
        api_key_path = Path(self.config.base_dir) / "files" / "apikeys.json"
        self.registry.register(
            API_KEY_SERVICE,
            APIKeyService(file_path=api_key_path)
        )
        
        # Diagram storage adapter
        from dipeo.infrastructure.adapters.storage import DiagramStorageAdapter
        diagram_storage_adapter = DiagramStorageAdapter(
            filesystem=filesystem_adapter,
            base_path=Path(self.config.base_dir) / "files"
        )
        # Register under both keys for backward compatibility
        self.registry.register(DIAGRAM_STORAGE, diagram_storage_adapter)
        self.registry.register(DIAGRAM_STORAGE_SERVICE, diagram_storage_adapter)
        
        # Artifact store (using existing patterns)
        self.registry.register(
            ARTIFACT_STORE,
            lambda: self.registry.resolve(DIAGRAM_STORAGE)
        )
    
    def _setup_llm_adapter(self):
        """Configure LLM service based on environment."""
        # Use existing LLM infrastructure service
        from dipeo.infra.llm.service import LLMInfraService
        from dipeo.domain.llm import LLMDomainService
        
        # Get API key service from registry
        api_key_service = self.registry.resolve(API_KEY_SERVICE)
        
        # Create LLM domain service
        llm_domain_service = LLMDomainService()
        
        # Create and register LLM infrastructure service
        self.registry.register(
            LLM_SERVICE,
            LLMInfraService(
                api_key_service=api_key_service,
                llm_domain_service=llm_domain_service
            )
        )
    
    def _setup_infrastructure_services(self):
        """Set up additional infrastructure services."""
        # State store - use None for CLI, server should override
        # For server usage, this should be overridden with StateRegistry
        self.registry.register(
            STATE_STORE,
            None  # Server must override this
        )
        
        # Message router - use None for CLI, server should override 
        # For server usage, this should be overridden with MessageRouter
        self.registry.register(
            MESSAGE_ROUTER,
            None  # Server must override this
        )
        
        # Blob store
        from dipeo.infrastructure.adapters.storage import LocalBlobAdapter
        self.registry.register(
            BLOB_STORE,
            LocalBlobAdapter(
                base_path=str(Path(self.config.base_dir) / "blobs")
            )
        )
        
        # API service - None for now, can be added when needed
        self.registry.register(
            API_SERVICE,
            None  # Override when API calls are needed
        )
        
        # Notion service - None for now
        self.registry.register(
            NOTION_SERVICE,
            None  # Override when Notion integration is needed
        )
        
        # AST parser - None for now
        self.registry.register(
            AST_PARSER,
            None  # Override when AST parsing is needed
        )


class ApplicationContainer:
    """Application services and use cases.
    
    Contains high-level orchestration, compilation pipeline,
    and execution services. Depends on both Core and Infrastructure.
    """
    
    def __init__(self, registry: ServiceRegistry):
        self.registry = registry
        self._setup_application_services()
    
    def _setup_application_services(self):
        """Register application-level services with dependencies."""
        # Use existing compilation service
        from dipeo.application.resolution import StaticDiagramCompiler
        self.registry.register(
            COMPILATION_SERVICE,
            StaticDiagramCompiler()
        )
        
        # Diagram converter service
        from dipeo.infrastructure.services.diagram import DiagramConverterService
        self.registry.register(
            DIAGRAM_CONVERTER,
            DiagramConverterService()
        )
        
        # Application services
        self._setup_app_services()
    
    def _setup_app_services(self):
        """Set up application-level services."""
        # DB operations service
        from dipeo.domain.db.services import DBOperationsDomainService
        self.registry.register(
            DB_OPERATIONS_SERVICE,
            DBOperationsDomainService()
        )
        
        # Condition evaluator
        from dipeo.application.utils.evaluator import ConditionEvaluator
        self.registry.register(
            CONDITION_EVALUATION_SERVICE,
            ConditionEvaluator()
        )
        
        # Person manager
        from dipeo.application.services.person_manager_impl import PersonManagerImpl
        self.registry.register(
            PERSON_MANAGER,
            PersonManagerImpl()
        )
        
        # Conversation manager
        from dipeo.application.services.conversation_manager_impl import ConversationManagerImpl
        conversation_manager = ConversationManagerImpl()
        self.registry.register(CONVERSATION_MANAGER, conversation_manager)
        # Also register as CONVERSATION_SERVICE (alias)
        from dipeo.application.registry.keys import CONVERSATION_SERVICE
        self.registry.register(CONVERSATION_SERVICE, conversation_manager)
        
        # Integrated diagram service
        from dipeo.infrastructure.services.diagram import DiagramService
        from dipeo.application.registry.keys import INTEGRATED_DIAGRAM_SERVICE
        self.registry.register(
            INTEGRATED_DIAGRAM_SERVICE,
            lambda: DiagramService(
                storage=self.registry.resolve(DIAGRAM_STORAGE),
                converter=None  # Will create default converter
            )
        )
        
        # Execution service with dependencies
        from dipeo.application.execution.use_cases import ExecuteDiagramUseCase
        self.registry.register(
            EXECUTION_SERVICE,
            lambda: ExecuteDiagramUseCase(
                file_service=self.registry.resolve(DIAGRAM_STORAGE),
                state_store=self.registry.resolve(STATE_STORE),
                message_router=self.registry.resolve(MESSAGE_ROUTER),
                compilation_service=self.registry.resolve(COMPILATION_SERVICE),
                diagram_converter_service=self.registry.resolve(DIAGRAM_CONVERTER),
                llm_service=self.registry.resolve(LLM_SERVICE),
                prompt_builder=self.registry.resolve(PROMPT_BUILDER),
                db_operations_service=self.registry.resolve(DB_OPERATIONS_SERVICE),
                condition_evaluator=self.registry.resolve(CONDITION_EVALUATION_SERVICE),
                api_service=self.registry.resolve(API_SERVICE),
                notion_service=self.registry.resolve(NOTION_SERVICE),
                person_manager=self.registry.resolve(PERSON_MANAGER),
                conversation_manager=self.registry.resolve(CONVERSATION_MANAGER),
                api_key_service=self.registry.resolve(API_KEY_SERVICE),
                blob_store=self.registry.resolve(BLOB_STORE),
                ast_parser=self.registry.resolve(AST_PARSER),
            )
        )


class Container:
    """Main container orchestrating the 3-container architecture.
    
    This simplified design removes profiles and complex initialization,
    making it easier to understand and maintain in a monorepo context.
    """
    
    def __init__(self, config: Config | None = None):
        # Use provided config or load from environment
        self.config = config or Config.from_env()
        
        # Single shared registry for all containers
        self.registry = ServiceRegistry()
        
        # Initialize containers in dependency order
        self.core = CoreContainer(self.registry)
        self.infrastructure = InfrastructureContainer(self.registry, self.config)
        self.application = ApplicationContainer(self.registry)
    
    def get_service(self, key: str | ServiceKey) -> Any:
        """Get a service by key from the registry.
        
        Args:
            key: Service key (string or ServiceKey object)
            
        Returns:
            The service instance
        """
        if isinstance(key, str):
            # Create a ServiceKey from string for backward compatibility
            service_key = ServiceKey(key)
        else:
            service_key = key
        return self.registry.resolve(service_key)
    
    async def initialize(self):
        """Initialize async resources if needed."""
        # Initialize APIKeyService to load keys from file
        api_key_service = self.registry.resolve(API_KEY_SERVICE)
        if api_key_service and hasattr(api_key_service, 'initialize'):
            await api_key_service.initialize()
    
    async def shutdown(self):
        """Clean up resources on shutdown."""
        # Clean up any open connections, files, etc.
        pass
    
    def create_sub_container(self, execution_id: str) -> "Container":
        """Create a sub-container for isolated execution.
        
        In this simplified design:
        - Core services are always shared (immutable)
        - Infrastructure is shared (connection pooling)
        - Only execution context is isolated
        
        Args:
            execution_id: The execution ID for the sub-container (reserved for future use)
        """
        # For now, return self - can add isolation later if needed
        # The execution service handles its own state isolation
        return self


# Convenience functions for backward compatibility
async def init_resources(container: Container):
    """Initialize container resources."""
    await container.initialize()


async def shutdown_resources(container: Container):
    """Shutdown container resources."""
    await container.shutdown()