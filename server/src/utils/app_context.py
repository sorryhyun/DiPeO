"""Application context and dependency injection configuration."""

from contextlib import asynccontextmanager
from typing import AsyncGenerator, Optional

from fastapi import FastAPI

from ..services.api_key_service import APIKeyService
from ..services.llm_service import LLMService
from ..services.diagram_service import DiagramService
from ..services.file_service import FileService
from ..services.memory_service import MemoryService
from ..services.execution_service import ExecutionService
from ..services.notion_service import NotionService
from ..services.message_router import message_router
from ..services.event_store import event_store
from ...config import BASE_DIR


class AppContext:
    """Application-wide common context for services."""
    
    def __init__(self):
        self.api_key_service: Optional[APIKeyService] = None
        self.llm_service: Optional[LLMService] = None
        self.diagram_service: Optional[DiagramService] = None
        self.file_service: Optional[FileService] = None
        self.memory_service: Optional[MemoryService] = None
        self.execution_service: Optional[ExecutionService] = None
        self.notion_service: Optional[NotionService] = None
    
    async def startup(self):
        """Initialize all services on startup."""
        # Initialize event store
        await event_store.initialize()
        
        # Initialize services in dependency order
        self.api_key_service = APIKeyService()
        self.memory_service = MemoryService()
        self.llm_service = LLMService(self.api_key_service)
        self.file_service = FileService(base_dir=BASE_DIR)
        self.diagram_service = DiagramService(
            self.llm_service, 
            self.api_key_service, 
            self.memory_service
        )
        self.notion_service = NotionService()
        self.execution_service = ExecutionService(
            self.llm_service,
            self.api_key_service,
            self.memory_service,
            self.file_service,
            self.diagram_service,
            self.notion_service
        )
    
    async def shutdown(self):
        """Cleanup resources on shutdown."""
        # Cleanup message router connections
        await message_router.cleanup()
        
        # Cleanup event store
        await event_store.cleanup()
        
        # Add any other cleanup logic here if needed
        # For example, closing database connections, saving state, etc.


# Global application context instance
app_context = AppContext()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator:
    """FastAPI lifespan context manager for proper startup/shutdown."""
    # Startup
    await app_context.startup()
    yield
    # Shutdown
    await app_context.shutdown()


# Dependency functions that use the state context
def get_api_key_service() -> APIKeyService:
    """Get APIKeyService instance from app context."""
    if app_context.api_key_service is None:
        raise RuntimeError("Application context not initialized")
    return app_context.api_key_service


def get_llm_service() -> LLMService:
    """Get LLMService instance from app context."""
    if app_context.llm_service is None:
        raise RuntimeError("Application context not initialized")
    return app_context.llm_service


def get_diagram_service() -> DiagramService:
    """Get DiagramService instance from app context."""
    if app_context.diagram_service is None:
        raise RuntimeError("Application context not initialized")
    return app_context.diagram_service


def get_file_service() -> FileService:
    """Get FileService instance from app context."""
    if app_context.file_service is None:
        raise RuntimeError("Application context not initialized")
    return app_context.file_service


def get_memory_service() -> MemoryService:
    """Get MemoryService instance from app context."""
    if app_context.memory_service is None:
        raise RuntimeError("Application context not initialized")
    return app_context.memory_service


def get_execution_service() -> ExecutionService:
    """Get ExecutionService instance from app context."""
    if app_context.execution_service is None:
        raise RuntimeError("Application context not initialized")
    return app_context.execution_service


def get_notion_service() -> NotionService:
    """Get NotionService instance from app context."""
    if app_context.notion_service is None:
        raise RuntimeError("Application context not initialized")
    return app_context.notion_service


def get_app_context() -> AppContext:
    """Get AppContext instance for dependency injection."""
    return app_context