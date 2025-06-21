"""
Job node schema - defines properties for code execution nodes
"""

from pydantic import Field, field_validator
from dipeo_domain import SupportedLanguage
from ..validation_helpers import CodeValidator
from .base import BaseNodeProps



class JobNodeProps(BaseNodeProps):
    """Properties for Job node that executes code in various languages"""
    
    code: str = Field(
        ...,
        min_length=1,
        description="Code to execute"
    )
    
    language: SupportedLanguage = Field(
        SupportedLanguage.python,
        description="Programming language for code execution"
    )
    
    timeout: int = Field(
        30,
        ge=1,
        le=300,
        description="Execution timeout in seconds (1-300)"
    )
    
    @field_validator('code')
    @classmethod
    def validate_code_not_empty(cls, v: str) -> str:
        """Ensure code is not just whitespace"""
        if not v.strip():
            raise ValueError("Code cannot be empty or only whitespace")
        return v
    
    @field_validator('code')
    @classmethod
    def validate_code_safety(cls, v: str, info) -> str:
        """Validate code for dangerous patterns using simplified validator"""
        language = info.data.get('language', SupportedLanguage.python)
        
        # Use the simplified CodeValidator
        error = CodeValidator.validate(v, language.value, strict=True)
        if error:
            raise ValueError(error)
        
        return v
    
    class Config:
        use_enum_values = True
        json_schema_extra = {
            "example": {
                "code": "result = sum(inputs.get('numbers', []))",
                "language": "python",
                "timeout": 30
            }
        }