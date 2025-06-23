"""Application context and dependency injection configuration."""

from contextlib import asynccontextmanager
from typing import TYPE_CHECKING, AsyncGenerator, Optional

from fastapi import FastAPI

from config import BASE_DIR
from dipeo_server.domains.apikey import APIKeyService
from dipeo_server.domains.diagram.services import (
    DiagramStorageAdapter,
    DiagramStorageService,
)
from dipeo_server.domains.execution import (
    ExecutionPreparationService,
    ExecutionService,
)
from dipeo_server.domains.execution.validators import DiagramValidator
from dipeo_server.domains.integrations import NotionService
from dipeo_server.domains.llm import LLMServiceClass as LLMService
from dipeo_server.domains.person import MemoryService
from dipeo_server.infrastructure.messaging import message_router
from dipeo_server.infrastructure.persistence import FileService, state_store

if TYPE_CHECKING:
    from dipeo_core import (
        SupportsAPIKey,
        SupportsExecution,
        SupportsFile,
        SupportsLLM,
        SupportsMemory,
        SupportsNotion,
    )


class AppContext:
    """Application-wide common context for services."""

    def __init__(self):
        self.api_key_service: Optional[SupportsAPIKey] = None
        self.llm_service: Optional[SupportsLLM] = None
        self.file_service: Optional[SupportsFile] = None
        self.memory_service: Optional[SupportsMemory] = None
        self.execution_service: Optional[SupportsExecution] = None
        self.notion_service: Optional[SupportsNotion] = None
        # Diagram services
        self.diagram_storage_service: Optional[DiagramStorageService] = None
        self.diagram_storage_adapter: Optional[DiagramStorageAdapter] = None
        # Execution services
        self.execution_preparation_service: Optional[ExecutionPreparationService] = None

    async def startup(self):
        """Initialize all services on startup."""
        await state_store.initialize()

        await message_router.initialize()

        # Initialize base services
        self.api_key_service = APIKeyService()
        self.memory_service = MemoryService()
        self.llm_service = LLMService(self.api_key_service)
        self.file_service = FileService(base_dir=BASE_DIR)
        self.notion_service = NotionService()

        # Initialize diagram services
        self.diagram_storage_service = DiagramStorageService(
            base_dir = BASE_DIR,
        )
        self.diagram_storage_adapter = DiagramStorageAdapter(
            storage_service=self.diagram_storage_service
        )

        # Initialize execution preparation service
        validator = DiagramValidator(self.api_key_service)
        self.execution_preparation_service = ExecutionPreparationService(
            storage_service=self.diagram_storage_service,
            validator=validator,
            api_key_service=self.api_key_service
        )

        # Initialize execution service
        self.execution_service = ExecutionService(
            self.llm_service,
            self.api_key_service,
            self.memory_service,
            self.file_service,
            None,  # diagram_service removed
            self.notion_service,
            self.execution_preparation_service,
        )

        # Initialize services that require it
        await self.llm_service.initialize()
        await self.diagram_storage_service.initialize()
        await self.notion_service.initialize()
        await self.execution_service.initialize()

    async def shutdown(self):
        """Cleanup resources on shutdown."""
        await message_router.cleanup()

        await state_store.cleanup()


app_context = AppContext()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator:
    """FastAPI lifespan context manager for proper startup/shutdown."""
    # Startup
    await app_context.startup()
    yield
    # Shutdown
    await app_context.shutdown()


def get_api_key_service() -> "SupportsAPIKey":
    """Get APIKeyService instance from app context."""
    if app_context.api_key_service is None:
        raise RuntimeError("Application context not initialized")
    return app_context.api_key_service


def get_llm_service() -> "SupportsLLM":
    """Get LLMService instance from app context."""
    if app_context.llm_service is None:
        raise RuntimeError("Application context not initialized")
    return app_context.llm_service


def get_file_service() -> "SupportsFile":
    """Get FileService instance from app context."""
    if app_context.file_service is None:
        raise RuntimeError("Application context not initialized")
    return app_context.file_service


def get_memory_service() -> "SupportsMemory":
    """Get MemoryService instance from app context."""
    if app_context.memory_service is None:
        raise RuntimeError("Application context not initialized")
    return app_context.memory_service


def get_execution_service() -> "SupportsExecution":
    """Get ExecutionService instance from app context."""
    if app_context.execution_service is None:
        raise RuntimeError("Application context not initialized")
    return app_context.execution_service


def get_notion_service() -> "SupportsNotion":
    """Get NotionService instance from app context."""
    if app_context.notion_service is None:
        raise RuntimeError("Application context not initialized")
    return app_context.notion_service


def get_app_context() -> AppContext:
    """Get AppContext instance for dependency injection."""
    return app_context


def get_diagram_storage_service() -> DiagramStorageService:
    """Get DiagramStorageService instance from app context."""
    if app_context.diagram_storage_service is None:
        raise RuntimeError("Application context not initialized")
    return app_context.diagram_storage_service


def get_diagram_storage_adapter() -> DiagramStorageAdapter:
    """Get DiagramStorageAdapter instance from app context."""
    if app_context.diagram_storage_adapter is None:
        raise RuntimeError("Application context not initialized")
    return app_context.diagram_storage_adapter


def get_execution_preparation_service() -> ExecutionPreparationService:
    """Get ExecutionPreparationService instance from app context."""
    if app_context.execution_preparation_service is None:
        raise RuntimeError("Application context not initialized")
    return app_context.execution_preparation_service
