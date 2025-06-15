"""
UserResponse node schema - interactive user input
"""

from pydantic import BaseModel, Field, field_validator
from typing import Optional

from .base import BaseNodeProps


class UserResponseNodeProps(BaseNodeProps):
    """Properties for UserResponse node"""
    prompt: str = Field(..., description="Prompt to display to the user")
    timeout: Optional[float] = Field(
        10,
        ge=1,
        le=60,
        description="Timeout in seconds for user response"
    )