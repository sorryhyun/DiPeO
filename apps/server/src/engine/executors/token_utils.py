from dataclasses import dataclass, asdict
from typing import Any, Dict


@dataclass
class TokenUsage:
    """Encapsulates token usage metrics"""
    input: int = 0
    output: int = 0
    cached: int = 0
    
    @property
    def total(self) -> int:
        """Total tokens used (input + output)"""
        return self.input + self.output
    
    def to_dict(self) -> Dict[str, int]:
        """Convert to dictionary format"""
        return asdict(self)

    @classmethod
    def from_response(cls, response: dict) -> 'TokenUsage':
        """Create TokenUsage from LLM response dict"""
        return cls(
            input=response.get("input_tokens", 0),
            output=response.get("output_tokens", 0),
            cached=response.get("cached_tokens", 0)
        )

    @classmethod
    def from_usage(cls, usage: Any, service: str = None) -> 'TokenUsage':
        """Create from provider-specific usage object"""
        if not usage:
            return cls()

        # Handle different provider formats
        if service == "gemini" and isinstance(usage, (list, tuple)):
            return cls(
                input=usage[0] if len(usage) > 0 else 0,
                output=usage[1] if len(usage) > 1 else 0
            )

        # Standard format
        return cls(
            input=(getattr(usage, 'input_tokens', None) or
                   getattr(usage, 'prompt_tokens', None) or 0),
            output=(getattr(usage, 'output_tokens', None) or
                    getattr(usage, 'completion_tokens', None) or 0),
            cached=getattr(usage, 'cached_tokens', 0)
        )
