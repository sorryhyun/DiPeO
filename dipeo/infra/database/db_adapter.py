"""Infrastructure adapter for database operations."""

import json
from pathlib import Path
from typing import Any

from dipeo.core import ValidationError
from dipeo.domain.ports.storage import FileSystemPort
from dipeo.domain.db.services import DBOperationsDomainService
from dipeo.domain.validators import DataValidator


class DBOperationsAdapter:
    """
    Infrastructure adapter that bridges domain service with file system operations.
    Handles all I/O operations while delegating business logic to domain service.
    """

    def __init__(
        self,
        file_system: FileSystemPort,
        domain_service: DBOperationsDomainService,
        validation_service: DataValidator
    ):
        self.file_system = file_system
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

    async def _get_db_file_path(self, db_name: str) -> Path:
        """Get the actual file path for a database."""
        # Use domain service to construct path
        db_path = self.domain_service.construct_db_path(db_name)
        
        # Convert to Path object
        return Path(db_path)

    async def _read_db(self, file_path: Path) -> dict[str, Any]:
        """Read database file and return formatted response."""
        try:
            # Check if file exists
            if not self.file_system.exists(file_path):
                return self.domain_service.prepare_read_response(
                    {}, str(file_path), 0
                )
            
            # Read file content using FileSystemPort
            with self.file_system.open(file_path, "rb") as f:
                raw_content = f.read()
            
            # Decode content
            content = raw_content.decode('utf-8')
            
            # Try to parse as JSON, fall back to plain text
            try:
                data = self.domain_service.validate_json_data(content, str(file_path))
            except ValidationError:
                # Not JSON, treat as plain text
                data = content
            
            # Get file size
            size = self.file_system.size(file_path)
            
            return self.domain_service.prepare_read_response(
                data, str(file_path), size
            )
        except ValidationError:
            # Re-raise domain validation errors
            raise
        except Exception as e:
            raise ValidationError(
                f"Failed to read database: {e!s}",
                details={"file_path": str(file_path)}
            )

    async def _write_db(self, file_path: Path, value: Any) -> dict[str, Any]:
        """Write data to database file."""
        try:
            # Check if this is a code file (non-JSON) and value is already a string
            is_code_file = any(str(file_path).endswith(ext) for ext in ['.ts', '.tsx', '.js', '.jsx', '.py', '.graphql', '.md', '.txt'])
            
            if is_code_file and isinstance(value, str):
                # For code files, write the string content directly
                content = value
                json_data = value  # Keep for response
            else:
                # Use domain service to prepare data for JSON files
                json_data = self.domain_service.ensure_json_serializable(value)
                content = json.dumps(json_data, indent=2)

            # Ensure parent directory exists
            parent_dir = file_path.parent
            if not self.file_system.exists(parent_dir):
                self.file_system.mkdir(parent_dir, parents=True)

            # Write file content using FileSystemPort
            with self.file_system.open(file_path, "wb") as f:
                f.write(content.encode('utf-8'))

            return self.domain_service.prepare_write_response(
                json_data, str(file_path), len(content)
            )
        except Exception as e:
            raise ValidationError(
                f"Failed to write database: {e!s}",
                details={"file_path": str(file_path)}
            )

    async def _append_db(self, file_path: Path, value: Any) -> dict[str, Any]:
        """Append data to database file."""
        try:
            # Read existing data
            existing_data = {}
            if self.file_system.exists(file_path):
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
                updated_data, str(file_path), len(str(updated_data))
            )
        except Exception as e:
            raise ValidationError(
                f"Failed to append to database: {e!s}",
                details={"file_path": str(file_path)}
            )