"""Domain service for database operations."""

import json
from collections.abc import Iterable, Sequence
from typing import Any

from dipeo.domain.base.exceptions import ValidationError


class DBOperationsDomainService:
    ALLOWED_OPERATIONS = ["prompt", "read", "write", "append", "update"]

    def __init__(self):
        pass

    def validate_operation(self, operation: str) -> None:
        if operation not in self.ALLOWED_OPERATIONS:
            raise ValidationError(
                f"Invalid operation: {operation}. Allowed operations: {self.ALLOWED_OPERATIONS}",
                details={"operation": operation, "allowed": self.ALLOWED_OPERATIONS},
            )

    def validate_operation_input(self, operation: str, value: Any) -> None:
        if operation in ["write", "append", "update"] and value is None:
            raise ValidationError(
                f"Operation '{operation}' requires a value", details={"operation": operation}
            )

    def normalize_keys(self, keys: Any) -> list[str]:
        if keys is None:
            return []

        if isinstance(keys, str):
            parts = [part.strip() for part in keys.split(",") if part.strip()]
            return parts if parts else []

        if isinstance(keys, Iterable):
            normalized: list[str] = []
            for key in keys:
                if key is None:
                    continue
                if not isinstance(key, str):
                    raise ValidationError(
                        "Database key must be a string",
                        details={"key": key},
                    )
                key = key.strip()
                if key:
                    normalized.append(key)
            return normalized

        raise ValidationError(
            "Database keys must be provided as a string or list of strings",
            details={"keys": keys},
        )

    def _coerce_line_endpoint(self, value: Any, field_name: str) -> int | None:
        if value is None:
            return None

        if isinstance(value, bool):
            raise ValidationError(
                f"Line range {field_name} cannot be a boolean",
                details={"value": value},
            )

        if isinstance(value, int):
            if value < 1:
                raise ValidationError(
                    "Line numbers must be positive integers (1-indexed)",
                    details={field_name: value},
                )
            return value

        if isinstance(value, float):
            if value.is_integer():
                return self._coerce_line_endpoint(int(value), field_name)
            raise ValidationError(
                "Line range boundaries must be whole numbers",
                details={field_name: value},
            )

        if isinstance(value, str):
            stripped = value.strip()
            if not stripped:
                return None
            try:
                parsed = int(stripped)
            except ValueError as exc:
                raise ValidationError(
                    "Line range boundaries must be integers",
                    details={field_name: value},
                ) from exc
            return self._coerce_line_endpoint(parsed, field_name)

        raise ValidationError(
            "Unsupported line range boundary type",
            details={field_name: value, "type": type(value).__name__},
        )

    def _validate_line_range(
        self, start: int | None, end: int | None, raw_value: Any
    ) -> tuple[int | None, int | None]:
        if start is not None and end is not None and end < start:
            raise ValidationError(
                "Line range end must be greater than or equal to start",
                details={"start": start, "end": end, "raw": raw_value},
            )
        return start, end

    def _parse_line_range(self, spec: Any) -> list[tuple[int | None, int | None]]:
        if spec is None:
            return []

        if isinstance(spec, tuple) and len(spec) == 2:
            start, end = spec
            start_val = self._coerce_line_endpoint(start, "start")
            end_val = self._coerce_line_endpoint(end, "end")
            return [self._validate_line_range(start_val, end_val, spec)]

        if isinstance(spec, list | set):
            ranges: list[tuple[int | None, int | None]] = []
            for item in spec:
                ranges.extend(self._parse_line_range(item))
            return ranges

        if isinstance(spec, dict):
            start = spec.get("start")
            if start is None:
                start = spec.get("from")
            end = spec.get("end")
            if end is None:
                end = spec.get("to")
            start_val = self._coerce_line_endpoint(start, "start")
            end_val = self._coerce_line_endpoint(end, "end")
            return [self._validate_line_range(start_val, end_val, spec)]

        if isinstance(spec, bool):
            raise ValidationError(
                "Line range specification cannot be a boolean",
                details={"value": spec},
            )

        if isinstance(spec, int | float):
            start_val = self._coerce_line_endpoint(spec, "start")
            return [self._validate_line_range(start_val, start_val, spec)]

        if isinstance(spec, str):
            value = spec.strip()
            if not value:
                return []
            if "," in value:
                ranges: list[tuple[int | None, int | None]] = []
                for part in value.split(","):
                    ranges.extend(self._parse_line_range(part))
                return ranges
            if ":" in value:
                start_str, end_str = value.split(":", 1)
            else:
                start_str, end_str = value, value
            start_val = self._coerce_line_endpoint(start_str, "start")
            end_val = self._coerce_line_endpoint(end_str, "end")
            return [self._validate_line_range(start_val, end_val, spec)]

        raise ValidationError(
            "Unsupported line range specification",
            details={"value": spec, "type": type(spec).__name__},
        )

    def normalize_line_ranges(self, lines: Any) -> list[tuple[int | None, int | None]]:
        """Deduplicate ranges while preserving order."""
        if lines is None:
            return []

        ranges = self._parse_line_range(lines)
        seen: set[tuple[int | None, int | None]] = set()
        normalized: list[tuple[int | None, int | None]] = []
        for start, end in ranges:
            key = (start, end)
            if key in seen:
                continue
            seen.add(key)
            normalized.append(key)
        return normalized

    def extract_lines_from_content(
        self, content: str, ranges: Sequence[tuple[int | None, int | None]]
    ) -> tuple[str, list[dict[str, int | None]], int]:
        lines = content.splitlines(keepends=True)
        total_lines = len(lines)

        if not ranges:
            return content, [], total_lines

        segments: list[str] = []
        metadata: list[dict[str, int | None]] = []

        for start, end in ranges:
            requested_start = 1 if start is None else start
            requested_end = end if end is not None else total_lines

            start_index = max((requested_start or 1) - 1, 0)
            end_bound = total_lines if end is None else max(min(end, total_lines), 0)

            if end_bound < start_index:
                end_bound = start_index

            segment_lines = lines[start_index:end_bound]
            segments.append("".join(segment_lines))

            resolved_start = start_index + 1 if segment_lines else None
            resolved_end = end_bound if segment_lines else None

            metadata.append(
                {
                    "start": start,
                    "end": end,
                    "resolved_start": resolved_start,
                    "resolved_end": resolved_end,
                }
            )

        return "".join(segments), metadata, total_lines

    @staticmethod
    def _split_key_path(key_path: str) -> list[str]:
        return [segment for segment in key_path.split(".") if segment]

    def _get_nested_value(self, data: Any, path: list[str]) -> Any:
        current = data
        for segment in path:
            if isinstance(current, dict):
                if segment not in current:
                    return None
                current = current[segment]
            else:
                return None
        return current

    def extract_data_by_keys(self, data: Any, keys: list[str]) -> Any:
        if not keys:
            return data

        if isinstance(data, str):
            try:
                data = json.loads(data) if data else {}
            except json.JSONDecodeError:
                return data

        if not isinstance(data, dict):
            return data

        results = {}
        for key_path in keys:
            path_segments = self._split_key_path(key_path)
            results[key_path] = self._get_nested_value(data, path_segments)

        if len(results) == 1:
            return next(iter(results.values()))
        return results

    def _set_nested_value(self, data: dict[str, Any], path: list[str], value: Any) -> None:
        current: dict[str, Any] = data
        for segment in path[:-1]:
            next_value = current.get(segment)
            if not isinstance(next_value, dict):
                next_value = {}
                current[segment] = next_value
            current = next_value
        current[path[-1]] = value

    def update_data_by_keys(
        self, existing_data: Any, value: Any, keys: list[str]
    ) -> dict[str, Any]:
        normalized_keys = self.normalize_keys(keys)
        if not normalized_keys:
            raise ValidationError(
                "Update operation requires at least one key",
                details={"keys": keys},
            )

        if isinstance(existing_data, str):
            try:
                existing_data = json.loads(existing_data) if existing_data else {}
            except json.JSONDecodeError as exc:
                raise ValidationError(
                    "Existing content is not valid JSON",
                    details={"error": str(exc)},
                ) from exc

        if existing_data is None:
            working_data: dict[str, Any] = {}
        elif isinstance(existing_data, dict):
            working_data = dict(existing_data)
        else:
            raise ValidationError(
                "Existing content must be a JSON object to update keys",
                details={"type": type(existing_data).__name__},
            )

        if len(normalized_keys) == 1:
            values_map = {normalized_keys[0]: value}
        else:
            if not isinstance(value, dict):
                raise ValidationError(
                    "Updating multiple keys requires a mapping of values",
                    details={"type": type(value).__name__},
                )
            values_map: dict[str, Any] = {}
            for key_path in normalized_keys:
                if key_path in value:
                    values_map[key_path] = value[key_path]
                else:
                    last_segment = key_path.split(".")[-1]
                    if last_segment in value:
                        values_map[key_path] = value[last_segment]
                    else:
                        raise ValidationError(
                            f"Value for key '{key_path}' not provided",
                            details={"keys": normalized_keys},
                        )

        for key_path, mapped_value in values_map.items():
            path_segments = self._split_key_path(key_path)
            if not path_segments:
                raise ValidationError(
                    "Key paths cannot be empty",
                    details={"key": key_path},
                )
            self._set_nested_value(working_data, path_segments, mapped_value)

        return working_data

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

    def prepare_read_response(
        self,
        data: Any,
        file_path: str,
        size: int,
        keys: list[str] | None = None,
        line_ranges: list[dict[str, int | None]] | None = None,
        total_lines: int | None = None,
    ) -> dict[str, Any]:
        metadata = {
            "operation": "read",
            "file_path": file_path,
            "size": size,
            "keys": keys or [],
        }
        if line_ranges is not None:
            metadata["line_ranges"] = line_ranges
            metadata["partial_content"] = True
        if total_lines is not None:
            metadata["total_lines"] = total_lines

        return {"value": data, "metadata": metadata}

    def prepare_write_response(
        self, data: Any, file_path: str, size: int, keys: list[str] | None = None
    ) -> dict[str, Any]:
        return {
            "value": data,
            "metadata": {
                "operation": "write",
                "file_path": file_path,
                "size": size,
                "keys": keys or [],
            },
        }

    def prepare_update_response(
        self, data: Any, file_path: str, size: int, keys: list[str]
    ) -> dict[str, Any]:
        return {
            "value": data,
            "metadata": {
                "operation": "update",
                "file_path": file_path,
                "size": size,
                "keys": keys,
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
