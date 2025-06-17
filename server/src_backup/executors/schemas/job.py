"""
Job node schema - defines properties for code execution nodes
"""

from pydantic import BaseModel, Field, field_validator
from typing import Optional, Literal, Dict, Any
from enum import Enum


class SupportedLanguage(str, Enum):
    """Supported programming languages for job execution"""
    PYTHON = "python"
    JAVASCRIPT = "javascript"
    BASH = "bash"


class JobNodeProps(BaseModel):
    """Properties for Job node that executes code in various languages"""
    
    code: str = Field(
        ...,
        min_length=1,
        description="Code to execute"
    )
    
    language: SupportedLanguage = Field(
        SupportedLanguage.PYTHON,
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
        """Basic validation for obviously dangerous patterns"""
        language = info.data.get('language', SupportedLanguage.PYTHON)
        
        # Define dangerous patterns per language
        dangerous_patterns = {
            SupportedLanguage.PYTHON: [
                ('import os', 'Direct OS imports are restricted'),
                ('import subprocess', 'Subprocess imports are restricted'),
                ('__import__', 'Dynamic imports are restricted'),
                ('eval(', 'eval() is restricted'),
                ('exec(', 'exec() is restricted'),
                ('open(', 'File operations are restricted'),
                ('compile(', 'compile() is restricted'),
            ],
            SupportedLanguage.JAVASCRIPT: [
                ('require(', 'require() is restricted'),
                ('import ', 'ES6 imports are restricted'),
                ('process.', 'Process access is restricted'),
                ('child_process', 'Child process operations are restricted'),
                ('fs.', 'File system access is restricted'),
                ('eval(', 'eval() is restricted'),
            ],
            SupportedLanguage.BASH: [
                ('rm -rf', 'Destructive commands are restricted'),
                ('sudo', 'Privileged operations are restricted'),
                ('chmod', 'Permission changes are restricted'),
                ('chown', 'Ownership changes are restricted'),
                ('mkfs', 'Filesystem operations are restricted'),
                ('dd ', 'Direct disk operations are restricted'),
                ('curl', 'Network operations are restricted'),
                ('wget', 'Network operations are restricted'),
            ]
        }
        
        # Check for dangerous patterns
        patterns = dangerous_patterns.get(language, [])
        for pattern, message in patterns:
            if pattern in v.lower():
                # For bash, we want to be stricter
                if language == SupportedLanguage.BASH:
                    raise ValueError(f"{message}: '{pattern}'")
                # For other languages, we'll handle this in the handler with warnings
                # but not block at schema level (except for the most dangerous ones)
                elif pattern in ['__import__', 'eval(', 'exec(', 'compile(']:
                    raise ValueError(f"{message}: '{pattern}'")
        
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