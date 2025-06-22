"""Application context and dependency injection configuration."""

from contextlib import asynccontextmanager
from typing import TYPE_CHECKING, AsyncGenerator, Optional

from fastapi import FastAPI

from dipeo_server.domains.diagram.services import (
    DiagramStorageService, 
    DiagramConverterService,
    DiagramExecutionAdapter
)
from dipeo_server.domains.execution import ExecutionService
from dipeo_server.domains.execution.services.message_router import message_router
from dipeo_server.domains.execution.services.state_store import state_store
from dipeo_server.domains.integrations import NotionService
from dipeo_server.domains.llm import LLMServiceClass as LLMService
from dipeo_server.domains.person import SimplifiedMemoryService as MemoryService

from .services import APIKeyService, FileService
from pathlib import Path

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


class AppContext:
    """Application-wide common context for services."""

    def __init__(self):
        self.api_key_service: Optional[SupportsAPIKey] = None
        self.llm_service: Optional[SupportsLLM] = None
        self.file_service: Optional[SupportsFile] = None
        self.memory_service: Optional[SupportsMemory] = None
        self.execution_service: Optional[SupportsExecution] = None
        self.notion_service: Optional[SupportsNotion] = None
        # New diagram services
        self.diagram_storage_service: Optional[DiagramStorageService] = None
        self.diagram_converter_service: Optional[DiagramConverterService] = None
        self.diagram_execution_adapter: Optional[DiagramExecutionAdapter] = None

    async def startup(self):
        """Initialize all services on startup."""
        await state_store.initialize()

        await message_router.initialize()

        # Initialize base services
        self.api_key_service = APIKeyService()
        self.memory_service = MemoryService()
        self.llm_service = LLMService(self.api_key_service)
        self.file_service = FileService()
        self.notion_service = NotionService()
        
        # Initialize new diagram services
        from config import FILES_DIR
        from dipeo_server.domains.execution.validators import DiagramValidator
        
        self.diagram_storage_service = DiagramStorageService(
            diagrams_dir=FILES_DIR / "diagrams",
            uploads_dir=FILES_DIR / "uploads"
        )
        self.diagram_converter_service = DiagramConverterService()
        validator = DiagramValidator(self.api_key_service)
        self.diagram_execution_adapter = DiagramExecutionAdapter(
            storage_service=self.diagram_storage_service,
            converter_service=self.diagram_converter_service,
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
            self.diagram_execution_adapter,  # Pass the new adapter
        )
        
        # Initialize services that require it
        await self.llm_service.initialize()
        await self.diagram_storage_service.initialize()
        await self.diagram_converter_service.initialize()
        await self.diagram_execution_adapter.initialize()
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


def get_diagram_converter_service() -> DiagramConverterService:
    """Get DiagramConverterService instance from app context."""
    if app_context.diagram_converter_service is None:
        raise RuntimeError("Application context not initialized")
    return app_context.diagram_converter_service


def get_diagram_execution_adapter() -> DiagramExecutionAdapter:
    """Get DiagramExecutionAdapter instance from app context."""
    if app_context.diagram_execution_adapter is None:
        raise RuntimeError("Application context not initialized")
    return app_context.diagram_execution_adapter
