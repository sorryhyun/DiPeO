"""Backward compatibility wrapper for database operations."""

from typing import Any

from dipeo.domain.storage import FileSystemPort
from dipeo.domain.db.services import DBOperationsDomainService as DomainDBService
from dipeo.domain.validators import DataValidator

from dipeo.infrastructure.adapters.database import DBOperationsAdapter


class DBOperationsDomainService:
    """
    Backward compatibility wrapper for DBOperationsDomainService.
    This class maintains the same interface but delegates to the new architecture.
    """

    ALLOWED_OPERATIONS = ["prompt", "read", "write", "append"]

    def __init__(
        self, file_system: FileSystemPort, validation_service: DataValidator
    ):
        self.domain_service = DomainDBService()
        self.adapter = DBOperationsAdapter(
            file_system=file_system,
            domain_service=self.domain_service,
            validation_service=validation_service
        )
        self.file_system = file_system
        self.validation_service = validation_service

    async def execute_operation(
        self, db_name: str, operation: str, value: Any = None
    ) -> dict[str, Any]:
        return await self.adapter.execute_operation(db_name, operation, value)

    async def _get_db_file_path(self, db_name: str) -> str:
        return await self.adapter._get_db_file_path(db_name)

    async def _read_db(self, file_path: str) -> dict[str, Any]:
        return await self.adapter._read_db(file_path)

    async def _write_db(self, file_path: str, value: Any) -> dict[str, Any]:
        return await self.adapter._write_db(file_path, value)

    async def _append_db(self, file_path: str, value: Any) -> dict[str, Any]:
        return await self.adapter._append_db(file_path, value)

    def _ensure_json_serializable(self, value: Any):
        return self.domain_service.ensure_json_serializable(value)