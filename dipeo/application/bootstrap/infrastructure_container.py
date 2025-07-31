from pathlib import Path
from typing import Any

from dipeo.application.registry import ServiceRegistry, ServiceKey
from dipeo.application.registry.keys import (
    API_KEY_SERVICE,
    API_SERVICE,
    ARTIFACT_STORE,
    AST_PARSER,
    BLOB_STORE,
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
