"""Application context and dependency injection configuration."""

from contextlib import asynccontextmanager
from typing import AsyncGenerator, Optional, TYPE_CHECKING

from fastapi import FastAPI

from src.shared.services.api_key_service import APIKeyService
from src.domains.llm.services.llm_service import LLMService
from src.domains.diagram.services.diagram_service import DiagramService
from src.shared.services.file_service import FileService
from src.domains.person.memory.memory_service import MemoryService
from src.domains.execution.services.execution_service import ExecutionService
from src.domains.integrations.notion.notion_service import NotionService
from src.domains.execution.services.message_router_simple import message_router
from src.domains.execution.services.simple_state_store import state_store
import os

if TYPE_CHECKING:
    from src.shared.service_types import (
        SupportsAPIKey,
        SupportsLLM,
        SupportsDiagram,
        SupportsFile,
        SupportsMemory,
        SupportsExecution,
        SupportsNotion
    )


class AppContext:
    """Application-wide common context for services."""
    
    def __init__(self):
        self.api_key_service: Optional['SupportsAPIKey'] = None
        self.llm_service: Optional['SupportsLLM'] = None
        self.diagram_service: Optional['SupportsDiagram'] = None
        self.file_service: Optional['SupportsFile'] = None
        self.memory_service: Optional['SupportsMemory'] = None
        self.execution_service: Optional['SupportsExecution'] = None
        self.notion_service: Optional['SupportsNotion'] = None
    
    async def startup(self):
        """Initialize all services on startup."""
        # Initialize state store
        await state_store.initialize()
        
        # Initialize message router
        await message_router.initialize()
        
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
        
        # Cleanup state store
        await state_store.cleanup()
        
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
def get_api_key_service() -> 'SupportsAPIKey':
    """Get APIKeyService instance from app context."""
    if app_context.api_key_service is None:
        raise RuntimeError("Application context not initialized")
    return app_context.api_key_service


def get_llm_service() -> 'SupportsLLM':
    """Get LLMService instance from app context."""
    if app_context.llm_service is None:
        raise RuntimeError("Application context not initialized")
    return app_context.llm_service


def get_diagram_service() -> 'SupportsDiagram':
    """Get DiagramService instance from app context."""
    if app_context.diagram_service is None:
        raise RuntimeError("Application context not initialized")
    return app_context.diagram_service


def get_file_service() -> 'SupportsFile':
    """Get FileService instance from app context."""
    if app_context.file_service is None:
        raise RuntimeError("Application context not initialized")
    return app_context.file_service


def get_memory_service() -> 'SupportsMemory':
    """Get MemoryService instance from app context."""
    if app_context.memory_service is None:
        raise RuntimeError("Application context not initialized")
    return app_context.memory_service


def get_execution_service() -> 'SupportsExecution':
    """Get ExecutionService instance from app context."""
    if app_context.execution_service is None:
        raise RuntimeError("Application context not initialized")
    return app_context.execution_service


def get_notion_service() -> 'SupportsNotion':
    """Get NotionService instance from app context."""
    if app_context.notion_service is None:
        raise RuntimeError("Application context not initialized")
    return app_context.notion_service


def get_app_context() -> AppContext:
    """Get AppContext instance for dependency injection."""
    return app_context