"""Infrastructure adapter for database operations."""

import json
from pathlib import Path
from typing import Any

from dipeo.core import ValidationError
from dipeo.core.ports import FileServicePort
from dipeo.domain.db.services import DBOperationsDomainService
from dipeo.domain.validators import DataValidator


class DBOperationsAdapter:
    """
    Infrastructure adapter that bridges domain service with file system operations.
    Handles all I/O operations while delegating business logic to domain service.
    """

    def __init__(
        self,
        file_service: FileServicePort,
        domain_service: DBOperationsDomainService,
        validation_service: DataValidator
    ):
        self.file_service = file_service
        self.domain_service = domain_service
        self.validation_service = validation_service

    async def execute_operation(
        self, db_name: str, operation: str, value: Any = None
    ) -> dict[str, Any]:
        """Execute a database operation."""
        # Delegate validation to domain services
        self.validation_service.validate_operation(operation, self.domain_service.ALLOWED_OPERATIONS)
        self.validation_service.validate_db_operation_input(operation, value)

        if operation == "prompt":
            return self.domain_service.prepare_prompt_response(db_name)

        # Get file path using domain logic
        file_path = await self._get_db_file_path(db_name)
        
        if operation == "read":
            return await self._read_db(file_path)
        elif operation == "write":
            return await self._write_db(file_path, value)
        elif operation == "append":
            return await self._append_db(file_path, value)
        else:
            raise ValidationError(
                f"Unsupported operation: {operation}",
                details={"operation": operation}
            )

    async def _get_db_file_path(self, db_name: str) -> str:
        """Get the actual file path for a database."""
        import logging
        log = logging.getLogger(__name__)

        # Use domain service to construct path
        db_path = self.domain_service.construct_db_path(db_name)

        # Handle file service specific path resolution
        if hasattr(self.file_service, "get_safe_path"):
            if "/" not in db_name and "\\" not in db_name:
                # Only use get_safe_path for relative paths
                path_parts = db_path.split("/")
                if len(path_parts) == 2 and path_parts[0] == "dbs":
                    db_path = await self.file_service.get_safe_path("dbs", path_parts[1])

        log.debug(f"Constructed db_path: '{db_path}'")
        return db_path

    async def _read_db(self, file_path: str) -> dict[str, Any]:
        """Read database file and return formatted response."""
        import logging
        log = logging.getLogger(__name__)

        try:
            # Handle file service read operation
            try:
                # ModularFileService expects file_id relative to base_dir
                # If path starts with known directories, use it as-is
                if file_path.startswith(('files/', 'dbs/', 'prompts/')):
                    # Remove the base directory prefix since ModularFileService will add it
                    file_id = file_path
                else:
                    file_id = file_path
                
                result = self.file_service.read(file_id)

                if isinstance(result, dict) and "success" in result:
                    if result.get("success"):
                        content = result.get("content", "{}")
                        
                        # ModularFileService may have already parsed the content
                        if isinstance(content, (dict, list)):
                            # Already parsed - use as-is
                            data = content
                        else:
                            # Try to parse as JSON, fall back to plain text
                            try:
                                data = self.domain_service.validate_json_data(content, file_path)
                            except ValidationError:
                                # Not JSON, treat as plain text
                                data = content
                        return self.domain_service.prepare_read_response(
                            data, file_path, result.get("size", 0)
                        )
                    else:
                        return self.domain_service.prepare_read_response(
                            {}, file_path, 0
                        )
            except (AttributeError, TypeError):
                # Handle async file service
                try:
                    content = await self.file_service.read(file_path)
                    # Try to parse as JSON, fall back to plain text
                    try:
                        data = self.domain_service.validate_json_data(content, file_path)
                    except ValidationError:
                        # Not JSON, treat as plain text
                        data = content
                    return self.domain_service.prepare_read_response(
                        data, file_path, len(content) if content else 0
                    )
                except Exception:
                    return self.domain_service.prepare_read_response(
                        {}, file_path, 0
                    )
        except ValidationError:
            # Re-raise domain validation errors
            raise
        except Exception as e:
            raise ValidationError(
                f"Failed to read database: {e!s}",
                details={"file_path": file_path}
            )

    async def _write_db(self, file_path: str, value: Any) -> dict[str, Any]:
        """Write data to database file."""
        try:
            # Check if this is a code file (non-JSON) and value is already a string
            is_code_file = any(file_path.endswith(ext) for ext in ['.ts', '.tsx', '.js', '.jsx', '.py', '.graphql', '.md', '.txt'])
            
            if is_code_file and isinstance(value, str):
                # For code files, write the string content directly
                content = value
                json_data = value  # Keep for response
            else:
                # Use domain service to prepare data for JSON files
                json_data = self.domain_service.ensure_json_serializable(value)
                content = json.dumps(json_data, indent=2)

            # Handle file service write operation
            import inspect
            if hasattr(self.file_service, "write"):
                sig = inspect.signature(self.file_service.write)
                if "content" in sig.parameters:
                    write_result = await self.file_service.write(
                        file_path, content=content
                    )
                    if isinstance(write_result, dict) and not write_result.get(
                        "success", True
                    ):
                        raise Exception(
                            f"Write failed: {write_result.get('error', 'Unknown error')}"
                        )
                else:
                    await self.file_service.write(file_path, content)

            return self.domain_service.prepare_write_response(
                json_data, file_path, len(content)
            )
        except Exception as e:
            raise ValidationError(
                f"Failed to write database: {e!s}",
                details={"file_path": file_path}
            )

    async def _append_db(self, file_path: str, value: Any) -> dict[str, Any]:
        """Append data to database file."""
        try:
            # Read existing data
            existing_data = {}
            if Path(file_path).exists():
                result = await self._read_db(file_path)
                existing_data = result["value"]

            # Use domain service to prepare data for append
            updated_data = self.domain_service.prepare_data_for_append(
                existing_data, value
            )

            # Write updated data
            result = await self._write_db(file_path, updated_data)
            
            # Return append-specific response
            return self.domain_service.prepare_append_response(
                updated_data, file_path, len(updated_data)
            )
        except Exception as e:
            raise ValidationError(
                f"Failed to append to database: {e!s}",
                details={"file_path": file_path}
            )