"""Simplified validation helpers using Pydantic."""

from typing import Any, Dict, List, Optional, TypeVar, Type
from pydantic import BaseModel, ValidationError, validator, Field
import re

T = TypeVar('T', bound=BaseModel)


def validate_with_schema(
    schema: Type[T], 
    data: Dict[str, Any],
    allow_extra: bool = True
) -> tuple[Optional[T], Optional[List[str]]]:
    """
    Validate data using a Pydantic schema.
    
    Returns:
        Tuple of (validated_model, error_messages)
    """
    try:
        if allow_extra:
            # Create a dynamic model that allows extra fields
            schema = type(
                f"{schema.__name__}WithExtra",
                (schema,),
                {"__annotations__": {**schema.__annotations__}, "class Config": type("Config", (), {"extra": "allow"})}
            )
        
        model = schema(**data)
        return model, None
    except ValidationError as e:
        errors = []
        for err in e.errors():
            field_path = ".".join(str(loc) for loc in err["loc"])
            errors.append(f"{field_path}: {err['msg']}")
        return None, errors


class PathValidator:
    """Validator for file paths."""
    
    @staticmethod
    def validate(path: str) -> Optional[str]:
        """Validate a file path for security issues."""
        if not path:
            return "Path cannot be empty"
        
        # Check for directory traversal
        if ".." in path or path.startswith("/"):
            return "Path cannot contain '..' or start with '/'"
        
        # Check for suspicious patterns
        dangerous_patterns = [
            r"\.\.[\\/]",  # Directory traversal
            r"^\s*[\\/]",  # Absolute paths
            r"[<>:|?*]",   # Invalid characters for most filesystems
        ]
        
        for pattern in dangerous_patterns:
            if re.search(pattern, path):
                return f"Path contains invalid pattern: {pattern}"
        
        return None


class CodeValidator:
    """Validator for code safety."""
    
    DANGEROUS_PATTERNS = {
        "python": {
            "import os", "import subprocess", "__import__", 
            "compile(", "exec(", "eval("
        },
        "javascript": {
            "require('fs')", "require('child_process')", 
            "eval(", "Function("
        },
        "bash": {
            "rm -rf", "sudo", "> /dev/", "dd if=", 
            "mkfs", ":(){ :|:& };:"
        }
    }
    
    @classmethod
    def validate(
        cls, 
        code: str, 
        language: str,
        strict: bool = True
    ) -> Optional[str]:
        """Validate code for dangerous patterns."""
        patterns = cls.DANGEROUS_PATTERNS.get(language, set())
        
        for pattern in patterns:
            if pattern in code:
                if strict:
                    return f"Code contains dangerous operation: {pattern}"
        
        return None


def create_validation_mixin(validators: Dict[str, Any]) -> type:
    """
    Create a mixin class with custom validators.
    
    Example:
        validators = {
            'path': lambda v: PathValidator.validate(v),
            'code': lambda v, values: CodeValidator.validate(v, values.get('language', 'python'))
        }
        
        class MySchema(BaseModel, create_validation_mixin(validators)):
            path: str
            code: str
            language: str
    """
    methods = {}
    
    for field_name, validator_func in validators.items():
        def make_validator(fname, func):
            def validator_method(cls, v, values=None):
                if values is None:
                    error = func(v)
                else:
                    error = func(v, values)
                
                if error:
                    raise ValueError(error)
                return v
            
            # Use validator decorator from pydantic
            return validator(fname, allow_reuse=True)(validator_method)
        
        method_name = f"validate_{field_name}"
        methods[method_name] = make_validator(field_name, validator_func)
    
    return type("ValidationMixin", (), methods)