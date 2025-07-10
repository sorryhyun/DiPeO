"""Utility functions for container management."""

import os
from pathlib import Path
from dipeo.core import (
    SupportsAPIKey,
    SupportsExecution,
    SupportsMemory,
)
from dipeo.core.ports import (
    FileServicePort,
    LLMServicePort,
    NotionServicePort,
)
from dipeo.core.ports.diagram_port import DiagramPort


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
    # Initialize infrastructure
    state_store = container.infra.state_store()
    if hasattr(state_store, 'initialize'):
        await state_store.initialize()
    
    message_router = container.infra.message_router()
    if hasattr(message_router, 'initialize'):
        await message_router.initialize()

    # Initialize services
    await container.infra.llm_service().initialize()
    await container.domain.diagram_storage_service().initialize()
    
    notion_service = container.infra.notion_service()
    if notion_service is not None and hasattr(notion_service, 'initialize'):
        await notion_service.initialize()

    # Initialize execution service
    execution_service = container.application.execution_service()
    if execution_service is not None:
        await execution_service.initialize()

    # Validate protocol compliance
    validate_protocol_compliance(container)


async def shutdown_resources(container) -> None:
    """Cleanup all resources."""
    message_router = container.infra.message_router()
    if hasattr(message_router, 'cleanup'):
        await message_router.cleanup()
    
    state_store = container.infra.state_store()
    if hasattr(state_store, 'cleanup'):
        await state_store.cleanup()


def validate_protocol_compliance(container) -> None:
    """Validate that all services implement their required protocols."""
    validations = [
        (container.domain.api_key_service(), SupportsAPIKey, "APIKeyService"),
        (container.infra.llm_service(), LLMServicePort, "LLMInfrastructureService"),
        (container.infra.file_service(), FileServicePort, "FileSystemRepository"),
        (container.domain.conversation_service(), SupportsMemory, "ConversationMemoryService"),
        (container.application.execution_service(), SupportsExecution, "ExecuteDiagramUseCase"),
        (container.infra.notion_service(), NotionServicePort, "NotionAPIService"),
        (container.domain.diagram_storage_service(), DiagramPort, "DiagramFileRepository"),
    ]

    for service, protocol, name in validations:
        if service is not None and not isinstance(service, protocol):
            raise TypeError(
                f"{name} does not implement required protocol {protocol.__name__}"
            )