"""Base schemas for all node types."""

from pydantic import BaseModel, Field
from typing import Optional, Dict, Any


class BaseNodeProps(BaseModel):
    """Base properties shared by all node types."""
    
    label: Optional[str] = Field(None, description="Human-readable label for the node")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")
    
    class Config:
        """Pydantic configuration."""
        extra = "forbid"  # Disallow extra fields
        validate_assignment = True  # Validate on assignment