# Infrastructure service for database operations.
# This is a backward compatibility wrapper.

from typing import Any

from dipeo.core.ports import FileServicePort
from dipeo.domain.db.services import DBOperationsDomainService as DomainDBService
from dipeo.domain.db.services import DBValidator

from .db_adapter import DBOperationsAdapter


class DBOperationsDomainService:
    """
    Backward compatibility wrapper for DBOperationsDomainService.
    This class maintains the same interface but delegates to the new architecture.
    """

    ALLOWED_OPERATIONS = ["prompt", "read", "write", "append"]

    def __init__(
        self, file_service: FileServicePort, validation_service: DBValidator
    ):
        # Create domain service and adapter
        self.domain_service = DomainDBService()
        self.adapter = DBOperationsAdapter(
            file_service=file_service,
            domain_service=self.domain_service,
            validation_service=validation_service
        )
        # Keep references for backward compatibility
        self.file_service = file_service
        self.validation_service = validation_service

    async def execute_operation(
        self, db_name: str, operation: str, value: Any = None
    ) -> dict[str, Any]:
        """Execute a database operation."""
        return await self.adapter.execute_operation(db_name, operation, value)

    # The following methods are kept for backward compatibility
    # but they now just delegate to the adapter
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