"""
DB node schema - defines properties for data source and file operation nodes
"""

from pydantic import BaseModel, Field, field_validator, model_validator
from typing import Optional
from enum import Enum
import json


class DBSubType(str, Enum):
    """Supported DB node subtypes"""
    FILE = "file"
    FIXED_PROMPT = "fixed_prompt"
    CODE = "code"
    API_TOOL = "api_tool"


class APIConfig(BaseModel):
    """Configuration for API tool subtype"""
    apiType: str = Field(..., description="Type of API (e.g., 'notion')")
    # Additional fields can be added based on API type
    
    class Config:
        extra = "allow"  # Allow additional fields for specific API configs


class DBNodeProps(BaseModel):
    """Properties for DB node that handles data sources and file operations"""
    
    subType: DBSubType = Field(
        DBSubType.FILE,
        description="Type of data source operation"
    )
    
    sourceDetails: str = Field(
        ...,
        min_length=1,
        description="Details specific to the subType (file path, prompt content, code, or API config JSON)"
    )
    
    @field_validator('sourceDetails')
    @classmethod
    def validate_source_details_not_empty(cls, v: str) -> str:
        """Ensure source details is not just whitespace or placeholder"""
        v = v.strip()
        if not v or v == "Enter your fixed prompt or content here":
            raise ValueError("Source details cannot be empty or contain placeholder text")
        return v
    
    @model_validator(mode='after')
    def validate_source_by_subtype(self) -> 'DBNodeProps':
        """Validate source details based on subType"""
        if self.subType == DBSubType.FILE:
            # Basic file path validation
            path = self.sourceDetails.strip()
            if not path:
                raise ValueError("File path is required for file subType")
            
            # Check for dangerous paths
            dangerous_patterns = ['../', '\\..\\', '/etc/', '/root/', '/home/', 'C:\\Windows', 'C:\\System']
            for pattern in dangerous_patterns:
                if pattern in path:
                    raise ValueError(f"File path contains potentially dangerous pattern: {pattern}")
            
        elif self.subType == DBSubType.API_TOOL:
            # Validate JSON format for API configuration
            try:
                api_config = json.loads(self.sourceDetails)
                if not isinstance(api_config, dict):
                    raise ValueError("API configuration must be a JSON object")
                if 'apiType' not in api_config:
                    raise ValueError("API configuration must include 'apiType'")
            except json.JSONDecodeError as e:
                raise ValueError(f"Invalid JSON for API configuration: {e}")
        
        elif self.subType == DBSubType.CODE:
            # Basic code validation
            code = self.sourceDetails.strip()
            if not code:
                raise ValueError("Code snippet cannot be empty")
            
            # Check for extremely dangerous patterns
            dangerous_patterns = [
                ('import os', 'Direct OS imports are restricted in DB code'),
                ('import subprocess', 'Subprocess imports are restricted in DB code'),
                ('__import__', 'Dynamic imports are restricted in DB code'),
                ('open(', 'File operations should use the file subType instead'),
            ]
            
            for pattern, message in dangerous_patterns:
                if pattern in code:
                    raise ValueError(f"{message}: '{pattern}'")
        
        return self
    
    def get_api_config(self) -> Optional[APIConfig]:
        """Parse and return API configuration if subType is api_tool"""
        if self.subType == DBSubType.API_TOOL:
            try:
                config_dict = json.loads(self.sourceDetails)
                return APIConfig(**config_dict)
            except (json.JSONDecodeError, TypeError, ValueError):
                return None
        return None
    
    class Config:
        use_enum_values = True
        json_schema_extra = {
            "examples": [
                {
                    "subType": "file",
                    "sourceDetails": "data/input.txt"
                },
                {
                    "subType": "fixed_prompt",
                    "sourceDetails": "This is a fixed prompt that will be returned as output"
                },
                {
                    "subType": "code",
                    "sourceDetails": "result = sum(inputs[0]) if inputs else 0"
                },
                {
                    "subType": "api_tool",
                    "sourceDetails": '{"apiType": "notion", "operation": "read_page"}'
                }
            ]
        }