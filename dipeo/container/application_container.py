"""Application layer container - Use cases and orchestration."""

from dependency_injector import containers, providers

from dipeo.application.unified_service_registry import UnifiedServiceRegistry


def _create_execution_preparation_service(storage_service, validator, api_key_service):
    from dipeo.application.execution.use_cases import PrepareDiagramForExecutionUseCase

    return PrepareDiagramForExecutionUseCase(
        storage_service=storage_service,
        validator=validator,
        api_key_service=api_key_service,
    )


def _create_service_registry(
    llm_service,
    api_key_service,
    file_service,
    conversation_service,
    notion_service,
    diagram_storage_domain_service,
    text_processing_service,
    validation_service,
    db_operations_service,
    person_job_services,
    condition_evaluation_service,
    template_service,
    # New infrastructure services
    api_service,
    diagram_loader,
    # Pure business logic utilities
    api_business_logic,
    file_domain_service,
    # Additional services for PersonJobNodeHandler
    conversation_manager,
    memory_transformer,
):
    """Factory for UnifiedServiceRegistry with explicit dependencies."""
    # Create registry and register all services dynamically
    registry = UnifiedServiceRegistry()
    
    # Core services - Primary registration with _service suffix
    registry.register("llm_service", llm_service)
    registry.register("api_key_service", api_key_service)
    registry.register("file_service", file_service)
    registry.register("conversation_service", conversation_service)
    registry.register("notion_service", notion_service)
    
    # Domain services - Primary registration with _service suffix
    registry.register("diagram_storage_domain_service", diagram_storage_domain_service)
    registry.register("text_processing_service", text_processing_service)
    registry.register("validation_service", validation_service)
    registry.register("db_operations_service", db_operations_service)
    registry.register("template_service", template_service)
    
    # Person job services - Register orchestrator as the main service
    
    # New focused services
    registry.register("prompt_builder", person_job_services["prompt_builder"])
    registry.register("conversation_state_manager", person_job_services["conversation_state_manager"])
    
    # Handle Factory providers by calling them to get instances
    
    # person_job_orchestrator removed - using direct services instead
    # person_job_orchestrator_provider = person_job_services["person_job_orchestrator"]
    # if isinstance(person_job_orchestrator_provider, providers.Factory) or isinstance(person_job_orchestrator_provider, providers.Singleton):
    #     registry.register("person_job_orchestrator", person_job_orchestrator_provider())
    # else:
    #     registry.register("person_job_orchestrator", person_job_orchestrator_provider)
    
    # Execution services - Primary registration with _service suffix
    registry.register("condition_evaluation_service", condition_evaluation_service)
    # input_resolution_service removed - using typed version directly
    
    # New infrastructure services
    registry.register("api_service", api_service)
    registry.register("diagram_loader", diagram_loader)
    
    # Pure business logic utilities
    registry.register("api_business_logic", api_business_logic)
    registry.register("file_domain_service", file_domain_service)
    
    # Additional services for PersonJobNodeHandler
    registry.register("conversation_manager", conversation_manager)
    registry.register("memory_transformer", memory_transformer)

    
    # Aliases for handlers that use short names
    registry.register("file", file_service)  # Used by endpoint.py
    registry.register("template", template_service)  # Used by code_job.py
    
    return registry


def _create_execute_diagram_use_case(
    service_registry, state_store, message_router, diagram_storage_service
):
    """Factory for ExecuteDiagramUseCase with explicit dependencies."""
    from dipeo.application.execution.use_cases import ExecuteDiagramUseCase

    return ExecuteDiagramUseCase(
        service_registry=service_registry,
        state_store=state_store,
        message_router=message_router,
        diagram_storage_service=diagram_storage_service,
    )


class ApplicationContainer(containers.DeclarativeContainer):
    """Application layer container - Use cases and orchestration."""
    
    config = providers.Configuration()
    # New container dependencies
    static = providers.DependenciesContainer()
    business = providers.DependenciesContainer()
    dynamic = providers.DependenciesContainer()
    persistence = providers.DependenciesContainer()
    integration = providers.DependenciesContainer()
    
    # Execution preparation
    execution_preparation_service = providers.Singleton(
        _create_execution_preparation_service,
        storage_service=persistence.diagram_storage_service,
        validator=static.diagram_validator,
        api_key_service=persistence.api_key_service,
    )
    
    # Service Registry with explicit dependencies from all layers
    service_registry = providers.Singleton(
        _create_service_registry,
        # From Integration Container (was infra)
        llm_service=integration.llm_service,
        notion_service=integration.notion_service,
        api_service=integration.api_service,
        
        # From Persistence Container (was infra/domain)
        file_service=persistence.file_service,
        diagram_loader=persistence.diagram_loader,
        api_key_service=persistence.api_key_service,
        diagram_storage_domain_service=persistence.diagram_storage_domain_service,
        db_operations_service=persistence.db_operations_service,
        
        # From Business Container (was domain)
        text_processing_service=business.text_processing_service,
        validation_service=business.validation_service,
        condition_evaluation_service=business.condition_evaluator,  # Note: renamed
        api_business_logic=business.api_business_logic,
        file_domain_service=business.file_business_logic,
        
        # From Static Container (was domain)
        template_service=static.template_processor,  # Note: renamed
        
        # From Dynamic Container (was domain) - person job services unpacked
        conversation_service=dynamic.conversation_manager,
        person_job_services={
            "prompt_builder": business.prompt_builder,
            "conversation_state_manager": business.conversation_state_manager,
            # "person_job_orchestrator": dynamic.person_job_orchestrator,  # Removed - using direct services
        },
        # Additional services for PersonJobNodeHandler
        conversation_manager=dynamic.conversation_manager,
        memory_transformer=static.memory_transformer,
    )
    
    # Execute Diagram Use Case
    execution_service = providers.Singleton(
        _create_execute_diagram_use_case,
        service_registry=service_registry,
        state_store=persistence.state_store,
        message_router=persistence.message_router,
        diagram_storage_service=persistence.diagram_storage_service,
    )