"""
Endpoint node schema - terminal nodes with optional file saving
"""

from typing import Optional

from pydantic import Field, field_validator

from .base import BaseNodeProps


class EndpointNodeProps(BaseNodeProps):
    """Properties for Endpoint node"""

    saveToFile: bool = Field(False, description="Whether to save output to a file")
    filePath: Optional[str] = Field(None, description="Path to save the file")
    fileFormat: str = Field("text", description="Format for saving the file")
    contentFormat: Optional[str] = Field(
        None,
        description="Custom format for content output (with variable substitution)",
    )

    @field_validator("filePath")
    @classmethod
    def validate_file_path(cls, v, info):
        """Validate file path when saveToFile is True"""
        values = info.data
        if values.get("saveToFile") and not v:
            raise ValueError("File path is required when saveToFile is True")

        # Basic security validation
        if v and (".." in v):
            raise ValueError("File path cannot contain directory traversal sequences")

        return v
