from pathlib import Path
from typing import Any
import os

from dipeo.application.registry import ServiceRegistry
from dipeo.application.registry.keys import (
    API_KEY_SERVICE,
    API_KEY_STORAGE,
    API_SERVICE,
    ARTIFACT_STORE,
    AST_PARSER,
    BLOB_STORE,
    CONVERSATION_REPOSITORY,
    DIAGRAM_VALIDATOR,
    DOMAIN_SERVICE_REGISTRY,
    EXECUTION_SERVICE,
    FILESYSTEM_ADAPTER,
    INTEGRATED_API_SERVICE,
    LLM_SERVICE,
    MESSAGE_ROUTER,
    NODE_REGISTRY,
    PERSON_MANAGER,
    PERSON_REPOSITORY,
    PROMPT_BUILDER,
    STATE_STORE,
    TEMPLATE_PROCESSOR,
)
from dipeo.domain.config import Config


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

        filesystem_adapter = LocalFileSystemAdapter(base_path=Path(self.config.base_dir))
        self.registry.register(FILESYSTEM_ADAPTER, filesystem_adapter)
        from dipeo.application.integrations.use_cases import APIKeyService
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
        # Register template processor service
        from dipeo.infrastructure.services.template.simple_processor import SimpleTemplateProcessor
        self.registry.register(
            TEMPLATE_PROCESSOR,
            SimpleTemplateProcessor()
        )
        
        self.registry.register(
            STATE_STORE,
            None
        )

        self.registry.register(
            MESSAGE_ROUTER,
            None
        )

        from dipeo.infrastructure.shared.adapters import LocalBlobAdapter
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
        from dipeo.infrastructure.integrations.adapters.api_service import APIService
        from dipeo.domain.integrations.api_services import APIBusinessLogic
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
    
    def _setup_storage_v2(self):
        """Setup storage services using domain ports."""
        from dipeo.application.bootstrap.wiring import wire_storage_services
        
        # First setup API key service (needed by other services)
        from dipeo.application.integrations.use_cases import APIKeyService
        api_key_path = Path(self.config.base_dir) / "files" / "apikeys.json"
        self.registry.register(
            API_KEY_SERVICE,
            APIKeyService(file_path=api_key_path)
        )
        
        # Wire V2 storage services
        wire_storage_services(self.registry)
        
        # Also keep filesystem adapter for backward compatibility
        from dipeo.infrastructure.shared.adapters import LocalFileSystemAdapter
        filesystem_adapter = LocalFileSystemAdapter(base_path=Path(self.config.base_dir))
        self.registry.register(FILESYSTEM_ADAPTER, filesystem_adapter)
    
    def _setup_llm_v2(self):
        """Setup LLM services using domain ports."""
        from dipeo.application.bootstrap.wiring import wire_llm_services
        
        # Ensure API key service exists
        if not self.registry.has(API_KEY_SERVICE):
            from dipeo.application.integrations.use_cases import APIKeyService
            api_key_path = Path(self.config.base_dir) / "files" / "apikeys.json"
            self.registry.register(
                API_KEY_SERVICE,
                APIKeyService(file_path=api_key_path)
            )
        
        api_key_service = self.registry.resolve(API_KEY_SERVICE)
        
        # Wire V2 LLM services
        wire_llm_services(self.registry, api_key_service)
        
        # Also register as old LLM_SERVICE key for backward compatibility
        from dipeo.application.registry.registry_tokens import LLM_SERVICE as LLM_SERVICE_V2
        if self.registry.has(LLM_SERVICE_V2):
            llm_service = self.registry.resolve(LLM_SERVICE_V2)
            self.registry.register(LLM_SERVICE, llm_service)
    
    def _setup_api_v2(self):
        """Setup API services using domain ports."""
        from dipeo.application.bootstrap.wiring import wire_api_services
        
        # Wire V2 API services
        wire_api_services(self.registry)
        
        # Override the old INTEGRATED_API_SERVICE with V2 version for backward compatibility
        from dipeo.application.registry.registry_tokens import API_INVOKER
        if self.registry.has(API_INVOKER):
            api_invoker = self.registry.resolve(API_INVOKER)
            self.registry.register(INTEGRATED_API_SERVICE, api_invoker)
    
    def _setup_repositories(self):
        """Setup repository implementations (now in infrastructure layer)."""
        from dipeo.infrastructure.repositories.conversation import (
            InMemoryConversationRepository,
            InMemoryPersonRepository
        )
        
        # Create and register repository instances
        conversation_repository = InMemoryConversationRepository()
        person_repository = InMemoryPersonRepository()
        
        # Register repositories for application layer to use
        self.registry.register(CONVERSATION_REPOSITORY, conversation_repository)
        self.registry.register(PERSON_REPOSITORY, person_repository)
