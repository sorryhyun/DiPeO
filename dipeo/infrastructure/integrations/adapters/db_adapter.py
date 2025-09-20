"""Infrastructure adapter for database operations."""

import json
from pathlib import Path
from typing import Any

from dipeo.domain.base.exceptions import ValidationError
from dipeo.domain.base.storage_port import FileSystemPort
from dipeo.domain.integrations.db_services import DBOperationsDomainService
from dipeo.domain.integrations.validators import DataValidator


class DBOperationsAdapter:
    """
    Infrastructure adapter that bridges domain service with file system operations.
    Handles all I/O operations while delegating business logic to domain service.
    """

    def __init__(
        self,
        file_system: FileSystemPort,
        domain_service: DBOperationsDomainService,
        validation_service: DataValidator,
    ):
        self.file_system = file_system
        self.domain_service = domain_service
        self.validation_service = validation_service

    async def execute_operation(
        self,
        db_name: str,
        operation: str,
        value: Any = None,
        keys: Any = None,
        lines: Any = None,
    ) -> dict[str, Any]:
        self.validation_service.validate_operation(
            operation, self.domain_service.ALLOWED_OPERATIONS
        )
        self.validation_service.validate_db_operation_input(
            operation, value, keys, lines
        )

        if operation == "prompt":
            return self.domain_service.prepare_prompt_response(db_name)

        file_path = await self._get_db_file_path(db_name)

        normalized_keys = self.domain_service.normalize_keys(keys)

        if operation == "read":
            return await self._read_db(file_path, normalized_keys, lines)
        elif operation == "write":
            return await self._write_db(
                file_path, value, normalized_keys or None, operation="write"
            )
        elif operation == "append":
            return await self._append_db(file_path, value)
        elif operation == "update":
            return await self._write_db(
                file_path, value, normalized_keys or None, operation="update"
            )
        else:
            raise ValidationError(
                f"Unsupported operation: {operation}", details={"operation": operation}
            )

    async def _get_db_file_path(self, db_name: str) -> Path:
        db_path = self.domain_service.construct_db_path(db_name)
        path = Path(db_path)
        return path

    async def _read_db(
        self, file_path: Path, keys: list[str] | None = None, lines: Any = None
    ) -> dict[str, Any]:
        try:
            import logging

            logger = logging.getLogger(__name__)

            exists = self.file_system.exists(file_path)
            if not exists:
                logger.warning(f"File not found: {file_path}")
                return self.domain_service.prepare_read_response(
                    {}, str(file_path), 0, keys or []
                )

            with self.file_system.open(file_path, "rb") as f:
                raw_content = f.read()

            content = raw_content.decode("utf-8")

            normalized_ranges = (
                self.domain_service.normalize_line_ranges(lines)
                if lines is not None
                else []
            )
            line_metadata: list[dict[str, int | None]] | None = None
            total_lines: int | None = None

            if normalized_ranges:
                sliced_content, metadata, total_lines = (
                    self.domain_service.extract_lines_from_content(
                        content, normalized_ranges
                    )
                )
                data = sliced_content
                line_metadata = metadata if metadata is not None else []
            else:
                try:
                    data = self.domain_service.validate_json_data(
                        content, str(file_path)
                    )
                except ValidationError:
                    data = content

            size = self.file_system.size(file_path)

            if keys:
                if normalized_ranges:
                    raise ValidationError(
                        "Cannot combine 'keys' and 'lines' for database read operations",
                        details={"file_path": str(file_path)},
                    )
                data = self.domain_service.extract_data_by_keys(data, keys)

            return self.domain_service.prepare_read_response(
                data,
                str(file_path),
                size,
                keys or [],
                line_ranges=line_metadata,
                total_lines=total_lines,
            )
        except ValidationError:
            raise
        except Exception as e:
            raise ValidationError(
                f"Failed to read database: {e!s}", details={"file_path": str(file_path)}
            )

    async def _write_db(
        self,
        file_path: Path,
        value: Any,
        keys: list[str] | None = None,
        operation: str = "write",
    ) -> dict[str, Any]:
        try:
            keys = keys or []
            if operation == "update" and not keys:
                raise ValidationError(
                    "Update operation requires one or more keys",
                    details={"operation": operation},
                )

            is_code_file = any(
                str(file_path).endswith(ext)
                for ext in [
                    ".ts",
                    ".tsx",
                    ".js",
                    ".jsx",
                    ".py",
                    ".graphql",
                    ".md",
                    ".txt",
                    ".yaml",
                    ".yml",
                ]
            )

            if keys:
                existing_data: Any = {}
                if self.file_system.exists(file_path):
                    existing_result = await self._read_db(file_path)
                    existing_data = existing_result["value"]
                updated_data = self.domain_service.update_data_by_keys(
                    existing_data, value, keys
                )
                json_data = self.domain_service.ensure_json_serializable(updated_data)
                content = json.dumps(json_data, indent=2)
            elif is_code_file and isinstance(value, str):
                content = value
                json_data = value  # Keep for response
            else:
                json_data = self.domain_service.ensure_json_serializable(value)
                content = json.dumps(json_data, indent=2)

            parent_dir = file_path.parent
            if not self.file_system.exists(parent_dir):
                self.file_system.mkdir(parent_dir, parents=True)

            with self.file_system.open(file_path, "wb") as f:
                f.write(content.encode("utf-8"))

            if operation == "update" or keys:
                return self.domain_service.prepare_update_response(
                    json_data, str(file_path), len(content), keys
                )

            return self.domain_service.prepare_write_response(
                json_data, str(file_path), len(content), keys or []
            )
        except Exception as e:
            raise ValidationError(
                f"Failed to write database: {e!s}", details={"file_path": str(file_path)}
            )

    async def _append_db(self, file_path: Path, value: Any) -> dict[str, Any]:
        try:
            existing_data = {}
            if self.file_system.exists(file_path):
                result = await self._read_db(file_path)
                existing_data = result["value"]

            updated_data = self.domain_service.prepare_data_for_append(existing_data, value)

            result = await self._write_db(file_path, updated_data)

            return self.domain_service.prepare_append_response(
                updated_data, str(file_path), len(str(updated_data))
            )
        except Exception as e:
            raise ValidationError(
                f"Failed to append to database: {e!s}", details={"file_path": str(file_path)}
            )
