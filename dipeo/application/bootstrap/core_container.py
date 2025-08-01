from dipeo.application.registry import ServiceRegistry, ServiceKey
from dipeo.application.registry.keys import (
    API_KEY_SERVICE,
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