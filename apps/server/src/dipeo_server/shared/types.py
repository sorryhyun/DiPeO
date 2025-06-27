"""
Shared domain type aliases and base models.
These types are used throughout the system to ensure consistency.
"""

from datetime import datetime

from pydantic import BaseModel, Field

# Import type aliases from generated models


class TimestampedModel(BaseModel):
    """Base model for entities with timestamps."""

    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime | None = None

    def update_timestamp(self):
        """Update the updated_at timestamp."""
        self.updated_at = datetime.utcnow()
