"""Application context and dependency injection configuration."""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from typing import TYPE_CHECKING

from dipeo_container.app_context_adapter import AppContextAdapter
from fastapi import FastAPI

from .container import ServerContainer, init_server_resources, shutdown_server_resources

if TYPE_CHECKING:
    from dipeo_core import (
        SupportsAPIKey,
        SupportsDiagram,
        SupportsExecution,
        SupportsFile,
        SupportsLLM,
        SupportsMemory,
        SupportsNotion,
    )
    from dipeo_domain.domains.diagram.services import (
        DiagramStorageAdapter,
    )
    from dipeo_domain.domains.execution import PrepareDiagramForExecutionUseCase
    from dipeo_domain.domains.api import APIIntegrationDomainService
    from dipeo_domain.domains.file import FileOperationsDomainService
    from dipeo_domain.domains.text import TextProcessingDomainService
    from dipeo_infra import MessageRouter

    from dipeo_server.infra.persistence.state_registry import StateRegistry


# Global container instance
_container: ServerContainer | None = None

# Global app context adapter for backward compatibility
_app_context: AppContextAdapter | None = None


def get_container() -> ServerContainer:
    """Get the global DI container instance."""
    if _container is None:
        raise RuntimeError("Container not initialized. Call initialize_container() first.")
    return _container


def initialize_container() -> ServerContainer:
    """Initialize the global DI container."""
    global _container, _app_context

    if _container is None:
        _container = ServerContainer()
        # Configure from environment - no need to call from_env() for now
        # as we're using factory functions that handle env vars directly

        # Wire the container to necessary modules
        _container.wire(modules=[
            "dipeo_server.api.graphql.queries",
            "dipeo_server.api.graphql.mutations",
            "dipeo_server.api.graphql.subscriptions",
            "dipeo_server.api.graphql.resolvers",
            "dipeo_domain.domains.execution.services",
        ])

        # Create app context adapter
        _app_context = AppContextAdapter(_container)

    return _container


class AppContext:
    """
    Legacy AppContext class that now delegates to the DI container.
    Maintained for backward compatibility.
    """

    def __init__(self):
        # Initialize container if not already done
        self._container = initialize_container()
        # Get the adapter from the global variable
        self._adapter = _app_context

    def __getattr__(self, name: str):
        """Delegate all attribute access to the adapter."""
        return getattr(self._adapter, name)

    async def startup(self):
        """Initialize all resources."""
        await init_server_resources(self._container)

    async def shutdown(self):
        """Cleanup all resources."""
        await shutdown_server_resources(self._container)

    # Properties to maintain type hints for IDE support
    @property
    def api_key_service(self) -> "SupportsAPIKey":
        return self._adapter.api_key_service

    @property
    def llm_service(self) -> "SupportsLLM":
        return self._adapter.llm_service

    @property
    def file_service(self) -> "SupportsFile":
        return self._adapter.file_service

    @property
    def conversation_service(self) -> "SupportsMemory":
        return self._adapter.conversation_service

    @property
    def execution_service(self) -> "SupportsExecution":
        return self._adapter.execution_service

    @property
    def notion_service(self) -> "SupportsNotion":
        return self._adapter.notion_service

    @property
    def diagram_storage_service(self) -> "SupportsDiagram":
        return self._adapter.diagram_storage_service

    @property
    def diagram_storage_adapter(self) -> "DiagramStorageAdapter":
        return self._adapter.diagram_storage_adapter

    @property
    def execution_preparation_service(self) -> "PrepareDiagramForExecutionUseCase":
        return self._adapter.execution_preparation_service

    @property
    def api_integration_service(self) -> "APIIntegrationDomainService":
        return self._adapter.api_integration_service

    @property
    def text_processing_service(self) -> "TextProcessingDomainService":
        return self._adapter.text_processing_service

    @property
    def file_operations_service(self) -> "FileOperationsDomainService":
        return self._adapter.file_operations_service

    @property
    def state_store(self) -> "StateRegistry":
        return self._adapter.state_store

    @property
    def message_router(self) -> "MessageRouter":
        return self._adapter.message_router


app_context = AppContext()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator:
    await app_context.startup()
    yield
    await app_context.shutdown()


def get_api_key_service() -> "SupportsAPIKey":
    if app_context.api_key_service is None:
        raise RuntimeError("Application context not initialized")
    return app_context.api_key_service


def get_llm_service() -> "SupportsLLM":
    if app_context.llm_service is None:
        raise RuntimeError("Application context not initialized")
    return app_context.llm_service


def get_file_service() -> "SupportsFile":
    if app_context.file_service is None:
        raise RuntimeError("Application context not initialized")
    return app_context.file_service


def get_conversation_service() -> "SupportsMemory":
    if app_context.conversation_service is None:
        raise RuntimeError("Application context not initialized")
    return app_context.conversation_service


def get_execution_service() -> "SupportsExecution":
    if app_context.execution_service is None:
        raise RuntimeError("Application context not initialized")
    return app_context.execution_service


def get_notion_service() -> "SupportsNotion":
    if app_context.notion_service is None:
        raise RuntimeError("Application context not initialized")
    return app_context.notion_service


def get_app_context() -> AppContext:
    return app_context


def get_diagram_storage_service() -> "SupportsDiagram":
    if app_context.diagram_storage_service is None:
        raise RuntimeError("Application context not initialized")
    return app_context.diagram_storage_service


def get_diagram_storage_adapter() -> "DiagramStorageAdapter":
    if app_context.diagram_storage_adapter is None:
        raise RuntimeError("Application context not initialized")
    return app_context.diagram_storage_adapter


def get_execution_preparation_service() -> "PrepareDiagramForExecutionUseCase":
    if app_context.execution_preparation_service is None:
        raise RuntimeError("Application context not initialized")
    return app_context.execution_preparation_service
