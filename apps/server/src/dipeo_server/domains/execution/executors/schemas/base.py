"""Base schemas for all node types."""

from typing import Any, Dict, Optional

from pydantic import BaseModel, Field


class BaseNodeProps(BaseModel):
    """Base properties shared by all node types."""

    label: Optional[str] = Field(None, description="Human-readable label for the node")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")

    class Config:
        """Pydantic configuration."""

        extra = "forbid"  # Disallow extra fields
        validate_assignment = True  # Validate on assignment
