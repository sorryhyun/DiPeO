"""Examples of migrating from string-based to ServiceKey-based lookups.

This file demonstrates how to update service lookups to use the new
type-safe ServiceKey pattern during the migration.
"""

# OLD WAY (string-based, no type safety):
def old_way_example(registry):
    # No type hints, prone to typos
    llm_service = registry.get("llm_service")
    state_store = registry.get("state_store")
    
    # Could return None, no compile-time checking
    if llm_service:
        result = llm_service.complete("prompt")


# NEW WAY (ServiceKey-based, type-safe):
from dipeo.application.registry import (
    ServiceKey,
    LLM_SERVICE,
    STATE_STORE,
    FILE_SERVICE,
    CONVERSATION_MANAGER,
)

def new_way_example(registry):
    # Type-safe retrieval with IDE support
    llm_service = registry.resolve(LLM_SERVICE)  # Type: LLMServicePort
    state_store = registry.resolve(STATE_STORE)  # Type: StateStorePort
    
    # Compile-time type checking
    result = llm_service.complete("prompt")  # IDE knows the methods


# MIGRATION PATTERN for handlers:
from dipeo.application.execution.handler_base import TypedNodeHandlerBase
from dipeo.models import ExecutableNode

class ExampleHandler(TypedNodeHandlerBase[ExecutableNode]):
    """Example of migrating a handler to use ServiceKeys."""
    
    def execute_request(self, request):
        # OLD WAY:
        # llm = request.services.get("llm_service")
        # file_service = request.services.get("file_service")
        
        # NEW WAY:
        llm = request.services.resolve(LLM_SERVICE)
        file_service = request.services.resolve(FILE_SERVICE)
        
        # Optional services with defaults
        conversation = request.services.get(CONVERSATION_MANAGER, None)
        
        # Use services with full type safety
        response = llm.complete(request.node.prompt)
        file_content = file_service.read_file("path/to/file")
        
        return self.build_output(response)


# MIGRATION PATTERN for GraphQL resolvers:
def migrate_graphql_resolver(info):
    registry = info.context.service_registry
    
    # OLD WAY:
    # api_key_service = registry.get("api_key_service")
    # diagram_service = registry.get("diagram_storage_service")
    
    # NEW WAY:
    from dipeo.application.registry import API_KEY_SERVICE, DIAGRAM_STORAGE_SERVICE
    
    api_key_service = registry.resolve(API_KEY_SERVICE)
    diagram_service = registry.resolve(DIAGRAM_STORAGE_SERVICE)
    
    # Use with confidence - types are known
    keys = api_key_service.list_keys()
    diagram = diagram_service.load_diagram("diagram_id")


# GRADUAL MIGRATION using MigrationServiceRegistry:
def gradual_migration_example(registry):
    """The MigrationServiceRegistry supports both old and new patterns."""
    
    # Both work during migration:
    llm_old = registry.get("llm_service")  # Old string-based
    llm_new = registry.resolve(LLM_SERVICE)  # New ServiceKey-based
    
    # They return the same instance
    assert llm_old is llm_new
    
    # Prefer new pattern for all new code
    file_service = registry.resolve(FILE_SERVICE)


# DEFINING NEW SERVICE KEYS:
# If you need a service key that doesn't exist yet:
from dipeo.application.registry import ServiceKey

# Define the key with proper typing
MY_CUSTOM_SERVICE = ServiceKey["MyCustomServiceType"]("my_custom_service")

# Register it
def register_custom_service(registry, service_instance):
    registry.register(MY_CUSTOM_SERVICE, service_instance)

# Use it
def use_custom_service(registry):
    service = registry.resolve(MY_CUSTOM_SERVICE)  # Type: MyCustomServiceType
    service.do_something()  # IDE knows the methods