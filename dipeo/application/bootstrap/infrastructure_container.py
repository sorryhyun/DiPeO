from pathlib import Path
from typing import Any

from dipeo.application.registry import ServiceRegistry, ServiceKey
from dipeo.application.registry.keys import (
    API_KEY_SERVICE,
    API_SERVICE,
    ARTIFACT_STORE,
    AST_PARSER,
    BLOB_STORE,
    DIAGRAM_VALIDATOR,
    EXECUTION_SERVICE,
    INTEGRATED_API_SERVICE,
    LLM_SERVICE,
    MESSAGE_ROUTER,
    PERSON_MANAGER,
    PROMPT_BUILDER,
    STATE_STORE,
)

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
        self._setup_storage_adapters()
        self._setup_llm_adapter()
        self._setup_infrastructure_services()

    def _setup_storage_adapters(self):
        from dipeo.infrastructure.adapters.storage import LocalFileSystemAdapter

        filesystem_adapter = LocalFileSystemAdapter(base_path=Path(self.config.base_dir))
        self.registry.register(FILESYSTEM_ADAPTER, filesystem_adapter)
        from dipeo.application.services.apikey_service import APIKeyService
        api_key_path = Path(self.config.base_dir) / "files" / "apikeys.json"
        self.registry.register(
            API_KEY_SERVICE,
            APIKeyService(file_path=api_key_path)
        )

        self.registry.register(
            ARTIFACT_STORE,
            None
        )

    def _setup_llm_adapter(self):
        from dipeo.infrastructure.services.llm.service import LLMInfraService
        from dipeo.domain.llm import LLMDomainService

        api_key_service = self.registry.resolve(API_KEY_SERVICE)
        llm_domain_service = LLMDomainService()
        self.registry.register(
            LLM_SERVICE,
            LLMInfraService(
                api_key_service=api_key_service,
                llm_domain_service=llm_domain_service
            )
        )

    def _setup_infrastructure_services(self):
        self.registry.register(
            STATE_STORE,
            None
        )

        self.registry.register(
            MESSAGE_ROUTER,
            None
        )

        from dipeo.infrastructure.adapters.storage import LocalBlobAdapter
        self.registry.register(
            BLOB_STORE,
            LocalBlobAdapter(
                base_path=str(Path(self.config.base_dir) / "blobs")
            )
        )

        self.registry.register(
            API_SERVICE,
            None
        )

        from dipeo.infrastructure.services.integrated_api import IntegratedApiService
        from dipeo.infrastructure.adapters.http.api_service import APIService
        from dipeo.domain.api.services import APIBusinessLogic
        from dipeo.infrastructure.services.template.simple_processor import SimpleTemplateProcessor
        
        template_processor = SimpleTemplateProcessor()
        api_business_logic = APIBusinessLogic(template_processor=template_processor)
        api_service = APIService(api_business_logic)
        integrated_api_service = IntegratedApiService(api_service=api_service)
        self.registry.register(
            INTEGRATED_API_SERVICE,
            integrated_api_service
        )

        from dipeo.infrastructure.services.parser import get_parser_service
        parser_service = get_parser_service(
            default_language="typescript",
            project_root=Path(self.config.base_dir),
            cache_enabled=True
        )
        self.registry.register(
            AST_PARSER,
            parser_service
        )
