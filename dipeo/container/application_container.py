"""Application layer container - Use cases and orchestration."""

from dependency_injector import providers

from dipeo.container.base import ImmutableBaseContainer


def _create_execution_preparation_use_case(storage_service, validator, api_key_service):
    """Factory for PrepareDiagramForExecutionUseCase.
    
    This use case validates and prepares diagrams before execution,
    ensuring all required resources and configurations are available.
    """
    from dipeo.application.execution.use_cases import PrepareDiagramForExecutionUseCase

    return PrepareDiagramForExecutionUseCase(
        storage_service=storage_service,
        validator=validator,
        api_key_service=api_key_service,
    )


def _create_execute_diagram_use_case(
    state_store,
    message_router,
    diagram_storage_service,
    service_registry,
):
    """Factory for ExecuteDiagramUseCase.
    
    This use case orchestrates the complete diagram execution flow,
    including compilation, state management, and node execution.
    """
    from dipeo.application.execution.use_cases import ExecuteDiagramUseCase

    return ExecuteDiagramUseCase(
        service_registry=service_registry,
        state_store=state_store,
        message_router=message_router,
        diagram_storage_service=diagram_storage_service,
    )


def _create_unified_service_registry(
    # Integration services
    llm_service,
    notion_service,
    api_service,
    integrated_diagram_service,
    typescript_parser,
    # Persistence services
    file_service,
    diagram_loader,
    api_key_service,
    diagram_storage_service,
    db_operations_service,
    state_store,
    message_router,
    # Business logic services
    validation_service,
    condition_evaluator,
    api_business_logic,
    file_business_logic,
    prompt_builder,
    # Static services
    template_processor,
    # Dynamic services
    conversation_manager,
):
    """Factory for UnifiedServiceRegistry.
    
    Creates a registry containing all services required by node handlers
    during diagram execution. This provides a unified interface for
    dependency injection in the execution context.
    """
    from dipeo.application.unified_service_registry import UnifiedServiceRegistry
    
    registry = UnifiedServiceRegistry()
    
    # Integration services
    registry.register("llm_service", llm_service)
    registry.register("notion_service", notion_service)
    registry.register("api_service", api_service)
    registry.register("integrated_diagram_service", integrated_diagram_service)
    registry.register("typescript_parser", typescript_parser)
    
    # Persistence services
    registry.register("file_service", file_service)
    registry.register("diagram_loader", diagram_loader)
    registry.register("api_key_service", api_key_service)
    registry.register("diagram_storage_service", diagram_storage_service)
    registry.register("db_operations_service", db_operations_service)
    registry.register("state_store", state_store)
    registry.register("message_router", message_router)
    
    # Business logic services
    registry.register("validation_service", validation_service)
    registry.register("condition_evaluation_service", condition_evaluator)
    registry.register("api_business_logic", api_business_logic)
    registry.register("file_domain_service", file_business_logic)
    registry.register("prompt_builder", prompt_builder)

    # Static services
    registry.register("template_service", template_processor)
    
    # Dynamic services
    registry.register("conversation_service", conversation_manager)
    registry.register("conversation_manager", conversation_manager)
    
    # Legacy aliases for backward compatibility
    registry.register("file", file_service)  # Used by endpoint.py
    registry.register("template", template_processor)  # Used by code_job.py
    
    return registry


class ApplicationContainer(ImmutableBaseContainer):
    """Application layer container - Use cases and orchestration.
    
    This container provides high-level use cases that orchestrate
    the execution of diagrams using services from all other layers.
    All services are stateless and can be safely shared.
    """
    
    config = providers.Configuration()
    
    # Dependencies from other containers
    static = providers.DependenciesContainer()
    business = providers.DependenciesContainer()
    dynamic = providers.DependenciesContainer()
    persistence = providers.DependenciesContainer()
    integration = providers.DependenciesContainer()
    
    # Service registry for node handlers
    service_registry = providers.Singleton(
        _create_unified_service_registry,
        # Integration services
        llm_service=integration.llm_service,
        notion_service=integration.notion_service,
        api_service=integration.api_service,
        integrated_diagram_service=integration.integrated_diagram_service,
        typescript_parser=integration.typescript_parser,
        # Persistence services
        file_service=persistence.file_service,
        diagram_loader=persistence.diagram_loader,
        api_key_service=persistence.api_key_service,
        diagram_storage_service=persistence.diagram_storage_service,
        db_operations_service=persistence.db_operations_service,
        state_store=persistence.state_store,
        message_router=persistence.message_router,
        # Business logic services
        validation_service=business.validation_service,
        condition_evaluator=business.condition_evaluator,
        api_business_logic=business.api_business_logic,
        file_business_logic=business.file_business_logic,
        prompt_builder=business.prompt_builder,
        # Static services
        template_processor=static.template_processor,
        # Dynamic services
        conversation_manager=dynamic.conversation_manager,
    )
    
    # Use case: Prepare diagram for execution
    execution_preparation_service = providers.Singleton(
        _create_execution_preparation_use_case,
        storage_service=persistence.diagram_storage_service,
        validator=static.diagram_validator,
        api_key_service=persistence.api_key_service,
    )
    
    # Use case: Execute diagram
    execution_service = providers.Singleton(
        _create_execute_diagram_use_case,
        state_store=persistence.state_store,
        message_router=persistence.message_router,
        diagram_storage_service=persistence.diagram_storage_service,
        service_registry=service_registry,
    )