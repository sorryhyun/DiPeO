"""
Shared domain type aliases and base models.
These types are used throughout the system to ensure consistency.
"""
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime

# Type aliases for domain identifiers
NodeID = str
ArrowID = str
HandleID = str
PersonID = str
ApiKeyID = str
DiagramID = str
ExecutionID = str


class Vec2(BaseModel):
    """2D position vector used for node positioning."""
    x: float
    y: float


class TokenUsage(BaseModel):
    """Token usage tracking for LLM services."""
    model_config = {"extra": "forbid"}
    
    prompt_tokens: int = Field(0, description="Number of tokens in the prompt")
    completion_tokens: int = Field(0, description="Number of tokens in the completion")
    total_tokens: int = Field(0, description="Total number of tokens used")
    
    @classmethod
    def zero(cls) -> 'TokenUsage':
        """Create a zero token usage instance."""
        return cls(prompt_tokens=0, completion_tokens=0, total_tokens=0)
    
    def __add__(self, other: 'TokenUsage') -> 'TokenUsage':
        """Add two token usage instances."""
        if not isinstance(other, TokenUsage):
            return NotImplemented
        return TokenUsage(
            prompt_tokens=self.prompt_tokens + other.prompt_tokens,
            completion_tokens=self.completion_tokens + other.completion_tokens,
            total_tokens=self.total_tokens + other.total_tokens
        )
    
    def __iadd__(self, other: 'TokenUsage') -> 'TokenUsage':
        """In-place addition of token usage."""
        if not isinstance(other, TokenUsage):
            return NotImplemented
        self.prompt_tokens += other.prompt_tokens
        self.completion_tokens += other.completion_tokens
        self.total_tokens += other.total_tokens
        return self
    
    def to_dict(self) -> Dict[str, int]:
        """Convert to dictionary format."""
        return {
            "prompt_tokens": self.prompt_tokens,
            "completion_tokens": self.completion_tokens,
            "total_tokens": self.total_tokens
        }


class TimestampedModel(BaseModel):
    """Base model for entities with timestamps."""
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None
    
    def update_timestamp(self):
        """Update the updated_at timestamp."""
        self.updated_at = datetime.utcnow()