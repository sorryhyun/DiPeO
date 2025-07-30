"""Utility functions for container management."""

import asyncio
import logging

from dipeo.core.dynamic.conversation_manager import ConversationManager
from dipeo.core.ports import LLMServicePort, NotionServicePort, SupportsAPIKey
from dipeo.core.ports.diagram_port import DiagramPort
from dipeo.domain.ports.storage import FileSystemPort

from .profiling import get_profiler

logger = logging.getLogger(__name__)


async def init_resources(container) -> None:
    """Initialize all resources that require async setup."""
    profiler = get_profiler()
    # Get profile from the Container class
    from .container import Container as ContainerClass
    profile = ContainerClass.get_profile() if hasattr(ContainerClass, 'get_profile') else None
    # Profile is now available for conditional initialization
    
    # Check if this is a sub-container
    is_sub_container = container.config.get('is_sub_container', False)
    
    # Initialize infrastructure
    # Initialize state store first (from persistence container)
    if not profile or profile.include_state_management:
        if profiler:
            async with profiler.profile_async("persistence.state_store"):
                state_store = container.persistence.state_store()
                if hasattr(state_store, 'initialize'):
                    await state_store.initialize()
        else:
            state_store = container.persistence.state_store()
            if hasattr(state_store, 'initialize'):
                await state_store.initialize()
        
        # Initialize message router
        if profiler:
            async with profiler.profile_async("persistence.message_router"):
                message_router = container.persistence.message_router()
                if hasattr(message_router, 'initialize'):
                    await message_router.initialize()
        else:
            message_router = container.persistence.message_router()
            if hasattr(message_router, 'initialize'):
                await message_router.initialize()

    # Initialize services
    # Always initialize diagram storage (needed for all modes) - but skip for sub-containers
    if not is_sub_container:
        # Initialize the new diagram storage adapter and service
        if profiler:
            async with profiler.profile_async("persistence.diagram_storage_adapter"):
                await container.persistence.diagram_storage_adapter().initialize()
            async with profiler.profile_async("persistence.diagram_converter"):
                await container.persistence.diagram_converter().initialize()
            async with profiler.profile_async("persistence.diagram_service"):
                await container.persistence.diagram_service().initialize()
        else:
            await container.persistence.diagram_storage_adapter().initialize()
            await container.persistence.diagram_converter().initialize()
            await container.persistence.diagram_service().initialize()
    
    # Initialize LLM service only if needed - skip for sub-containers
    if not is_sub_container:
        if not profile or profile.include_llm_services:
            if not profile or not profile.lazy_load_llm:
                if profiler:
                    async with profiler.profile_async("integration.llm_service"):
                        await container.integration.llm_service().initialize()
                else:
                    await container.integration.llm_service().initialize()
    
    # Initialize API key service - skip for sub-containers
    if not is_sub_container:
        if profiler:
            async with profiler.profile_async("persistence.api_key_service"):
                api_key_service = container.persistence.api_key_service()
                if hasattr(api_key_service, 'initialize'):
                    await api_key_service.initialize()
        else:
            api_key_service = container.persistence.api_key_service()
            if hasattr(api_key_service, 'initialize'):
                await api_key_service.initialize()
    
    # Initialize optional services
    if not profile or profile.include_notion_service:
        if not profile or not profile.lazy_load_integrations:
            if profiler:
                async with profiler.profile_async("integration.notion_service"):
                    notion_service = container.integration.notion_service()
                    if notion_service is not None and hasattr(notion_service, 'initialize'):
                        await notion_service.initialize()
            else:
                notion_service = container.integration.notion_service()
                if notion_service is not None and hasattr(notion_service, 'initialize'):
                    await notion_service.initialize()

    # Initialize execution service
    if not profile or profile.include_execution_service:
        if not profile or not profile.lazy_load_execution:
            if profiler:
                async with profiler.profile_async("application.execution_service"):
                    execution_service = container.application.execution_service()
                    if execution_service is not None:
                        await execution_service.initialize()
            else:
                execution_service = container.application.execution_service()
                if execution_service is not None:
                    await execution_service.initialize()

    # Validate protocol compliance
    if profiler:
        with profiler.profile("validate_protocol_compliance"):
            validate_protocol_compliance(container)
    else:
        validate_protocol_compliance(container)
    
    # Validate required services in registry
    service_registry = container.application.service_registry()
    required_services = [
        "state_store",
        "message_router",
        "llm_service",
        "api_key_service",
        "filesystem_adapter",
        "diagram_storage_adapter",
        "diagram_service"
    ]
    
    validation_results = service_registry.validate_required_services(required_services)
    missing_services = [name for name, present in validation_results.items() if not present]
    
    if missing_services:
        logger.warning(f"Missing required services: {missing_services}")
    
    # Service health status logging removed - method not implemented


async def shutdown_resources(container) -> None:
    """Cleanup all resources comprehensively.
    
    This function ensures all services with cleanup methods are properly
    shut down to prevent resource leaks.
    """
    # Track services that have been cleaned up
    cleaned_services = set()
    
    # Define the order of cleanup (reverse order of initialization)
    cleanup_order = [
        # Application layer (highest level)
        ('application', ['execution_service', 'execution_preparation_service']),
        
        # Dynamic services (stateful, cleanup first)
        ('dynamic', ['conversation_manager', 'person_manager']),
        
        # Integration services
        ('integration', ['llm_service', 'notion_service', 'api_service', 
                        'integrated_diagram_service', 'typescript_parser']),
        
        # Persistence services
        ('persistence', ['message_router', 'state_store', 'file_service',
                        'diagram_loader', 'api_key_service', 'diagram_storage_service',
                        'db_operations_service']),
        
        # Static services (usually no cleanup needed, but check anyway)
        ('static', ['diagram_validator', 'diagram_compiler', 'template_processor']),
        
        # Business logic (usually no cleanup needed)
        ('business', ['validation_service', 'condition_evaluator'])
    ]
    
    logger.info("Starting comprehensive resource cleanup...")
    
    for container_name, service_names in cleanup_order:
        # Get the sub-container
        sub_container = None
        if hasattr(container, container_name):
            sub_container_provider = getattr(container, container_name)
            try:
                sub_container = sub_container_provider()
            except Exception as e:
                logger.warning(f"Failed to access {container_name} container: {e}")
                continue
        
        if not sub_container:
            continue
            
        # Cleanup services in this container
        for service_name in service_names:
            if service_name in cleaned_services:
                continue
                
            try:
                # Get the service provider
                if hasattr(sub_container, service_name):
                    service_provider = getattr(sub_container, service_name)
                    service = service_provider()
                    
                    # Check if service has cleanup method
                    if hasattr(service, 'cleanup'):

                        # Handle both sync and async cleanup methods
                        cleanup_method = getattr(service, 'cleanup')
                        if asyncio.iscoroutinefunction(cleanup_method):
                            await cleanup_method()
                        else:
                            cleanup_method()
                            
                        cleaned_services.add(service_name)

                    # Also check for close() method (common pattern)
                    elif hasattr(service, 'close'):
                        close_method = getattr(service, 'close')
                        if asyncio.iscoroutinefunction(close_method):
                            await close_method()
                        else:
                            close_method()
                        cleaned_services.add(service_name)

            except Exception as e:
                logger.warning(f"Error cleaning up {container_name}.{service_name}: {e}")
    
    # Special handling for services accessed via service registry
    if hasattr(container, 'application') and hasattr(container.application, 'service_registry'):
        try:
            service_registry = container.application.service_registry()
            
            # Additional services that might be in registry but not in containers
            additional_services = ['template']  # Legacy aliases
            
            for service_name in additional_services:
                if service_name in cleaned_services:
                    continue
                    
                service = service_registry.get(service_name)
                if service and hasattr(service, 'cleanup'):
                    cleanup_method = getattr(service, 'cleanup')
                    if asyncio.iscoroutinefunction(cleanup_method):
                        await cleanup_method()
                    else:
                        cleanup_method()
                    cleaned_services.add(service_name)
                    
        except Exception as e:
            logger.warning(f"Error cleaning up registry services: {e}")
    


def validate_protocol_compliance(container) -> None:
    """Validate that all services implement their required protocols."""
    validations = [
        (container.persistence.api_key_service(), SupportsAPIKey, "APIKeyService"),
        (container.integration.llm_service(), LLMServicePort, "LLMInfrastructureService"),
        (container.persistence.filesystem_adapter(), FileSystemPort, "LocalFileSystemAdapter"),
        (container.dynamic.conversation_manager(), ConversationManager, "ConversationManagerImpl"),
        (container.integration.notion_service(), NotionServicePort, "NotionAPIService"),
        (container.integration.integrated_diagram_service(), DiagramPort, "IntegratedDiagramService"),
    ]

    for service, protocol, name in validations:
        if service is not None and not isinstance(service, protocol):
            raise TypeError(
                f"{name} does not implement required protocol {protocol.__name__}"
            )