# Domain service for database operations.

import json
from typing import Any, Dict, List, Union
from pathlib import Path

from dipeo.core import SupportsFile
from ..validation import ValidationDomainService, BusinessRuleViolationError


class DBOperationsDomainService:
    # Domain service handling database operations with business logic.
    # Supports read, write, and append operations with validation.
    # Handles different file service implementations.

    ALLOWED_OPERATIONS = ["prompt", "read", "write", "append"]

    def __init__(
        self, file_service: SupportsFile, validation_service: ValidationDomainService
    ):
        self.file_service = file_service
        self.validation_service = validation_service

    async def execute_operation(
        self, db_name: str, operation: str, value: Any = None
    ) -> Dict[str, Any]:
        self.validation_service.validate_operation(operation, self.ALLOWED_OPERATIONS)
        self.validation_service.validate_db_operation_input(operation, value)

        if operation == "prompt":
            # For prompt operation, return the db_name directly as the prompt content
            return {
                "value": db_name,
                "metadata": {
                    "operation": "prompt",
                    "content_type": "text"
                }
            }
        
        # For file-based operations, get the file path
        file_path = await self._get_db_file_path(db_name)
        
        if operation == "read":
            return await self._read_db(file_path)
        elif operation == "write":
            return await self._write_db(file_path, value)
        elif operation == "append":
            return await self._append_db(file_path, value)
        else:
            raise BusinessRuleViolationError(
                rule="db_operation",
                message=f"Unsupported operation: {operation}",
                context={"operation": operation},
            )

    async def _get_db_file_path(self, db_name: str) -> str:
        import logging

        log = logging.getLogger(__name__)

        if "/" in db_name or "\\" in db_name:
            return db_name

        safe_db_name = db_name.replace("/", "_").replace("\\", "_")

        if not safe_db_name.endswith(".json"):
            safe_db_name += ".json"

        if hasattr(self.file_service, "get_safe_path"):
            db_path = await self.file_service.get_safe_path("dbs", safe_db_name)
        else:
            db_path = f"dbs/{safe_db_name}"

        log.debug(f"Constructed db_path: '{db_path}'")
        return db_path

    async def _read_db(self, file_path: str) -> Dict[str, Any]:
        import logging

        log = logging.getLogger(__name__)

        try:
            try:
                result = self.file_service.read(file_path)

                if isinstance(result, dict) and "success" in result:
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
                        log.debug("SimpleFileService - file doesn't exist")
                        return {
                            "value": {},
                            "metadata": {"empty": True, "file_path": file_path},
                        }
            except (AttributeError, TypeError):
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
        try:
            Path(file_path).parent.mkdir(parents=True, exist_ok=True)
            json_data = self._ensure_json_serializable(value)
            content = json.dumps(json_data, indent=2)

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
        try:
            existing_data = {}
            if Path(file_path).exists():
                result = await self._read_db(file_path)
                existing_data = result["value"]

            if not isinstance(existing_data, list):
                if isinstance(existing_data, dict) and not existing_data:
                    existing_data = []
                else:
                    existing_data = [existing_data]

            new_value = self._ensure_json_serializable(value)
            existing_data.append(new_value)

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
        if isinstance(value, (dict, list, str, int, float, bool, type(None))):
            return value
        elif hasattr(value, "dict"):  # Pydantic models
            return value.dict()
        elif hasattr(value, "__dict__"):  # Regular objects
            return value.__dict__
        else:
            # Convert to string as fallback
            return str(value)
