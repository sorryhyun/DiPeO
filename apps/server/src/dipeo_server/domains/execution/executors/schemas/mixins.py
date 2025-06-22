"""Common mixins for node schemas to reduce duplication."""

from typing import Optional, Dict, Any, TypeVar, Generic
from pydantic import Field, field_validator, model_validator
import json
import re


class FilePathMixin:
    """Mixin for schemas that need file path validation."""
    
    @field_validator('filePath', 'file_path', check_fields=False)
    @classmethod
    def validate_file_path(cls, v: str) -> str:
        """Validate file paths for security."""
        if v and ('..' in v or v.startswith('/')):
            raise ValueError("File path cannot contain '..' or start with '/'")
        return v


class JSONFieldMixin:
    """Mixin for schemas with JSON string fields."""
    
    @staticmethod
    def validate_json_string(value: str, field_name: str) -> str:
        """Validate that a string contains valid JSON."""
        if value:
            try:
                json.loads(value)
            except json.JSONDecodeError as e:
                raise ValueError(f"{field_name} must be valid JSON: {e}")
        return value
    
    @staticmethod
    def parse_json_field(value: Optional[str], default: Any = None) -> Any:
        """Parse a JSON string field, returning default if empty."""
        if not value:
            return default
        try:
            return json.loads(value)
        except json.JSONDecodeError:
            return default


class CodeContentMixin:
    """Mixin for schemas with code or text content fields."""
    
    @field_validator('code', 'content', 'script', check_fields=False)
    @classmethod
    def validate_code_content(cls, v: str) -> str:
        """Validate code/content is not empty or placeholder."""
        if not v or not v.strip():
            raise ValueError("Code/content cannot be empty")
        
        # Check for common placeholder patterns
        placeholder_patterns = [
            r"^/\*.*\*/\s*$",  # /* comment only */
            r"^//.*$",         # // comment only
            r"^#.*$",          # # comment only
            r"^\s*$",          # whitespace only
        ]
        
        for pattern in placeholder_patterns:
            if re.match(pattern, v.strip(), re.MULTILINE | re.DOTALL):
                raise ValueError("Code/content cannot be just a comment or placeholder")
        
        return v


class TimeoutMixin:
    """Mixin for schemas that need timeout configuration."""
    
    timeout: int = Field(
        default=30,
        ge=1,
        le=300,
        description="Execution timeout in seconds"
    )


class TemplateValidationMixin:
    """Mixin for validating template syntax."""
    
    @staticmethod
    def validate_template_syntax(template: str, field_name: str = "template") -> str:
        """Validate template has balanced braces."""
        if template:
            open_count = template.count("{{")
            close_count = template.count("}}")
            if open_count != close_count:
                raise ValueError(
                    f"{field_name} has unbalanced template braces: "
                    f"{open_count} opening vs {close_count} closing"
                )
        return template


T = TypeVar('T')


class ConditionalRequiredFieldsMixin(Generic[T]):
    """Base mixin for conditional field validation."""
    
    @model_validator(mode='after')
    def validate_conditional_fields(self) -> T:
        """Override this method to implement conditional validation logic."""
        return self


class NodeSecurityMixin:
    """Mixin for common security validations."""
    
    @staticmethod
    def check_dangerous_patterns(value: str, field_name: str) -> None:
        """Check for potentially dangerous patterns in user input."""
        dangerous_patterns = [
            (r"import\s+os", "Direct OS imports are not allowed"),
            (r"import\s+subprocess", "Subprocess imports are not allowed"),
            (r"eval\s*\(", "eval() is not allowed"),
            (r"exec\s*\(", "exec() is not allowed"),
            (r"__import__", "__import__ is not allowed"),
        ]
        
        for pattern, message in dangerous_patterns:
            if re.search(pattern, value, re.IGNORECASE):
                raise ValueError(f"{field_name}: {message}")


class VariableSubstitutionMixin:
    """Mixin for schemas that support variable substitution."""
    
    @staticmethod
    def extract_variables(text: str) -> list[str]:
        """Extract variable names from {{variable}} patterns."""
        if not text:
            return []
        
        pattern = r'\{\{(\w+)\}\}'
        return list(set(re.findall(pattern, text)))
    
    @staticmethod
    def has_variables(text: str) -> bool:
        """Check if text contains any variable placeholders."""
        return bool(text and '{{' in text and '}}' in text)