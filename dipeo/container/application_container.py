"""Application layer container - Use cases and orchestration."""

from dependency_injector import containers, providers
from dipeo.application.unified_service_registry import UnifiedServiceRegistry


def _create_execution_preparation_service(storage_service, validator, api_key_service):
    from dipeo.application.execution.preparation import PrepareDiagramForExecutionUseCase

    return PrepareDiagramForExecutionUseCase(
        storage_service=storage_service,
        validator=validator,
        api_key_service=api_key_service,
    )


def _create_service_registry(
    llm_service,
    api_key_service,
    file_service,
    conversation_memory_service,
    notion_service,
    diagram_storage_domain_service,
    text_processing_service,
    validation_service,
    db_operations_service,
    person_job_services,
    condition_evaluation_service,
    flow_control_service,
    input_resolution_service,
    template_service,
    # New infrastructure services
    api_service,
    file_operations_infra_service,
    diagram_loader,
    # Pure business logic utilities
    api_business_logic,
    file_domain_service,
):
    """Factory for UnifiedServiceRegistry with explicit dependencies."""
    # Create registry and register all services dynamically
    registry = UnifiedServiceRegistry()
    
    # Core services - Primary registration with _service suffix
    registry.register("llm_service", llm_service)
    registry.register("api_key_service", api_key_service)
    registry.register("file_service", file_service)
    registry.register("conversation_memory_service", conversation_memory_service)
    registry.register("conversation_service", conversation_memory_service)  # Alias for handlers
    registry.register("notion_service", notion_service)
    
    # Domain services - Primary registration with _service suffix
    registry.register("diagram_storage_domain_service", diagram_storage_domain_service)
    registry.register("text_processing_service", text_processing_service)
    registry.register("validation_service", validation_service)
    registry.register("db_operations_service", db_operations_service)
    registry.register("template_service", template_service)
    
    # Person job services - Register orchestrator as the main service
    registry.register("conversation_processor", person_job_services["conversation_processor"])
    registry.register("output_builder", person_job_services["output_builder"])
    
    # New focused services
    registry.register("prompt_builder", person_job_services["prompt_builder"])
    registry.register("conversation_state_manager", person_job_services["conversation_state_manager"])
    registry.register("llm_executor", person_job_services["llm_executor"])
    registry.register("person_job_orchestrator", person_job_services["person_job_orchestrator"])
    
    # Execution services - Primary registration with _service suffix
    registry.register("condition_evaluation_service", condition_evaluation_service)
    registry.register("flow_control_service", flow_control_service)  # New unified service
    registry.register("input_resolution_service", input_resolution_service)
    
    # New infrastructure services
    registry.register("api_service", api_service)
    registry.register("file_operations_infra_service", file_operations_infra_service)
    registry.register("diagram_loader", diagram_loader)
    
    # Pure business logic utilities
    registry.register("api_business_logic", api_business_logic)
    registry.register("file_domain_service", file_domain_service)

    
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
    infra = providers.DependenciesContainer()
    domain = providers.DependenciesContainer()
    
    # Execution preparation
    execution_preparation_service = providers.Singleton(
        _create_execution_preparation_service,
        storage_service=domain.diagram_storage_service,
        validator=domain.diagram_validator,
        api_key_service=domain.api_key_service,
    )
    
    # Service Registry with explicit dependencies from all layers
    service_registry = providers.Singleton(
        _create_service_registry,
        # Infrastructure services
        llm_service=infra.llm_service,
        file_service=infra.file_service,
        notion_service=infra.notion_service,
        api_service=infra.api_service,
        file_operations_infra_service=infra.file_operations_service,
        diagram_loader=infra.diagram_loader,
        # Domain services
        api_key_service=domain.api_key_service,
        conversation_memory_service=domain.conversation_service,
        diagram_storage_domain_service=domain.diagram_storage_domain_service,
        text_processing_service=domain.text_processing_service,
        validation_service=domain.validation_service,
        db_operations_service=domain.db_operations_service,
        person_job_services=domain.person_job_services,
        condition_evaluation_service=domain.condition_evaluation_service,
        flow_control_service=domain.flow_control_service,
        input_resolution_service=domain.input_resolution_service,
        template_service=domain.template_service,
        api_business_logic=domain.api_business_logic,
        file_domain_service=domain.file_business_logic,
    )
    
    # Execute Diagram Use Case
    execution_service = providers.Singleton(
        _create_execute_diagram_use_case,
        service_registry=service_registry,
        state_store=infra.state_store,
        message_router=infra.message_router,
        diagram_storage_service=domain.diagram_storage_service,
    )