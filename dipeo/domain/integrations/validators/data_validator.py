"""Data validation service for database and data operations."""

from typing import Any

from dipeo.domain.base.exceptions import ValidationError
from dipeo.domain.base.validator import BaseValidator, ValidationResult, ValidationWarning, Severity


class DataValidator(BaseValidator):
    """Validates data operations including database operations."""
    
    ALLOWED_DB_OPERATIONS = ["prompt", "read", "write", "append"]
    
    def _perform_validation(self, target: Any, result: ValidationResult) -> None:
        """Perform data validation."""
        if isinstance(target, dict):
            # Check if it's a database operation
            if 'operation' in target:
                self._validate_db_operation(target, result)
            # Check if it's data to be stored
            elif 'data' in target:
                self._validate_data_content(target, result)
            else:
                self._validate_generic_data(target, result)
        elif isinstance(target, (list, tuple)):
            self._validate_data_collection(target, result)
        elif isinstance(target, str):
            self._validate_string_data(target, result)
        else:
            # For primitive types, just do basic validation
            self._validate_primitive_data(target, result)
    
    def _validate_db_operation(self, config: dict[str, Any], result: ValidationResult) -> None:
        """Validate database operation configuration."""
        operation = config.get('operation')
        
        if not operation:
            result.add_error(ValidationError("Database operation is required"))
            return
        
        if operation not in self.ALLOWED_DB_OPERATIONS:
            result.add_error(ValidationError(
                f"Invalid database operation: {operation}",
                details={"allowed_operations": self.ALLOWED_DB_OPERATIONS}
            ))
        
        # Validate operation-specific requirements
        value = config.get('value')
        
        if operation in ["write", "append"]:
            if value is None:
                result.add_error(ValidationError(
                    f"Operation '{operation}' requires a value",
                    details={"operation": operation}
                ))
            elif value == "":
                result.add_warning(ValidationWarning(
                    f"Operation '{operation}' has empty value",
                    field_name="value"
                ))
        
        # Validate database/collection name if present
        db_name = config.get('database') or config.get('collection')
        if db_name:
            self._validate_db_name(db_name, result)
        
        # Validate key if present
        if 'key' in config:
            self._validate_db_key(config['key'], result)
    
    def _validate_data_content(self, data_dict: dict[str, Any], result: ValidationResult) -> None:
        """Validate data content for storage."""
        data = data_dict.get('data')
        
        if data is None:
            result.add_error(ValidationError("Data field is required"))
            return
        
        # Check data size (warn if large)
        try:
            import json
            data_size = len(json.dumps(data))
            if data_size > 1_000_000:  # 1MB
                result.add_warning(ValidationWarning(
                    f"Large data size: {data_size / 1_000_000:.2f}MB",
                    field_name="data"
                ))
        except Exception:
            # If we can't serialize, it might have issues
            result.add_warning(ValidationWarning(
                "Data may not be JSON serializable",
                field_name="data"
            ))
        
        # Check for sensitive data patterns
        self._check_sensitive_data(data, result)
    
    def _validate_generic_data(self, data: dict[str, Any], result: ValidationResult) -> None:
        """Validate generic data dictionary."""
        # Check for common issues
        if not data:
            result.add_warning(ValidationWarning("Empty data dictionary"))
        
        # Check for very large dictionaries
        if len(data) > 1000:
            result.add_warning(ValidationWarning(
                f"Very large dictionary with {len(data)} keys",
                field_name="data"
            ))
        
        # Check keys
        for key in data:
            if not isinstance(key, str):
                result.add_error(ValidationError(
                    f"Dictionary key must be string, found: {type(key).__name__}"
                ))
            elif not key:
                result.add_error(ValidationError("Empty string key in dictionary"))
    
    def _validate_data_collection(self, collection: list | tuple, result: ValidationResult) -> None:
        """Validate data collections (lists/tuples)."""
        if not collection:
            result.add_warning(ValidationWarning("Empty collection"))
        
        # Warn about very large collections
        if len(collection) > 10000:
            result.add_warning(ValidationWarning(
                f"Very large collection with {len(collection)} items",
                severity=Severity.WARNING
            ))
        
        # Check for mixed types
        types = set(type(item).__name__ for item in collection[:100])  # Sample first 100
        if len(types) > 3:
            result.add_warning(ValidationWarning(
                f"Collection contains many different types: {types}",
                field_name="collection"
            ))
    
    def _validate_string_data(self, data: str, result: ValidationResult) -> None:
        """Validate string data."""
        if not data:
            result.add_warning(ValidationWarning("Empty string data"))
        elif len(data) > 1_000_000:  # 1MB
            result.add_warning(ValidationWarning(
                f"Very large string: {len(data) / 1_000_000:.2f}MB",
                field_name="string_data"
            ))
        
        # Check for null bytes
        if '\0' in data:
            result.add_error(ValidationError("String contains null bytes"))
        
        # Check for potential issues
        if data.strip() != data:
            result.add_warning(ValidationWarning(
                "String has leading/trailing whitespace",
                field_name="string_data"
            ))
    
    def _validate_primitive_data(self, data: Any, result: ValidationResult) -> None:
        """Validate primitive data types."""
        # Check for None
        if data is None:
            result.add_warning(ValidationWarning("Data is None"))
        
        # Check numeric values
        elif isinstance(data, (int, float)):
            if isinstance(data, float):
                if data != data:  # NaN check
                    result.add_error(ValidationError("Float value is NaN"))
                elif data == float('inf') or data == float('-inf'):
                    result.add_warning(ValidationWarning("Float value is infinite"))
    
    def _validate_db_name(self, name: str, result: ValidationResult) -> None:
        """Validate database/collection name."""
        if not name:
            result.add_error(ValidationError("Database/collection name cannot be empty"))
            return
        
        # Check for invalid characters
        invalid_chars = ['/', '\\', '.', ' ', '"', '$']
        for char in invalid_chars:
            if char in name:
                result.add_error(ValidationError(
                    f"Database name contains invalid character: '{char}'",
                    details={"name": name}
                ))
        
        # Check length
        if len(name) > 64:
            result.add_warning(ValidationWarning(
                f"Database name is very long: {len(name)} characters",
                field_name="database"
            ))
    
    def _validate_db_key(self, key: str, result: ValidationResult) -> None:
        """Validate database key."""
        if not key:
            result.add_error(ValidationError("Database key cannot be empty"))
            return
        
        if not isinstance(key, str):
            result.add_error(ValidationError(
                f"Database key must be string, found: {type(key).__name__}"
            ))
            return
        
        # Check for problematic characters
        if '\0' in key:
            result.add_error(ValidationError("Database key contains null byte"))
        
        if key.startswith('$'):
            result.add_warning(ValidationWarning(
                "Database key starts with '$' which may have special meaning",
                field_name="key"
            ))
        
        # Check length
        if len(key) > 1024:
            result.add_warning(ValidationWarning(
                f"Database key is very long: {len(key)} characters",
                field_name="key"
            ))
    
    def _check_sensitive_data(self, data: Any, result: ValidationResult) -> None:
        """Check for potentially sensitive data patterns."""
        # Convert to string for pattern matching
        data_str = str(data).lower()
        
        # Common sensitive patterns
        sensitive_patterns = [
            ('password', 'password'),
            ('api_key', 'api key'),
            ('secret', 'secret'),
            ('token', 'token'),
            ('private_key', 'private key'),
            ('ssn', 'social security'),
            ('credit_card', 'credit card')
        ]
        
        for pattern, description in sensitive_patterns:
            if pattern in data_str:
                result.add_warning(ValidationWarning(
                    f"Data may contain sensitive information: {description}",
                    severity=Severity.WARNING,
                    details={"pattern": pattern}
                ))
    
    # Convenience methods for backward compatibility
    def validate_operation(self, operation: str, allowed_operations: list[str]) -> None:
        """Validate that an operation is allowed (raises exception)."""
        if operation not in allowed_operations:
            raise ValidationError(
                f"Operation '{operation}' is not allowed. Must be one of: {', '.join(allowed_operations)}",
                details={"operation": operation, "allowed": allowed_operations}
            )
    
    def validate_db_operation_input(self, operation: str, value: Any) -> None:
        """Validate input for database operations (raises exception)."""
        config = {'operation': operation, 'value': value}
        result = self.validate(config)
        
        if not result.is_valid:
            raise result.errors[0]