from dipeo.application.registry import ServiceRegistry
from dipeo.application.registry.keys import (
    API_KEY_SERVICE,
    API_KEY_STORAGE,
    DIAGRAM_VALIDATOR,
    DOMAIN_SERVICE_REGISTRY,
    EXECUTION_SERVICE,
    FILESYSTEM_ADAPTER,
    LLM_SERVICE,
    MESSAGE_ROUTER,
    NODE_REGISTRY,
    PERSON_MANAGER,
    PROMPT_BUILDER,
    STATE_STORE,
    TEMPLATE_PROCESSOR,
)
from dipeo.core.bak.config import Config


class CoreContainer:
    """Immutable core services with no external dependencies.

    Contains pure domain logic, validators, and business rules.
    These services can be safely shared across all execution contexts.
    """

    def __init__(self, registry: ServiceRegistry):
        self.registry = registry
        self._setup_domain_services()

    def _setup_domain_services(self):
        from dipeo.domain.validators import DiagramValidator
        self.registry.register(
            DIAGRAM_VALIDATOR,
            lambda: DiagramValidator(
                api_key_service=self.registry.resolve(API_KEY_SERVICE)
            )
        )

        from dipeo.infrastructure.services.template.simple_processor import SimpleTemplateProcessor
        self.registry.register(
            TEMPLATE_PROCESSOR,
            SimpleTemplateProcessor()
        )

        from dipeo.application.utils import PromptBuilder
        template_processor = SimpleTemplateProcessor()
        self.registry.register(
            PROMPT_BUILDER,
            PromptBuilder(template_processor=template_processor)
        )

        from dipeo.application import get_global_registry
        self.registry.register(
            NODE_REGISTRY,
            get_global_registry()
        )