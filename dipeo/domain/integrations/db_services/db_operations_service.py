"""Domain service for database operations."""

import json
from typing import Any

from dipeo.domain.base.exceptions import ValidationError


class DBOperationsDomainService:
    ALLOWED_OPERATIONS = ["prompt", "read", "write", "append"]

    def __init__(self):
        pass

    def validate_operation(self, operation: str) -> None:
        if operation not in self.ALLOWED_OPERATIONS:
            raise ValidationError(
                f"Invalid operation: {operation}. Allowed operations: {self.ALLOWED_OPERATIONS}",
                details={"operation": operation, "allowed": self.ALLOWED_OPERATIONS},
            )

    def validate_operation_input(self, operation: str, value: Any) -> None:
        if operation in ["write", "append"] and value is None:
            raise ValidationError(
                f"Operation '{operation}' requires a value", details={"operation": operation}
            )

    def construct_db_path(self, db_name: str) -> str:
        if not db_name:
            raise ValidationError(
                "Database name cannot be None or empty", details={"db_name": db_name}
            )

        if "/" in db_name or "\\" in db_name:
            return db_name

        safe_db_name = db_name.replace("/", "_").replace("\\", "_")

        import os

        if "." not in os.path.basename(safe_db_name):
            safe_db_name += ".json"

        return f"dbs/{safe_db_name}"

    def prepare_prompt_response(self, db_name: str) -> dict[str, Any]:
        return {"value": db_name, "metadata": {"operation": "prompt", "content_type": "text"}}

    def prepare_read_response(self, data: Any, file_path: str, size: int) -> dict[str, Any]:
        return {
            "value": data,
            "metadata": {
                "operation": "read",
                "file_path": file_path,
                "size": size,
            },
        }

    def prepare_write_response(self, data: Any, file_path: str, size: int) -> dict[str, Any]:
        return {
            "value": data,
            "metadata": {
                "operation": "write",
                "file_path": file_path,
                "size": size,
            },
        }

    def prepare_append_response(
        self, data: Any, file_path: str, items_count: int
    ) -> dict[str, Any]:
        return {
            "value": data,
            "metadata": {
                "operation": "append",
                "file_path": file_path,
                "items_count": items_count,
            },
        }

    def ensure_json_serializable(self, value: Any) -> dict | list | str | int | float | bool | None:
        if isinstance(value, dict | list | str | int | float | bool | type(None)):
            return value
        elif hasattr(value, "dict"):
            return value.dict()
        elif hasattr(value, "__dict__"):
            return value.__dict__
        else:
            return str(value)

    def prepare_data_for_append(self, existing_data: Any, new_value: Any) -> list:
        if not isinstance(existing_data, list):
            if isinstance(existing_data, dict) and not existing_data:
                existing_data = []
            else:
                existing_data = [existing_data]

        new_value = self.ensure_json_serializable(new_value)
        existing_data.append(new_value)

        return existing_data

    def validate_json_data(self, content: str, file_path: str) -> Any:
        try:
            return json.loads(content) if content else {}
        except json.JSONDecodeError as e:
            raise ValidationError(
                f"Invalid JSON in database file: {e!s}", details={"file_path": file_path}
            ) from e
