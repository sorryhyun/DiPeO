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


def _create_unified_service_registry_from_dependencies(static, business, dynamic, persistence, integration):
    """Factory for UnifiedServiceRegistry using automatic service discovery."""
    from dipeo.application.unified_service_registry import UnifiedServiceRegistry
    import logging
    
    logger = logging.getLogger(__name__)
    registry = UnifiedServiceRegistry()
    
    # Define container mappings with their service configurations
    container_configs = {
        "persistence": {
            "container": persistence,
            "services": [
                "state_store",
                "message_router",
                "file_service",
                "api_key_service",
                "diagram_storage_service",
                "diagram_storage_adapter",
                "diagram_loader",
                "db_operations_service",
            ],
            "aliases": {
                "file": "file_service",  # Legacy alias
            }
        },
        "integration": {
            "container": integration,
            "services": [
                "llm_service",
                "api_service",
                "notion_service",
                "integrated_diagram_service",
            ],
            "optional_services": [
                "api_integration_service",
                "code_execution_service",
            ]
        },
        "business": {
            "container": business,
            "services": [
                "condition_evaluator",
                "api_business_logic",
                "file_business_logic",
                "diagram_business_logic",
                "db_validator",
                "validation_service",
                "prompt_builder",
            ],
            "aliases": {
                "condition_evaluation_service": "condition_evaluator",
                "file_domain_service": "file_business_logic",
            }
        },
        "static": {
            "container": static,
            "services": [
                "diagram_validator",
                "diagram_compiler",
                "template_processor",
            ],
            "aliases": {
                "template_service": "template_processor",
                "template": "template_processor",  # Legacy alias
            }
        },
        "dynamic": {
            "container": dynamic,
            "services": [
                "conversation_manager",
            ],
            "optional_services": [
                "execution_flow_service",
            ],
            "aliases": {
                "conversation_service": "conversation_manager",
            }
        }
    }
    
    # Register services from each container
    for container_name, config in container_configs.items():
        container = config["container"]
        if not container:
            continue
            
        try:
            # Register required services
            for service_name in config.get("services", []):
                if hasattr(container, service_name):
                    service = getattr(container, service_name)()
                    registry.register(service_name, service)
            
            # Register optional services
            for service_name in config.get("optional_services", []):
                if hasattr(container, service_name):
                    service = getattr(container, service_name)()
                    registry.register(service_name, service)
            
            # Register aliases
            for alias, target in config.get("aliases", {}).items():
                if hasattr(container, target):
                    service = getattr(container, target)()
                    registry.register(alias, service)

        except Exception as e:
            logger.error(f"Failed to register {container_name} services: {e}")
    
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
    
    # Service registry for node handlers - manually registering from dependencies
    service_registry = providers.Singleton(
        _create_unified_service_registry_from_dependencies,
        static=static,
        business=business,
        dynamic=dynamic,
        persistence=persistence,
        integration=integration,
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