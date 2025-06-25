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
    def __init__(self):
        self.api_key_service: Optional[SupportsAPIKey] = None
        self.llm_service: Optional[SupportsLLM] = None
        self.file_service: Optional[SupportsFile] = None
        self.memory_service: Optional[SupportsMemory] = None
        self.execution_service: Optional[SupportsExecution] = None
        self.notion_service: Optional[SupportsNotion] = None
        self.diagram_storage_service: Optional[DiagramStorageService] = None
        self.diagram_storage_adapter: Optional[DiagramStorageAdapter] = None
        self.execution_preparation_service: Optional[ExecutionPreparationService] = None

    async def startup(self):
        await state_store.initialize()

        await message_router.initialize()

        self.api_key_service = APIKeyService()
        self.memory_service = MemoryService()
        self.llm_service = LLMService(self.api_key_service)
        self.file_service = FileService(base_dir=BASE_DIR)
        self.notion_service = NotionService()

        self.diagram_storage_service = DiagramStorageService(
            base_dir=BASE_DIR,
        )
        self.diagram_storage_adapter = DiagramStorageAdapter(
            storage_service=self.diagram_storage_service
        )

        validator = DiagramValidator(self.api_key_service)
        self.execution_preparation_service = ExecutionPreparationService(
            storage_service=self.diagram_storage_service,
            validator=validator,
            api_key_service=self.api_key_service,
        )

        self.execution_service = ExecutionService(
            self.llm_service,
            self.api_key_service,
            self.memory_service,
            self.file_service,
            None,
            self.notion_service,
            self.execution_preparation_service,
        )

        await self.llm_service.initialize()
        await self.diagram_storage_service.initialize()
        await self.notion_service.initialize()
        await self.execution_service.initialize()

    async def shutdown(self):
        await message_router.cleanup()

        await state_store.cleanup()


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


def get_memory_service() -> "SupportsMemory":
    if app_context.memory_service is None:
        raise RuntimeError("Application context not initialized")
    return app_context.memory_service


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


def get_diagram_storage_service() -> DiagramStorageService:
    if app_context.diagram_storage_service is None:
        raise RuntimeError("Application context not initialized")
    return app_context.diagram_storage_service


def get_diagram_storage_adapter() -> DiagramStorageAdapter:
    if app_context.diagram_storage_adapter is None:
        raise RuntimeError("Application context not initialized")
    return app_context.diagram_storage_adapter


def get_execution_preparation_service() -> ExecutionPreparationService:
    if app_context.execution_preparation_service is None:
        raise RuntimeError("Application context not initialized")
    return app_context.execution_preparation_service
