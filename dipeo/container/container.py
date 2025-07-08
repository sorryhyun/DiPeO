"""Dependency Injection Container for DiPeO applications."""

import os
from pathlib import Path

from dependency_injector import containers, providers
from dipeo.core import (
    SupportsAPIKey,
    SupportsDiagram,
    SupportsExecution,
    SupportsFile,
    SupportsLLM,
    SupportsMemory,
    SupportsNotion,
)

from .adapters.app_context_adapter import AppContextAdapter


def _get_project_base_dir():
    """Get the project base directory."""
    # Try to import from config if available
    try:
        from config import BASE_DIR

        return BASE_DIR
    except ImportError:
        # Fall back to finding the project root
        # This file is in dipeo/container
        # Project root is 2 levels up
        return Path(__file__).resolve().parents[2]


def _create_state_store_for_context():
    """Create appropriate state store based on execution context.
    
    This factory method determines whether we're running in a server
    or CLI context and returns the appropriate state store implementation.
    """
    # Check if we're in a server context by looking for server-specific env vars
    # or by attempting to import server modules
    is_server_context = os.environ.get("DIPEO_CONTEXT") == "server"
    
    if is_server_context:
        try:
            from dipeo_server.infra.persistence import state_store
            return state_store
        except ImportError:
            # Fallback if server modules aren't available
            pass
    
    # Return minimal implementation for CLI/local usage
    from dipeo.application.services.minimal_state_store import MinimalStateStore
    return MinimalStateStore()


def _create_message_router_for_context():
    """Create appropriate message router based on execution context.
    
    This factory method determines whether we're running in a server
    or CLI context and returns the appropriate message router implementation.
    """
    # Check if we're in a server context
    is_server_context = os.environ.get("DIPEO_CONTEXT") == "server"
    
    if is_server_context:
        try:
            from dipeo_server.infra.messaging import message_router
            return message_router
        except ImportError:
            # Fallback if server modules aren't available
            pass
    
    # Return minimal implementation for CLI/local usage
    from dipeo.application.services.minimal_message_router import MinimalMessageRouter
    return MinimalMessageRouter()


def _create_api_key_service():
    from dipeo.domain.services.apikey import APIKeyDomainService

    return APIKeyDomainService()


def _create_file_service(base_dir):
    from dipeo.infra import ConsolidatedFileService

    return ConsolidatedFileService(base_dir=base_dir)


def _create_memory_service():
    from dipeo.infra.persistence.memory import InMemoryConversationStore
    
    return InMemoryConversationStore()


def _create_conversation_service(memory_service):
    from dipeo.domain.services.conversation.simple_service import (
        ConversationMemoryService,
    )

    return ConversationMemoryService(memory_service)


def _create_llm_service(api_key_service):
    from dipeo.infra.adapters.llm import LLMInfraService

    return LLMInfraService(api_key_service)


def _create_notion_service():
    # TODO: NotionAPIService not yet implemented in new structure
    # Return None for now as it's optional
    return None


def _create_diagram_storage_service(base_dir):
    from dipeo.domain.services.diagram import DiagramFileRepository
    return DiagramFileRepository(base_dir=base_dir)


def _create_diagram_storage_adapter(storage_service):
    from dipeo.domain.services.diagram import DiagramStorageAdapter

    return DiagramStorageAdapter(storage_service=storage_service)


def _create_diagram_validator(api_key_service):
    from dipeo.domain.services.execution.validators import DiagramValidator

    return DiagramValidator(api_key_service)


def _create_execution_preparation_service(storage_service, validator, api_key_service):
    from dipeo.domain.services.execution.preparation_service import PrepareDiagramForExecutionUseCase

    return PrepareDiagramForExecutionUseCase(
        storage_service=storage_service,
        validator=validator,
        api_key_service=api_key_service,
    )


def _create_api_domain_service():
    """Create pure API domain service."""
    from dipeo.domain.services.api.api_domain_service import APIDomainService
    return APIDomainService()


def _create_api_service(api_domain_service, file_service):
    """Create infrastructure API service."""
    from dipeo.infra.services.api import APIService
    return APIService(
        domain_service=api_domain_service,
        file_service=file_service
    )


def _create_api_integration_service(api_service):
    """Create legacy API integration service (for backward compatibility).
    
    TODO: Migrate all usages to the new api_service directly.
    """
    # For now, return the new API service for backward compatibility
    return api_service


def _create_text_processing_service():
    from dipeo.domain.services.text import TextProcessingDomainService

    return TextProcessingDomainService()


def _create_file_domain_service():
    """Create pure file domain service."""
    from dipeo.domain.services.file.file_domain_service import FileDomainService
    return FileDomainService()


def _create_file_operations_infra_service(file_domain_service):
    """Create infrastructure file operations service."""
    from dipeo.infra.services.file import FileOperationsService
    return FileOperationsService(domain_service=file_domain_service)


def _create_file_operations_service(file_operations_infra_service):
    """Create legacy file operations service (for backward compatibility).
    
    TODO: Migrate all usages to the new file_operations_infra_service directly.
    """
    # For now, return the new infrastructure service for backward compatibility
    return file_operations_infra_service



def _create_diagram_storage_domain_service(storage_service):
    from dipeo.domain.services.diagram.domain_service import (
        DiagramStorageDomainService,
    )

    return DiagramStorageDomainService(storage_service=storage_service)


def _create_validation_service():
    from dipeo.domain.services.validation import ValidationDomainService

    return ValidationDomainService()


def _create_db_operations_service(file_service, validation_service):
    from dipeo.domain.services.db import DBOperationsDomainService

    return DBOperationsDomainService(file_service, validation_service)


def _create_template_service():
    from dipeo.domain.services.text.template_service import TemplateService
    
    return TemplateService()


def _create_person_job_services(template_service, conversation_memory_service, memory_transformer):
    from dipeo.domain.services.person_job import (
        PromptProcessingService,
        ConversationProcessingService,
        PersonJobOutputBuilder,
        PersonJobExecutionService,
    )
    from dipeo.domain.services.conversation import OnEveryTurnHandler
    
    # Import new focused services
    from dipeo.domain.services.prompt.builder import PromptBuilder
    from dipeo.domain.services.conversation.state_manager import ConversationStateManager
    from dipeo.domain.services.conversation.message_preparator import MessagePreparator
    from dipeo.domain.services.llm.executor import LLMExecutor
    from dipeo.domain.services.person_job.orchestrator import PersonJobOrchestrator
    
    # Create legacy services (for backward compatibility)
    prompt_service = PromptProcessingService(template_service)
    conversation_processor = ConversationProcessingService()
    output_builder = PersonJobOutputBuilder()
    on_every_turn_handler = OnEveryTurnHandler()
    
    # Create new focused services
    prompt_builder = PromptBuilder()
    conversation_state_manager = ConversationStateManager()
    message_preparator = MessagePreparator()
    llm_executor = LLMExecutor()
    
    # Create orchestrator with new services
    person_job_orchestrator = PersonJobOrchestrator(
        prompt_builder=prompt_builder,
        conversation_state_manager=conversation_state_manager,
        message_preparator=message_preparator,
        llm_executor=llm_executor,
        output_builder=output_builder,
        conversation_processor=conversation_processor,
        memory_transformer=memory_transformer,
    )
    
    # Create legacy execution service (for backward compatibility)
    execution_service = PersonJobExecutionService(
        prompt_service=prompt_service,
        conversation_processor=conversation_processor,
        output_builder=output_builder,
        on_every_turn_handler=on_every_turn_handler,
        memory_transformer=memory_transformer,
    )
    
    return {
        "prompt_service": prompt_service,
        "conversation_processor": conversation_processor,
        "output_builder": output_builder,
        "execution_service": execution_service,
        # New focused services
        "prompt_builder": prompt_builder,
        "conversation_state_manager": conversation_state_manager,
        "message_preparator": message_preparator,
        "llm_executor": llm_executor,
        "person_job_orchestrator": person_job_orchestrator,
    }


def _create_condition_evaluation_service(template_service):
    from dipeo.domain.services.condition import ConditionEvaluationService
    
    return ConditionEvaluationService(template_service)


def _create_execution_flow_service():
    from dipeo.domain.services.execution import ExecutionFlowService
    
    return ExecutionFlowService()


def _create_arrow_processor():
    from dipeo.domain.services.arrow import ArrowProcessor
    
    return ArrowProcessor()


def _create_memory_transformer():
    from dipeo.domain.services.arrow import MemoryTransformer
    
    return MemoryTransformer()


def _create_input_resolution_service(arrow_processor):
    from dipeo.domain.services.execution import InputResolutionService
    
    return InputResolutionService(arrow_processor=arrow_processor)


def _create_service_registry(
    llm_service,
    api_key_service,
    file_service,
    conversation_memory_service,
    notion_service,
    diagram_storage_domain_service,
    api_integration_service,
    text_processing_service,
    file_operations_service,
    validation_service,
    db_operations_service,
    person_job_services,
    condition_evaluation_service,
    execution_flow_service,
    input_resolution_service,
    template_service,
    # New infrastructure services
    api_service,
    file_operations_infra_service,
    # Pure domain services
    api_domain_service,
    file_domain_service,
):
    """Factory for UnifiedServiceRegistry with explicit dependencies."""
    from dipeo.application.unified_service_registry import UnifiedServiceRegistry

    # Create registry and register all services dynamically
    registry = UnifiedServiceRegistry()
    
    # Core services - Primary registration with _service suffix
    registry.register("llm_service", llm_service)
    registry.register("api_key_service", api_key_service)
    registry.register("file_service", file_service)
    registry.register("conversation_memory_service", conversation_memory_service)
    registry.register("notion_service", notion_service)
    
    # Domain services - Primary registration with _service suffix
    registry.register("diagram_storage_service", diagram_storage_domain_service)
    registry.register("api_integration_service", api_integration_service)
    registry.register("text_processing_service", text_processing_service)
    registry.register("file_operations_service", file_operations_service)
    registry.register("validation_service", validation_service)
    registry.register("db_operations_service", db_operations_service)
    registry.register("template_service", template_service)
    
    # Person job services - Already follow the pattern
    registry.register("person_job_execution_service", person_job_services["execution_service"])
    registry.register("prompt_processing_service", person_job_services["prompt_service"])
    registry.register("conversation_processor", person_job_services["conversation_processor"])
    registry.register("person_job_output_builder", person_job_services["output_builder"])
    
    # New focused services
    registry.register("prompt_builder", person_job_services["prompt_builder"])
    registry.register("conversation_state_manager", person_job_services["conversation_state_manager"])
    registry.register("message_preparator", person_job_services["message_preparator"])
    registry.register("llm_executor", person_job_services["llm_executor"])
    registry.register("person_job_orchestrator", person_job_services["person_job_orchestrator"])
    
    # Execution services - Primary registration with _service suffix
    registry.register("condition_evaluation_service", condition_evaluation_service)
    registry.register("execution_flow_service", execution_flow_service)
    registry.register("input_resolution_service", input_resolution_service)
    
    # New infrastructure services
    registry.register("api_service", api_service)
    registry.register("file_operations_infra_service", file_operations_infra_service)
    
    # Pure domain services
    registry.register("api_domain_service", api_domain_service)
    registry.register("file_domain_service", file_domain_service)
    
    # Aliases for common service names
    registry.register("conversation_service", conversation_memory_service)  # Primary alias used by handlers
    registry.register("conversation", conversation_memory_service)  # Legacy alias for execution_engine.py
    
    # Legacy aliases for backward compatibility
    registry.register("llm", llm_service)  # Used in execution_engine.py
    registry.register("api_key", api_key_service)
    
    # Aliases for handlers that use short names
    registry.register("file", file_service)  # Used by endpoint.py
    registry.register("template", template_service)  # Used by code_job.py
    
    return registry


def _create_execute_diagram_use_case(
    service_registry, state_store, message_router, diagram_storage_service
):
    """Factory for ExecuteDiagramUseCase with explicit dependencies."""
    from dipeo.application.execution.server_execution_service import ExecuteDiagramUseCase

    return ExecuteDiagramUseCase(
        service_registry=service_registry,
        state_store=state_store,
        message_router=message_router,
        diagram_storage_service=diagram_storage_service,
    )


async def init_resources(container: "Container") -> None:
    """Initialize all resources that require async setup."""
    # Initialize infrastructure
    state_store = container.state_store()
    if hasattr(state_store, 'initialize'):
        await state_store.initialize()
    
    message_router = container.message_router()
    if hasattr(message_router, 'initialize'):
        await message_router.initialize()

    # Initialize services
    await container.llm_service().initialize()
    await container.diagram_storage_service().initialize()
    
    notion_service = container.notion_service()
    if notion_service is not None and hasattr(notion_service, 'initialize'):
        await notion_service.initialize()

    # Initialize execution service
    execution_service = container.execution_service()
    if execution_service is not None:
        await execution_service.initialize()

    # Validate protocol compliance
    _validate_protocol_compliance(container)


async def shutdown_resources(container: "Container") -> None:
    """Cleanup all resources."""
    message_router = container.message_router()
    if hasattr(message_router, 'cleanup'):
        await message_router.cleanup()
    
    state_store = container.state_store()
    if hasattr(state_store, 'cleanup'):
        await state_store.cleanup()


def _validate_protocol_compliance(container: "Container") -> None:
    """Validate that all services implement their required protocols."""
    validations = [
        (container.api_key_service(), SupportsAPIKey, "APIKeyService"),
        (container.llm_service(), SupportsLLM, "LLMInfrastructureService"),
        (container.file_service(), SupportsFile, "FileSystemRepository"),
        (container.conversation_service(), SupportsMemory, "ConversationMemoryService"),
        (container.execution_service(), SupportsExecution, "ExecuteDiagramUseCase"),
        (container.notion_service(), SupportsNotion, "NotionAPIService"),
        (container.diagram_storage_service(), SupportsDiagram, "DiagramFileRepository"),
    ]

    for service, protocol, name in validations:
        if service is not None and not isinstance(service, protocol):
            raise TypeError(
                f"{name} does not implement required protocol {protocol.__name__}"
            )


class Container(containers.DeclarativeContainer):
    """Main dependency injection container for DiPeO."""

    # Self reference for container injection
    __self__ = providers.Self()

    # Configuration
    config = providers.Configuration()

    # Base directory configuration
    base_dir = providers.Factory(
        lambda: Path(os.environ.get("DIPEO_BASE_DIR", _get_project_base_dir()))
    )

    # Infrastructure Services (Singletons)
    state_store = providers.Singleton(_create_state_store_for_context)
    message_router = providers.Singleton(_create_message_router_for_context)

    # Core Domain Services
    api_key_service = providers.Singleton(_create_api_key_service)

    file_service = providers.Singleton(
        _create_file_service,
        base_dir=base_dir,
    )

    memory_service = providers.Singleton(_create_memory_service)

    conversation_service = providers.Singleton(
        _create_conversation_service,
        memory_service=memory_service,
    )

    llm_service = providers.Singleton(
        _create_llm_service,
        api_key_service=api_key_service,
    )

    notion_service = providers.Singleton(_create_notion_service)

    # Diagram Services
    diagram_storage_service = providers.Singleton(
        _create_diagram_storage_service,
        base_dir=base_dir,
    )

    diagram_storage_adapter = providers.Singleton(
        _create_diagram_storage_adapter,
        storage_service=diagram_storage_service,
    )

    # Execution Services
    diagram_validator = providers.Factory(
        _create_diagram_validator,
        api_key_service=api_key_service,
    )

    execution_preparation_service = providers.Singleton(
        _create_execution_preparation_service,
        storage_service=diagram_storage_service,
        validator=diagram_validator,
        api_key_service=api_key_service,
    )

    # Pure Domain Services
    api_domain_service = providers.Singleton(_create_api_domain_service)
    file_domain_service = providers.Singleton(_create_file_domain_service)
    text_processing_service = providers.Singleton(_create_text_processing_service)

    # Infrastructure Services (combining I/O with domain logic)
    api_service = providers.Singleton(
        _create_api_service,
        api_domain_service=api_domain_service,
        file_service=file_service,
    )

    file_operations_infra_service = providers.Singleton(
        _create_file_operations_infra_service,
        file_domain_service=file_domain_service,
    )

    # Legacy services for backward compatibility
    api_integration_service = providers.Singleton(
        _create_api_integration_service,
        api_service=api_service,
    )

    file_operations_service = providers.Singleton(
        _create_file_operations_service,
        file_operations_infra_service=file_operations_infra_service,
    )


    # Additional Domain Services

    diagram_storage_domain_service = providers.Singleton(
        _create_diagram_storage_domain_service,
        storage_service=diagram_storage_service,
    )

    # Validation Services
    validation_service = providers.Singleton(_create_validation_service)
    db_operations_service = providers.Singleton(
        _create_db_operations_service,
        file_service=file_service,
        validation_service=validation_service,
    )

    # Template service
    template_service = providers.Singleton(_create_template_service)
    
    # Arrow processing services (moved before person_job_services)
    arrow_processor = providers.Singleton(_create_arrow_processor)
    memory_transformer = providers.Singleton(_create_memory_transformer)
    
    # Person job services
    person_job_services = providers.Singleton(
        _create_person_job_services,
        template_service=template_service,
        conversation_memory_service=conversation_service,
        memory_transformer=memory_transformer,
    )
    
    # Condition evaluation service
    condition_evaluation_service = providers.Singleton(
        _create_condition_evaluation_service,
        template_service=template_service,
    )
    
    # Execution flow services
    execution_flow_service = providers.Singleton(_create_execution_flow_service)
    input_resolution_service = providers.Singleton(
        _create_input_resolution_service,
        arrow_processor=arrow_processor,
    )

    # Service Registry with explicit dependencies
    service_registry = providers.Singleton(
        _create_service_registry,
        llm_service=llm_service,
        api_key_service=api_key_service,
        file_service=file_service,
        conversation_memory_service=conversation_service,
        notion_service=notion_service,
        diagram_storage_domain_service=diagram_storage_domain_service,
        api_integration_service=api_integration_service,
        text_processing_service=text_processing_service,
        file_operations_service=file_operations_service,
        validation_service=validation_service,
        db_operations_service=db_operations_service,
        person_job_services=person_job_services,
        condition_evaluation_service=condition_evaluation_service,
        execution_flow_service=execution_flow_service,
        input_resolution_service=input_resolution_service,
        template_service=template_service,
        # New services
        api_service=api_service,
        file_operations_infra_service=file_operations_infra_service,
        api_domain_service=api_domain_service,
        file_domain_service=file_domain_service,
    )

    # Application Context for backward compatibility
    app_context = providers.Singleton(
        AppContextAdapter,
        container=__self__,
    )

    # Execute Diagram Use Case with explicit dependencies
    execution_service = providers.Singleton(
        _create_execute_diagram_use_case,
        service_registry=service_registry,
        state_store=state_store,
        message_router=message_router,
        diagram_storage_service=diagram_storage_service,
    )
