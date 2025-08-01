# Auto-generated Pydantic model for user_response node

from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field




class UserResponseNodeData(BaseModel):
    """Data model for User Response node."""
    prompt: str = Field(description="Question to ask the user")
    timeout: float = Field(description="Response timeout in seconds")

    class Config:
        extra = "forbid"
        validate_assignment = True