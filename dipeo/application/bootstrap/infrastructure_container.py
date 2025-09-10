from pathlib import Path

from dipeo.application.registry import ServiceRegistry
from dipeo.application.registry.keys import (
    API_KEY_SERVICE,
    AST_PARSER,
    BLOB_STORE,
    CONVERSATION_REPOSITORY,
    FILESYSTEM_ADAPTER,
    INTEGRATED_API_SERVICE,
    LLM_SERVICE,
    MESSAGE_ROUTER,
    PERSON_REPOSITORY,
    STATE_STORE,
    TEMPLATE_PROCESSOR,
)
from dipeo.config import AppSettings


class InfrastructureContainer:
    """External integration adapters.

    Contains all I/O operations, external service integrations,
    and infrastructure concerns. Configured based on environment.
    """

    def __init__(self, registry: ServiceRegistry, config: AppSettings):
        self.registry = registry
        self.config = config
        self._setup_adapters()

    def _setup_adapters(self):
        # Setup storage
        self._setup_storage_v2()

        # Setup LLM
        self._setup_llm_v2()

        # Setup API and other infrastructure services
        self._setup_infrastructure_services()

        # Setup repositories
        self._setup_repositories()

        # Setup API
        self._setup_api_v2()

    def _setup_storage_adapters(self):
        from dipeo.infrastructure.shared.adapters import LocalFileSystemAdapter

        # Use absolute path from config
        base_dir = Path(self.config.storage.base_dir).resolve()

        filesystem_adapter = LocalFileSystemAdapter(base_path=base_dir)
        self.registry.register(FILESYSTEM_ADAPTER, filesystem_adapter)
        from dipeo.infrastructure.shared.keys.drivers import APIKeyService

        api_key_path = (
            Path(self.config.storage.base_dir) / self.config.storage.data_dir / "apikeys.json"
        )
        self.registry.register(API_KEY_SERVICE, APIKeyService(file_path=api_key_path))

    def _setup_llm_adapter(self):
        import os

        api_key_service = self.registry.resolve(API_KEY_SERVICE)

        # Check if simplified LLM service is enabled
        use_simplified = os.getenv("DIPEO_USE_SIMPLIFIED_LLM", "true").lower() == "true"

        if use_simplified:
            from dipeo.infrastructure.llm.simplified_service import SimplifiedLLMService

            self.registry.register(
                LLM_SERVICE, SimplifiedLLMService(api_key_service=api_key_service)
            )
        else:
            from dipeo.infrastructure.llm.drivers.service import LLMInfraService

            self.registry.register(LLM_SERVICE, LLMInfraService(api_key_service=api_key_service))

    def _setup_infrastructure_services(self):
        # Register SimpleTemplateProcessor for path interpolation in DB nodes
        from dipeo.domain.diagram.template import SimpleTemplateProcessor

        self.registry.register(TEMPLATE_PROCESSOR, SimpleTemplateProcessor())

        self.registry.register(STATE_STORE, None)

        self.registry.register(MESSAGE_ROUTER, None)

        from dipeo.infrastructure.shared.adapters import LocalBlobAdapter

        self.registry.register(
            BLOB_STORE,
            LocalBlobAdapter(base_path=str(Path(self.config.storage.base_dir) / "blobs")),
        )

        from dipeo.domain.integrations.api_services import APIBusinessLogic
        from dipeo.infrastructure.integrations.adapters.api_service import APIService
        from dipeo.infrastructure.integrations.drivers.integrated_api import IntegratedApiService

        # Get the template processor for API business logic
        template_processor = self.registry.resolve(TEMPLATE_PROCESSOR)
        api_business_logic = APIBusinessLogic(template_processor=template_processor)
        api_service = APIService(api_business_logic)
        integrated_api_service = IntegratedApiService(api_service=api_service)
        self.registry.register(INTEGRATED_API_SERVICE, integrated_api_service)

        from dipeo.infrastructure.codegen.parsers.parser_service import get_parser_service

        parser_service = get_parser_service(
            project_root=Path(self.config.storage.base_dir), cache_enabled=True
        )
        self.registry.register(AST_PARSER, parser_service)

    def _setup_storage_v2(self):
        """Setup storage services using domain ports."""
        from dipeo.application.bootstrap.wiring import wire_storage_services

        # First setup API key service (needed by other services)
        from dipeo.infrastructure.shared.keys.drivers import APIKeyService

        api_key_path = (
            Path(self.config.storage.base_dir) / self.config.storage.data_dir / "apikeys.json"
        )
        self.registry.register(API_KEY_SERVICE, APIKeyService(file_path=api_key_path))

        # Wire V2 storage services
        wire_storage_services(self.registry)

        # Override the filesystem adapter with the correct base path from config
        from dipeo.infrastructure.shared.adapters import LocalFileSystemAdapter

        base_dir = Path(self.config.storage.base_dir).resolve()
        filesystem_adapter = LocalFileSystemAdapter(base_path=base_dir)
        self.registry.register(FILESYSTEM_ADAPTER, filesystem_adapter)

    def _setup_llm_v2(self):
        """Setup LLM services using domain ports."""
        from dipeo.application.bootstrap.wiring import wire_llm_services

        # Ensure API key service exists
        if not self.registry.has(API_KEY_SERVICE):
            from dipeo.infrastructure.shared.keys.drivers import APIKeyService

            api_key_path = (
                Path(self.config.storage.base_dir) / self.config.storage.data_dir / "apikeys.json"
            )
            self.registry.register(API_KEY_SERVICE, APIKeyService(file_path=api_key_path))

        api_key_service = self.registry.resolve(API_KEY_SERVICE)

        # Wire V2 LLM services
        wire_llm_services(self.registry, api_key_service)

        # Also register as old LLM_SERVICE key for backward compatibility
        from dipeo.application.registry.keys import LLM_SERVICE as LLM_SERVICE_V2

        if self.registry.has(LLM_SERVICE_V2):
            llm_service = self.registry.resolve(LLM_SERVICE_V2)
            self.registry.register(LLM_SERVICE, llm_service)

    def _setup_api_v2(self):
        """Setup API services using domain ports."""
        from dipeo.application.bootstrap.wiring import wire_api_services

        # Wire V2 API services
        wire_api_services(self.registry)

        # Override the old INTEGRATED_API_SERVICE with V2 version for backward compatibility
        from dipeo.application.registry.keys import API_INVOKER

        if self.registry.has(API_INVOKER):
            api_invoker = self.registry.resolve(API_INVOKER)
            self.registry.register(INTEGRATED_API_SERVICE, api_invoker)

    def _setup_repositories(self):
        """Setup repository implementations (now in infrastructure layer)."""
        from dipeo.infrastructure.repositories.conversation import (
            InMemoryConversationRepository,
            InMemoryPersonRepository,
        )

        # Create and register repository instances
        conversation_repository = InMemoryConversationRepository()
        person_repository = InMemoryPersonRepository()

        # Register repositories for application layer to use
        self.registry.register(CONVERSATION_REPOSITORY, conversation_repository)
        self.registry.register(PERSON_REPOSITORY, person_repository)
