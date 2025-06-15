"""
Validation utilities for executor operations.
Contains all validation logic extracted from utils.py.
"""
from typing import Dict, Any, List, Optional, Tuple, TYPE_CHECKING
import json
from dataclasses import dataclass, field

if TYPE_CHECKING:
    from ..execution_engine import Ctx as ExecutionContext


@dataclass
class ValidationResult:
    """Result of node validation"""
    is_valid: bool
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)


def validate_required_properties(
    node: Dict[str, Any], 
    required_props: List[str]
) -> ValidationResult:
    """
    Validate that required properties exist in the node.
    
    Args:
        node: The node to validate
        required_props: List of required property names
        
    Returns:
        ValidationResult
    """
    errors = []
    properties = node.get("properties", {})
    
    for prop in required_props:
        if prop not in properties or properties[prop] is None:
            errors.append(f"Required property '{prop}' is missing")
    
    return ValidationResult(
        is_valid=len(errors) == 0,
        errors=errors
    )


def validate_property_types(
    node: Dict[str, Any],
    type_specs: Dict[str, type]
) -> ValidationResult:
    """
    Validate property types match expected types.
    
    Args:
        node: The node to validate
        type_specs: Dictionary mapping property names to expected types
        
    Returns:
        ValidationResult
    """
    errors = []
    warnings = []
    properties = node.get("properties", {})
    
    for prop_name, expected_type in type_specs.items():
        if prop_name in properties:
            value = properties[prop_name]
            if value is not None and not isinstance(value, expected_type):
                # Try type coercion for common cases
                if expected_type == int and isinstance(value, str):
                    try:
                        int(value)
                        warnings.append(f"Property '{prop_name}' will be converted from string to int")
                    except ValueError:
                        errors.append(f"Property '{prop_name}' must be of type {expected_type.__name__}")
                elif expected_type == float and isinstance(value, (int, str)):
                    try:
                        float(value)
                        warnings.append(f"Property '{prop_name}' will be converted to float")
                    except ValueError:
                        errors.append(f"Property '{prop_name}' must be of type {expected_type.__name__}")
                else:
                    errors.append(f"Property '{prop_name}' must be of type {expected_type.__name__}")
    
    return ValidationResult(
        is_valid=len(errors) == 0,
        errors=errors,
        warnings=warnings
    )


async def check_api_keys(required_keys: List[str], context: 'ExecutionContext') -> ValidationResult:
    """
    Check if required API keys are available.
    
    Args:
        required_keys: List of required API key names
        context: Execution context
        
    Returns:
        ValidationResult
    """
    errors = []
    
    # Check API keys from context or environment
    api_keys = context.api_keys if hasattr(context, 'api_keys') else {}
    
    for key_name in required_keys:
        if key_name not in api_keys or not api_keys[key_name]:
            errors.append(f"Missing required API key: {key_name}")
    
    return ValidationResult(
        is_valid=len(errors) == 0,
        errors=errors
    )


def validate_required_fields(
    properties: Dict[str, Any],
    required_fields: List[str],
    field_descriptions: Optional[Dict[str, str]] = None
) -> List[str]:
    """
    Validate that required fields exist and are non-empty.
    
    Args:
        properties: Node properties to validate
        required_fields: List of required field names
        field_descriptions: Optional mapping of field names to descriptions
        
    Returns:
        List of error messages
    """
    errors = []
    for field in required_fields:
        value = properties.get(field)
        if value is None or (isinstance(value, str) and not value.strip()):
            desc = field_descriptions.get(field, field) if field_descriptions else field
            errors.append(f"{desc} is required")
    return errors


def validate_enum_field(
    properties: Dict[str, Any],
    field_name: str,
    allowed_values: List[str],
    case_sensitive: bool = True
) -> Optional[str]:
    """
    Validate that a field contains one of the allowed values.
    
    Args:
        properties: Node properties
        field_name: Name of the field to validate
        allowed_values: List of allowed values
        case_sensitive: Whether to perform case-sensitive comparison
        
    Returns:
        Error message if invalid, None if valid
    """
    value = properties.get(field_name)
    if value is None:
        return None
    
    check_value = value if case_sensitive else value.lower()
    check_allowed = allowed_values if case_sensitive else [v.lower() for v in allowed_values]
    
    if check_value not in check_allowed:
        return f"Invalid {field_name}: '{value}'. Allowed values: {', '.join(allowed_values)}"
    return None


def validate_positive_integer(
    properties: Dict[str, Any],
    field_name: str,
    min_value: int = 1,
    required: bool = False
) -> Optional[str]:
    """
    Validate that a field is a positive integer.
    
    Args:
        properties: Node properties
        field_name: Name of the field to validate
        min_value: Minimum allowed value (default 1)
        required: Whether the field is required
        
    Returns:
        Error message if invalid, None if valid
    """
    value = properties.get(field_name)
    
    if value is None:
        return f"{field_name} is required" if required else None
    
    if not isinstance(value, int) or value < min_value:
        return f"{field_name} must be a positive integer >= {min_value}"
    
    return None


def validate_file_path(
    path: str,
    field_name: str = "File path",
    allow_empty: bool = False
) -> List[str]:
    """
    Validate file path for security issues.
    
    Args:
        path: File path to validate
        field_name: Name of the field for error messages
        allow_empty: Whether empty paths are allowed
        
    Returns:
        List of error messages
    """
    errors = []
    
    if not path and not allow_empty:
        errors.append(f"{field_name} is required")
    elif path:
        # Check for directory traversal
        if any(pattern in path for pattern in ["../", "..\\"]):
            errors.append(f"{field_name} cannot contain directory traversal sequences")
    
    return errors


def validate_either_required(
    properties: Dict[str, Any],
    field_groups: List[List[str]],
    group_descriptions: Optional[List[str]] = None
) -> List[str]:
    """
    Validate that at least one field from each group is provided.
    
    Args:
        properties: Node properties
        field_groups: List of field groups, where at least one field per group is required
        group_descriptions: Optional descriptions for each group
        
    Returns:
        List of error messages
    """
    errors = []
    
    for i, group in enumerate(field_groups):
        has_value = any(
            properties.get(field) and 
            (not isinstance(properties.get(field), str) or properties.get(field).strip())
            for field in group
        )
        
        if not has_value:
            if group_descriptions and i < len(group_descriptions):
                errors.append(group_descriptions[i])
            else:
                errors.append(f"Either {' or '.join(group)} is required")
    
    return errors


def validate_json_field(
    properties: Dict[str, Any],
    field_name: str,
    required: bool = False
) -> Tuple[Optional[Dict], Optional[str]]:
    """
    Validate and parse a JSON field.
    
    Args:
        properties: Node properties
        field_name: Name of the field containing JSON
        required: Whether the field is required
        
    Returns:
        Tuple of (parsed_json, error_message)
    """
    value = properties.get(field_name)
    
    if not value:
        if required:
            return None, f"{field_name} is required"
        return None, None
    
    try:
        if isinstance(value, str):
            parsed = json.loads(value)
        else:
            parsed = value
        return parsed, None
    except json.JSONDecodeError as e:
        return None, f"Invalid JSON in {field_name}: {str(e)}"


def validate_numeric_range(
    properties: Dict[str, Any],
    field_name: str,
    min_value: Optional[float] = None,
    max_value: Optional[float] = None,
    required: bool = False,
    allow_int: bool = True,
    allow_float: bool = True
) -> Optional[str]:
    """
    Validate that a field is a number within a specified range.
    
    Args:
        properties: Node properties
        field_name: Name of the field to validate
        min_value: Minimum allowed value (inclusive)
        max_value: Maximum allowed value (inclusive)
        required: Whether the field is required
        allow_int: Whether integer values are allowed
        allow_float: Whether float values are allowed
        
    Returns:
        Error message if invalid, None if valid
    """
    value = properties.get(field_name)
    
    if value is None:
        return f"{field_name} is required" if required else None
    
    # Type checking
    if allow_int and allow_float:
        if not isinstance(value, (int, float)):
            return f"{field_name} must be a number"
    elif allow_int and not allow_float:
        if not isinstance(value, int):
            return f"{field_name} must be an integer"
    elif allow_float and not allow_int:
        if not isinstance(value, float):
            return f"{field_name} must be a float"
    
    # Range checking
    if min_value is not None and value < min_value:
        return f"{field_name} must be at least {min_value}"
    if max_value is not None and value > max_value:
        return f"{field_name} cannot exceed {max_value}"
    
    return None


def validate_dangerous_code(
    code: str,
    language: str,
    strict: bool = True
) -> Tuple[List[str], List[str]]:
    """
    Check code for dangerous patterns.
    
    Args:
        code: Code to validate
        language: Programming language
        strict: Whether to return errors (True) or warnings (False) for dangerous patterns
        
    Returns:
        Tuple of (errors, warnings)
    """
    errors = []
    warnings = []
    
    dangerous_patterns = {
        "python": {
            "high_risk": ["import os", "import subprocess", "__import__", "compile(", "globals("],
            "medium_risk": ["exec(", "eval(", "open(", "file("]
        },
        "javascript": {
            "high_risk": ["require('fs')", "require('child_process')", "eval("],
            "medium_risk": ["Function(", "setTimeout(", "setInterval("]
        },
        "bash": {
            "high_risk": ["rm -rf", "sudo", "> /dev/", "dd if=", "mkfs", ":(){ :|:& };:"],
            "medium_risk": ["curl", "wget", "nc"]
        }
    }
    
    patterns = dangerous_patterns.get(language, {})
    
    for pattern in patterns.get("high_risk", []):
        if pattern in code:
            msg = f"Code contains dangerous operation: {pattern}"
            if strict:
                errors.append(msg)
            else:
                warnings.append(msg)
    
    for pattern in patterns.get("medium_risk", []):
        if pattern in code:
            warnings.append(f"Code contains potentially dangerous operation: {pattern}")
    
    return errors, warnings


def merge_validation_results(*results: ValidationResult) -> ValidationResult:
    """
    Merge multiple validation results into one.
    
    Args:
        *results: Variable number of ValidationResult objects
        
    Returns:
        Merged ValidationResult
    """
    all_errors = []
    all_warnings = []
    
    for result in results:
        all_errors.extend(result.errors)
        all_warnings.extend(result.warnings)
    
    return ValidationResult(
        is_valid=len(all_errors) == 0,
        errors=all_errors,
        warnings=all_warnings
    )