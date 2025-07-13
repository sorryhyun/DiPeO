"""Utility functions for container management."""

import os
from pathlib import Path
from dipeo.application.protocols import (
    SupportsAPIKey,
)
from dipeo.core.ports import (
    FileServicePort,
    LLMServicePort,
    NotionServicePort,
)
from dipeo.core.ports.diagram_port import DiagramPort
from dipeo.core.dynamic.conversation_manager import ConversationManager
from .profiling import get_profiler
from .core.container_profiles import ContainerProfile


def get_project_base_dir():
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


async def init_resources(container) -> None:
    """Initialize all resources that require async setup."""
    profiler = get_profiler()
    # Get profile from the Container class
    from .container import Container as ContainerClass
    profile = ContainerClass.get_profile() if hasattr(ContainerClass, 'get_profile') else None
    # Profile is now available for conditional initialization
    
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
    # Always initialize diagram storage (needed for all modes)
    if profiler:
        async with profiler.profile_async("persistence.diagram_storage"):
            await container.persistence.diagram_storage_service().initialize()
    else:
        await container.persistence.diagram_storage_service().initialize()
    
    # Initialize LLM service only if needed
    if not profile or profile.include_llm_services:
        if not profile or not profile.lazy_load_llm:
            if profiler:
                async with profiler.profile_async("integration.llm_service"):
                    await container.integration.llm_service().initialize()
            else:
                await container.integration.llm_service().initialize()
    
    # Initialize API key service
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


async def shutdown_resources(container) -> None:
    """Cleanup all resources."""
    message_router = container.persistence.message_router()
    if hasattr(message_router, 'cleanup'):
        await message_router.cleanup()
    
    state_store = container.persistence.state_store()
    if hasattr(state_store, 'cleanup'):
        await state_store.cleanup()


def validate_protocol_compliance(container) -> None:
    """Validate that all services implement their required protocols."""
    validations = [
        (container.persistence.api_key_service(), SupportsAPIKey, "APIKeyService"),
        (container.integration.llm_service(), LLMServicePort, "LLMInfrastructureService"),
        (container.persistence.file_service(), FileServicePort, "FileSystemRepository"),
        (container.dynamic.conversation_manager(), ConversationManager, "ConversationManagerImpl"),
        (container.integration.notion_service(), NotionServicePort, "NotionAPIService"),
        (container.persistence.diagram_storage_service(), DiagramPort, "DiagramFileRepository"),
    ]

    for service, protocol, name in validations:
        if service is not None and not isinstance(service, protocol):
            raise TypeError(
                f"{name} does not implement required protocol {protocol.__name__}"
            )