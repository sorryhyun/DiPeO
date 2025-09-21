"""Data validation service for database and data operations."""

from typing import Any

from dipeo.domain.base.exceptions import ValidationError
from dipeo.domain.base.validator import BaseValidator, Severity, ValidationResult, ValidationWarning
from dipeo.domain.integrations.db_services import DBOperationsDomainService


class DataValidator(BaseValidator):
    """Validates data operations including database operations."""

    ALLOWED_DB_OPERATIONS = ["prompt", "read", "write", "append", "update"]

    def _perform_validation(self, target: Any, result: ValidationResult) -> None:
        if isinstance(target, dict):
            if "operation" in target:
                self._validate_db_operation(target, result)
            elif "data" in target:
                self._validate_data_content(target, result)
            else:
                self._validate_generic_data(target, result)
        elif isinstance(target, list | tuple):
            self._validate_data_collection(target, result)
        elif isinstance(target, str):
            self._validate_string_data(target, result)
        else:
            self._validate_primitive_data(target, result)

    def _validate_db_operation(self, config: dict[str, Any], result: ValidationResult) -> None:
        operation = config.get("operation")

        if not operation:
            result.add_error(ValidationError("Database operation is required"))
            return

        if operation not in self.ALLOWED_DB_OPERATIONS:
            result.add_error(
                ValidationError(
                    f"Invalid database operation: {operation}",
                    details={"allowed_operations": self.ALLOWED_DB_OPERATIONS},
                )
            )

        value = config.get("value")

        if operation in ["write", "append"]:
            if value is None:
                result.add_error(
                    ValidationError(
                        f"Operation '{operation}' requires a value",
                        details={"operation": operation},
                    )
                )
            elif value == "":
                result.add_warning(
                    ValidationWarning(
                        f"Operation '{operation}' has empty value", field_name="value"
                    )
                )

        db_name = config.get("database") or config.get("collection")
        if db_name:
            self._validate_db_name(db_name, result)

        if "key" in config:
            self._validate_db_key(config["key"], result)

        if "keys" in config:
            self._validate_db_keys(config["keys"], result)

        if config.get("lines") is not None:
            self._validate_line_ranges(
                config["lines"], operation, result, config.get("keys")
            )

        if operation == "update" and not config.get("keys"):
            result.add_error(
                ValidationError(
                    "Update operation requires one or more keys",
                    details={"operation": operation},
                )
            )

    def _validate_data_content(self, data_dict: dict[str, Any], result: ValidationResult) -> None:
        data = data_dict.get("data")

        if data is None:
            result.add_error(ValidationError("Data field is required"))
            return

        try:
            import json

            data_size = len(json.dumps(data))
            if data_size > 1_000_000:  # 1MB
                result.add_warning(
                    ValidationWarning(
                        f"Large data size: {data_size / 1_000_000:.2f}MB", field_name="data"
                    )
                )
        except Exception:
            result.add_warning(
                ValidationWarning("Data may not be JSON serializable", field_name="data")
            )

        self._check_sensitive_data(data, result)

    def _validate_generic_data(self, data: dict[str, Any], result: ValidationResult) -> None:
        if not data:
            result.add_warning(ValidationWarning("Empty data dictionary"))

        if len(data) > 1000:
            result.add_warning(
                ValidationWarning(f"Very large dictionary with {len(data)} keys", field_name="data")
            )

        for key in data:
            if not isinstance(key, str):
                result.add_error(
                    ValidationError(f"Dictionary key must be string, found: {type(key).__name__}")
                )
            elif not key:
                result.add_error(ValidationError("Empty string key in dictionary"))

    def _validate_data_collection(self, collection: list | tuple, result: ValidationResult) -> None:
        if not collection:
            result.add_warning(ValidationWarning("Empty collection"))

        if len(collection) > 10000:
            result.add_warning(
                ValidationWarning(
                    f"Very large collection with {len(collection)} items", severity=Severity.WARNING
                )
            )

        types = set(type(item).__name__ for item in collection[:100])
        if len(types) > 3:
            result.add_warning(
                ValidationWarning(
                    f"Collection contains many different types: {types}", field_name="collection"
                )
            )

    def _validate_string_data(self, data: str, result: ValidationResult) -> None:
        if not data:
            result.add_warning(ValidationWarning("Empty string data"))
        elif len(data) > 1_000_000:
            result.add_warning(
                ValidationWarning(
                    f"Very large string: {len(data) / 1_000_000:.2f}MB", field_name="string_data"
                )
            )

        if "\0" in data:
            result.add_error(ValidationError("String contains null bytes"))

        if data.strip() != data:
            result.add_warning(
                ValidationWarning(
                    "String has leading/trailing whitespace", field_name="string_data"
                )
            )

    def _validate_primitive_data(self, data: Any, result: ValidationResult) -> None:
        if data is None:
            result.add_warning(ValidationWarning("Data is None"))

        elif isinstance(data, int | float) and isinstance(data, float):
            if data != data:
                result.add_error(ValidationError("Float value is NaN"))
            elif data == float("inf") or data == float("-inf"):
                result.add_warning(ValidationWarning("Float value is infinite"))

    def _validate_db_name(self, name: str, result: ValidationResult) -> None:
        if not name:
            result.add_error(ValidationError("Database/collection name cannot be empty"))
            return

        invalid_chars = ["/", "\\", ".", " ", '"', "$"]
        for char in invalid_chars:
            if char in name:
                result.add_error(
                    ValidationError(
                        f"Database name contains invalid character: '{char}'",
                        details={"name": name},
                    )
                )

        if len(name) > 64:
            result.add_warning(
                ValidationWarning(
                    f"Database name is very long: {len(name)} characters", field_name="database"
                )
            )

    def _validate_db_key(self, key: str, result: ValidationResult) -> None:
        if not key:
            result.add_error(ValidationError("Database key cannot be empty"))
            return

        if not isinstance(key, str):
            result.add_error(
                ValidationError(f"Database key must be string, found: {type(key).__name__}")
            )
            return

        if "\0" in key:
            result.add_error(ValidationError("Database key contains null byte"))

        if key.startswith("$"):
            result.add_warning(
                ValidationWarning(
                    "Database key starts with '$' which may have special meaning", field_name="key"
                )
            )

        if len(key) > 1024:
            result.add_warning(
                ValidationWarning(
                    f"Database key is very long: {len(key)} characters", field_name="key"
                )
            )

    def _validate_db_keys(self, keys: Any, result: ValidationResult) -> None:
        if keys is None:
            return

        if isinstance(keys, str):
            if not keys.strip():
                result.add_error(ValidationError("Keys string cannot be empty"))
            return

        if not isinstance(keys, (list, tuple)):
            result.add_error(
                ValidationError(
                    "Keys must be provided as a string or list of strings",
                    details={"type": type(keys).__name__},
                )
            )
            return

        for index, key in enumerate(keys):
            if not isinstance(key, str):
                result.add_error(
                    ValidationError(
                        "Each key must be a string",
                        details={"index": index, "type": type(key).__name__},
                    )
                )
                continue
            if not key.strip():
                result.add_error(
                    ValidationError(
                        "Key entries cannot be empty",
                        details={"index": index},
                    )
                )

    def _validate_line_ranges(
        self,
        lines: Any,
        operation: str,
        result: ValidationResult,
        keys: Any = None,
    ) -> None:
        if operation != "read":
            result.add_error(
                ValidationError(
                    "The 'lines' option is only supported for read operations",
                    details={"operation": operation},
                )
            )
            return

        if keys not in (None, "", []):
            result.add_error(
                ValidationError(
                    "Cannot combine 'keys' and 'lines' for database reads",
                    details={"keys": keys},
                )
            )
            return

        service = DBOperationsDomainService()
        try:
            normalized = service.normalize_line_ranges(lines)
        except ValidationError as exc:
            result.add_error(exc)
            return

        if not normalized:
            result.add_warning(
                ValidationWarning(
                    "Lines specification did not resolve to any ranges",
                    field_name="lines",
                )
            )

    def _check_sensitive_data(self, data: Any, result: ValidationResult) -> None:
        data_str = str(data).lower()

        sensitive_patterns = [
            ("password", "password"),
            ("api_key", "api key"),
            ("secret", "secret"),
            ("token", "token"),
            ("private_key", "private key"),
            ("ssn", "social security"),
            ("credit_card", "credit card"),
        ]

        for pattern, description in sensitive_patterns:
            if pattern in data_str:
                result.add_warning(
                    ValidationWarning(
                        f"Data may contain sensitive information: {description}",
                        severity=Severity.WARNING,
                        details={"pattern": pattern},
                    )
                )

    def validate_operation(self, operation: str, allowed_operations: list[str]) -> None:
        if operation not in allowed_operations:
            raise ValidationError(
                f"Operation '{operation}' is not allowed. Must be one of: {', '.join(allowed_operations)}",
                details={"operation": operation, "allowed": allowed_operations},
            )

    def validate_db_operation_input(
        self, operation: str, value: Any, keys: Any = None, lines: Any = None
    ) -> None:
        """Validate input for database operations (raises exception)."""
        config = {
            "operation": operation,
            "value": value,
            "keys": keys,
            "lines": lines,
        }
        result = self.validate(config)

        if not result.is_valid:
            raise result.errors[0]
