import logging
from pathlib import Path

from dipeo.application.registry.enhanced_service_registry import EnhancedServiceRegistry
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

logger = logging.getLogger(__name__)


class InfrastructureContainer:
    """External integration adapters.

    Contains all I/O operations, external service integrations,
    and infrastructure concerns. Configured based on environment.
    """

    def __init__(self, registry: EnhancedServiceRegistry, config: AppSettings):
        self.registry = registry
        self.config = config
        self._setup_adapters()

    def _setup_adapters(self):
        self._setup_storage_v2()
        self._setup_llm_v2()
        self._setup_infrastructure_services()
        self._setup_repositories()
        self._setup_api_v2()

    def _setup_storage_adapters(self):
        from dipeo.infrastructure.shared.adapters import LocalFileSystemAdapter

        base_dir = Path(self.config.storage.base_dir).resolve()

        filesystem_adapter = LocalFileSystemAdapter(base_path=base_dir)
        self.registry.register(FILESYSTEM_ADAPTER, filesystem_adapter)
        from dipeo.infrastructure.shared.keys.drivers import APIKeyService

        api_key_path = (
            Path(self.config.storage.base_dir) / self.config.storage.data_dir / "apikeys.json"
        )
        self.registry.register(API_KEY_SERVICE, APIKeyService(file_path=api_key_path))

    def _setup_llm_adapter(self):
        from dipeo.infrastructure.llm.drivers.service import LLMInfraService

        api_key_service = self.registry.resolve(API_KEY_SERVICE)
        self.registry.register(LLM_SERVICE, LLMInfraService(api_key_service=api_key_service))

    def _setup_infrastructure_services(self):
        from dipeo.infrastructure.template import SimpleTemplateProcessor

        self.registry.register(TEMPLATE_PROCESSOR, SimpleTemplateProcessor())

        from dipeo.infrastructure.shared.adapters import LocalBlobAdapter

        self.registry.register(
            BLOB_STORE,
            LocalBlobAdapter(base_path=str(Path(self.config.storage.base_dir) / "blobs")),
        )

        from dipeo.domain.integrations.api_services import APIBusinessLogic
        from dipeo.infrastructure.integrations.adapters.api_service import APIService
        from dipeo.infrastructure.integrations.drivers.integrated_api import IntegratedApiService

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

        wire_storage_services(self.registry)

        from dipeo.infrastructure.shared.adapters import LocalFileSystemAdapter

        base_dir = Path(self.config.storage.base_dir).resolve()
        filesystem_adapter = LocalFileSystemAdapter(base_path=base_dir)
        self.registry.register(FILESYSTEM_ADAPTER, filesystem_adapter)

    def _setup_llm_v2(self):
        """Setup LLM services using domain ports."""
        from dipeo.application.bootstrap.wiring import wire_llm_services

        api_key_service = self.registry.resolve(API_KEY_SERVICE)

        wire_llm_services(self.registry, api_key_service)

        from dipeo.application.registry.keys import LLM_SERVICE as LLM_SERVICE_V2

        if self.registry.has(LLM_SERVICE_V2):
            llm_service = self.registry.resolve(LLM_SERVICE_V2)
            self.registry.register(LLM_SERVICE, llm_service)

    def _setup_api_v2(self):
        """Setup API services using domain ports."""
        from dipeo.application.bootstrap.wiring import wire_api_services

        wire_api_services(self.registry)

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

        conversation_repository = InMemoryConversationRepository()
        person_repository = InMemoryPersonRepository()

        self.registry.register(CONVERSATION_REPOSITORY, conversation_repository)
        self.registry.register(PERSON_REPOSITORY, person_repository)
