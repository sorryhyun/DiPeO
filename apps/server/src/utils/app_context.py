"""Application context and dependency injection configuration."""

from contextlib import asynccontextmanager
from typing import AsyncGenerator, Optional

from fastapi import FastAPI

from ..services.api_key_service import APIKeyService
from ..services.llm_service import LLMService
from ..services.diagram_service import DiagramService
from ..services.file_service import FileService
from ..services.memory_service import MemoryService


class AppContext:
    """Application-wide shared context for services."""
    
    def __init__(self):
        self.api_key_service: Optional[APIKeyService] = None
        self.llm_service: Optional[LLMService] = None
        self.diagram_service: Optional[DiagramService] = None
        self.file_service: Optional[FileService] = None
        self.memory_service: Optional[MemoryService] = None
    
    async def startup(self):
        """Initialize all services on startup."""
        # Initialize services in dependency order
        self.api_key_service = APIKeyService()
        self.memory_service = MemoryService()
        self.llm_service = LLMService(self.api_key_service)
        self.file_service = FileService()
        self.diagram_service = DiagramService(
            self.llm_service, 
            self.api_key_service, 
            self.memory_service
        )
    
    async def shutdown(self):
        """Cleanup resources on shutdown."""
        # Add any cleanup logic here if needed
        # For example, closing database connections, saving state, etc.
        pass


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


# Dependency functions that use the global context
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