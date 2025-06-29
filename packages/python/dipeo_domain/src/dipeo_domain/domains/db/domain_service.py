"""Domain service for database operations."""

import json
from typing import Any, Dict, List, Union
from pathlib import Path

from dipeo_core import SupportsFile
from ..validation import ValidationDomainService, BusinessRuleViolationError


class DBOperationsDomainService:
    """Domain service handling database operations with business logic."""

    ALLOWED_OPERATIONS = ["read", "write", "append"]

    def __init__(
        self, file_service: SupportsFile, validation_service: ValidationDomainService
    ):
        self.file_service = file_service
        self.validation_service = validation_service

    async def execute_operation(
        self, db_name: str, operation: str, value: Any = None
    ) -> Dict[str, Any]:
        """Execute a database operation with validation."""
        # Validate operation
        self.validation_service.validate_operation(operation, self.ALLOWED_OPERATIONS)

        # Validate input based on operation
        self.validation_service.validate_db_operation_input(operation, value)

        # Construct file path
        file_path = await self._get_db_file_path(db_name)

        # Execute operation
        if operation == "read":
            return await self._read_db(file_path)
        elif operation == "write":
            return await self._write_db(file_path, value)
        elif operation == "append":
            return await self._append_db(file_path, value)
        else:
            # This should never happen due to validation
            raise BusinessRuleViolationError(
                rule="db_operation",
                message=f"Unsupported operation: {operation}",
                context={"operation": operation},
            )

    async def _get_db_file_path(self, db_name: str) -> str:
        """Get the full path for a database file."""
        # Remove any path separators from db_name for security
        safe_db_name = db_name.replace("/", "_").replace("\\", "_")

        # Add .json extension if not present
        if not safe_db_name.endswith(".json"):
            safe_db_name += ".json"

        # For compatibility with different file services
        if hasattr(self.file_service, "get_safe_path"):
            db_path = await self.file_service.get_safe_path("dbs", safe_db_name)
        else:
            # Simple path construction for basic file services
            db_path = f"dbs/{safe_db_name}"

        return db_path

    async def _read_db(self, file_path: str) -> Dict[str, Any]:
        """Read data from database file."""
        try:
            # Handle different file service types
            # Check if it's a SimpleFileService by trying to call read and seeing if it returns a dict
            try:
                result = self.file_service.read(file_path)
                if isinstance(result, dict) and "success" in result:
                    # SimpleFileService style - returns dict
                    if result.get("success"):
                        data = result.get("content", {})
                        return {
                            "value": data,
                            "metadata": {
                                "operation": "read",
                                "file_path": file_path,
                                "size": result.get("size", 0),
                            },
                        }
                    else:
                        # File doesn't exist
                        return {
                            "value": {},
                            "metadata": {"empty": True, "file_path": file_path},
                        }
            except (AttributeError, TypeError):
                # Standard file service - returns content string
                if not Path(file_path).exists():
                    return {
                        "value": {},
                        "metadata": {"empty": True, "file_path": file_path},
                    }

                content = await self.file_service.read(file_path)
                data = json.loads(content) if content else {}

                return {
                    "value": data,
                    "metadata": {
                        "operation": "read",
                        "file_path": file_path,
                        "size": len(content) if content else 0,
                    },
                }
        except json.JSONDecodeError as e:
            raise BusinessRuleViolationError(
                rule="db_format",
                message=f"Invalid JSON in database file: {str(e)}",
                context={"file_path": file_path},
            )
        except Exception as e:
            raise BusinessRuleViolationError(
                rule="db_read",
                message=f"Failed to read database: {str(e)}",
                context={"file_path": file_path},
            )

    async def _write_db(self, file_path: str, value: Any) -> Dict[str, Any]:
        """Write data to database file."""
        try:
            # For SimpleFileService, we need to ensure the directory structure matches
            # what it expects (it will create person_* subdirs)
            # Just validate that we can write
            Path(file_path).parent.mkdir(parents=True, exist_ok=True)

            # Convert value to JSON
            json_data = self._ensure_json_serializable(value)
            content = json.dumps(json_data, indent=2)

            # Write to file - handle different file service signatures
            import inspect

            if hasattr(self.file_service, "write"):
                sig = inspect.signature(self.file_service.write)
                if "content" in sig.parameters:
                    # SimpleFileService style - keyword argument
                    write_result = await self.file_service.write(
                        file_path, content=content
                    )
                    # Check if write was successful
                    if isinstance(write_result, dict) and not write_result.get(
                        "success", True
                    ):
                        raise Exception(
                            f"Write failed: {write_result.get('error', 'Unknown error')}"
                        )
                else:
                    # Standard file service - positional arguments
                    await self.file_service.write(file_path, content)

            return {
                "value": json_data,
                "metadata": {
                    "operation": "write",
                    "file_path": file_path,
                    "size": len(content),
                },
            }
        except Exception as e:
            raise BusinessRuleViolationError(
                rule="db_write",
                message=f"Failed to write database: {str(e)}",
                context={"file_path": file_path},
            )

    async def _append_db(self, file_path: str, value: Any) -> Dict[str, Any]:
        """Append data to database file."""
        try:
            # Read existing data
            existing_data = {}
            if Path(file_path).exists():
                result = await self._read_db(file_path)
                existing_data = result["value"]

            # Ensure existing data is a list for append
            if not isinstance(existing_data, list):
                if isinstance(existing_data, dict) and not existing_data:
                    # Empty dict, convert to list
                    existing_data = []
                else:
                    # Non-empty dict or other type, wrap in list
                    existing_data = [existing_data]

            # Append new value
            new_value = self._ensure_json_serializable(value)
            existing_data.append(new_value)

            # Write back
            result = await self._write_db(file_path, existing_data)
            result["metadata"]["operation"] = "append"
            result["metadata"]["items_count"] = len(existing_data)

            return result
        except Exception as e:
            raise BusinessRuleViolationError(
                rule="db_append",
                message=f"Failed to append to database: {str(e)}",
                context={"file_path": file_path},
            )

    def _ensure_json_serializable(
        self, value: Any
    ) -> Union[Dict, List, str, int, float, bool, None]:
        """Ensure value is JSON serializable."""
        if isinstance(value, (dict, list, str, int, float, bool, type(None))):
            return value
        elif hasattr(value, "dict"):  # Pydantic models
            return value.dict()
        elif hasattr(value, "__dict__"):  # Regular objects
            return value.__dict__
        else:
            # Convert to string as fallback
            return str(value)
