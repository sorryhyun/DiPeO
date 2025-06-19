"""
Consolidated TokenUsage implementation with all utility methods.
Single source of truth for TokenUsage extensions.
"""
from typing import Dict, Any, Optional
from src.__generated__.models import TokenUsage as GeneratedTokenUsage


class TokenUsage(GeneratedTokenUsage):
    """Extended TokenUsage with mathematical operations and provider-specific parsing."""
    
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
    
    def to_dict(self) -> Dict[str, float]:
        """Convert to dictionary format."""
        return {
            "input": self.input,
            "output": self.output,
            "cached": self.cached or 0,
            "total": self.total or (self.input + self.output)
        }
    
    @classmethod
    def from_response(cls, response: dict) -> 'TokenUsage':
        """Create TokenUsage from LLM response dict."""
        return cls(
            input=response.get("input_tokens", 0),
            output=response.get("output_tokens", 0),
            cached=response.get("cached_tokens", 0)
        )
    
    @classmethod
    def from_usage(cls, usage: Any, service: Optional[str] = None) -> 'TokenUsage':
        """Create from provider-specific usage object."""
        if not usage:
            return cls.zero()
        
        # Handle different provider formats
        if service == "gemini" and isinstance(usage, (list, tuple)):
            return cls(
                input=usage[0] if len(usage) > 0 else 0,
                output=usage[1] if len(usage) > 1 else 0
            )
        
        # Extract tokens based on format
        input_tokens = (getattr(usage, 'input_tokens', None) or
                        getattr(usage, 'prompt_tokens', None) or 0)
        output_tokens = (getattr(usage, 'output_tokens', None) or
                         getattr(usage, 'completion_tokens', None) or 0)
        cached_tokens = 0
        
        # Special handling for OpenAI cached tokens
        if service == "openai":
            # Try to get cached tokens from nested structure
            if hasattr(usage, 'input_tokens_details') and hasattr(usage.input_tokens_details, 'cached_tokens'):
                cached_tokens = usage.input_tokens_details.cached_tokens or 0
        else:
            cached_tokens = getattr(usage, 'cached_tokens', 0)
            
        return cls(
            input=input_tokens,
            output=output_tokens,
            cached=cached_tokens
        )