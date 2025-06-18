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
    Vec2,
    TokenUsage as GeneratedTokenUsage,
)

# ExecutionID is not in generated models yet
ExecutionID = NewType('ExecutionID', str)

# Extended TokenUsage with additional methods
class TokenUsage(GeneratedTokenUsage):
    """Token usage tracking for LLM services with additional utility methods."""
    
    @classmethod
    def zero(cls) -> 'TokenUsage':
        """Create a zero token usage instance."""
        return cls(input=0, output=0, cached=0)
    
    def __add__(self, other: 'TokenUsage') -> 'TokenUsage':
        """Add two token usage instances."""
        if not isinstance(other, (TokenUsage, GeneratedTokenUsage)):
            return NotImplemented
        return TokenUsage(
            input=self.input + other.input,
            output=self.output + other.output,
            cached=(self.cached or 0) + (other.cached or 0)
        )
    
    def __iadd__(self, other: 'TokenUsage') -> 'TokenUsage':
        """In-place addition of token usage."""
        if not isinstance(other, (TokenUsage, GeneratedTokenUsage)):
            return NotImplemented
        self.input += other.input
        self.output += other.output
        self.cached = (self.cached or 0) + (other.cached or 0)
        return self
    
    def to_dict(self) -> Dict[str, int]:
        """Convert to dictionary format."""
        return {
            "input": self.input,
            "output": self.output,
            "cached": self.cached or 0,
            "total": self.total or (self.input + self.output)
        }


class TimestampedModel(BaseModel):
    """Base model for entities with timestamps."""
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None
    
    def update_timestamp(self):
        """Update the updated_at timestamp."""
        self.updated_at = datetime.utcnow()