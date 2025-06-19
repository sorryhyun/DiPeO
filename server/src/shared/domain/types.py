"""
Shared domain type aliases and base models.
These types are used throughout the system to ensure consistency.
"""
from typing import Optional, Dict, Any, NewType
from pydantic import BaseModel, Field
from datetime import datetime

# Import type aliases from generated models
from src.__generated__.models import (
    NodeID,
    ArrowID,
    HandleID,
    PersonID,
    ApiKeyID,
    DiagramID,
    ExecutionID,
    Vec2,
)

# Import the consolidated TokenUsage implementation
from .token_usage import TokenUsage


class TimestampedModel(BaseModel):
    """Base model for entities with timestamps."""
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None
    
    def update_timestamp(self):
        """Update the updated_at timestamp."""
        self.updated_at = datetime.utcnow()