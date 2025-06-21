"""
Token usage utility service for LLM domain.
Handles provider-specific parsing and mathematical operations.
"""
from typing import Dict, Any, Optional
from dipeo_domain import TokenUsage


class TokenUsageService:
    """Service for handling token usage operations and provider-specific parsing."""
    
    @staticmethod
    def zero() -> TokenUsage:
        """Create a zero token usage instance."""
        return TokenUsage(input=0, output=0, cached=0)
    
    @staticmethod
    def add(first: TokenUsage, second: TokenUsage) -> TokenUsage:
        """Add two token usage instances."""
        return TokenUsage(
            input=first.input + second.input,
            output=first.output + second.output,
            cached=(first.cached or 0) + (second.cached or 0)
        )
    
    @staticmethod
    def to_dict(usage: TokenUsage) -> Dict[str, float]:
        """Convert TokenUsage to dictionary format."""
        return {
            "input": usage.input,
            "output": usage.output,
            "cached": usage.cached or 0,
            "total": usage.total or (usage.input + usage.output)
        }
    
    @staticmethod
    def from_response(response: dict) -> TokenUsage:
        """Create TokenUsage from LLM response dict."""
        return TokenUsage(
            input=response.get("input_tokens", 0),
            output=response.get("output_tokens", 0),
            cached=response.get("cached_tokens", 0)
        )
    
    @staticmethod
    def from_usage(usage: Any, service: Optional[str] = None) -> TokenUsage:
        """Create TokenUsage from provider-specific usage object."""
        if not usage:
            return TokenUsageService.zero()
        
        # Handle different provider formats
        if service == "gemini" and isinstance(usage, (list, tuple)):
            return TokenUsage(
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
            
        return TokenUsage(
            input=input_tokens,
            output=output_tokens,
            cached=cached_tokens
        )