"""Anthropic client wrapper."""

import logging
import os
from typing import Any, AsyncIterator, Dict, Iterator, List, Optional

from anthropic import Anthropic, AsyncAnthropic

from ...core.client import AsyncBaseClientWrapper, BaseClientWrapper
from ...core.types import AdapterConfig

logger = logging.getLogger(__name__)


class AnthropicClientWrapper(BaseClientWrapper):
    """Synchronous Anthropic client wrapper."""
    
    def _create_client(self) -> Anthropic:
        """Create Anthropic client instance."""
        api_key = self.config.api_key or os.getenv("ANTHROPIC_API_KEY")
        
        if not api_key:
            raise ValueError("Anthropic API key not provided")
        
        return Anthropic(
            api_key=api_key,
            base_url=self.config.base_url,
            timeout=self.config.timeout,
            max_retries=0  # We handle retries at adapter level
        )
    
    def chat_completion(
        self,
        messages: List[Dict[str, Any]],
        model: str,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        tools: Optional[List[Dict[str, Any]]] = None,
        response_format: Optional[Dict[str, Any]] = None,
        system: Optional[str] = None,
        **kwargs
    ) -> Any:
        """Execute chat completion request."""
        client = self._get_client()
        
        # Build request parameters
        params = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens or 4096,  # Anthropic requires max_tokens
        }
        
        if system:
            params["system"] = system
        
        if tools:
            params["tools"] = tools
            if "tool_choice" in kwargs:
                params["tool_choice"] = kwargs["tool_choice"]
        
        # Anthropic doesn't directly support response_format like OpenAI
        # but we can use tools to achieve structured output
        if response_format and not tools:
            # Convert response_format to a tool for structured output
            params["tools"] = [{
                "name": "respond_with_structure",
                "description": "Respond with structured output",
                "input_schema": response_format.get("json_schema", {})
            }]
            params["tool_choice"] = {"type": "tool", "name": "respond_with_structure"}
        
        # Add any additional parameters
        for key, value in kwargs.items():
            if key not in params and key not in ["tool_choice", "system"]:
                params[key] = value
        
        return client.messages.create(**params)
    
    def stream_chat_completion(
        self,
        messages: List[Dict[str, Any]],
        model: str,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        tools: Optional[List[Dict[str, Any]]] = None,
        system: Optional[str] = None,
        **kwargs
    ) -> Iterator[Any]:
        """Stream chat completion response."""
        client = self._get_client()
        
        params = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens or 4096,
            "stream": True,
        }
        
        if system:
            params["system"] = system
        
        if tools:
            params["tools"] = tools
            if "tool_choice" in kwargs:
                params["tool_choice"] = kwargs["tool_choice"]
        
        # Add any additional parameters
        for key, value in kwargs.items():
            if key not in params and key not in ["tool_choice", "system"]:
                params[key] = value
        
        return client.messages.create(**params)
    
    def count_tokens(self, text: str, model: str) -> int:
        """Count tokens for Anthropic models."""
        # Anthropic doesn't provide a public tokenizer
        # Use approximation based on character count
        return len(text) // 4  # Rough estimate
    
    def validate_connection(self) -> bool:
        """Validate Anthropic client connection."""
        try:
            client = self._get_client()
            # Try a minimal request to validate connection
            client.messages.create(
                model="claude-3-haiku-20240307",
                messages=[{"role": "user", "content": "Hi"}],
                max_tokens=1
            )
            return True
        except Exception as e:
            logger.error(f"Anthropic connection validation failed: {e}")
            return False


class AsyncAnthropicClientWrapper(AsyncBaseClientWrapper):
    """Asynchronous Anthropic client wrapper."""
    
    async def _create_client(self) -> AsyncAnthropic:
        """Create async Anthropic client instance."""
        api_key = self.config.api_key or os.getenv("ANTHROPIC_API_KEY")
        
        if not api_key:
            raise ValueError("Anthropic API key not provided")
        
        return AsyncAnthropic(
            api_key=api_key,
            base_url=self.config.base_url,
            timeout=self.config.timeout,
            max_retries=0  # We handle retries at adapter level
        )
    
    async def chat_completion(
        self,
        messages: List[Dict[str, Any]],
        model: str,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        tools: Optional[List[Dict[str, Any]]] = None,
        response_format: Optional[Dict[str, Any]] = None,
        system: Optional[str] = None,
        **kwargs
    ) -> Any:
        """Execute async chat completion request."""
        client = await self._get_client()
        
        params = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens or 4096,
        }
        
        if system:
            params["system"] = system
        
        if tools:
            params["tools"] = tools
            if "tool_choice" in kwargs:
                params["tool_choice"] = kwargs["tool_choice"]
        
        # Handle structured output via tools
        if response_format and not tools:
            params["tools"] = [{
                "name": "respond_with_structure",
                "description": "Respond with structured output",
                "input_schema": response_format.get("json_schema", {})
            }]
            params["tool_choice"] = {"type": "tool", "name": "respond_with_structure"}
        
        # Add any additional parameters
        for key, value in kwargs.items():
            if key not in params and key not in ["tool_choice", "system"]:
                params[key] = value
        
        return await client.messages.create(**params)
    
    async def stream_chat_completion(
        self,
        messages: List[Dict[str, Any]],
        model: str,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        tools: Optional[List[Dict[str, Any]]] = None,
        system: Optional[str] = None,
        **kwargs
    ) -> AsyncIterator[Any]:
        """Stream async chat completion response."""
        client = await self._get_client()
        
        params = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens or 4096,
            "stream": True,
        }
        
        if system:
            params["system"] = system
        
        if tools:
            params["tools"] = tools
            if "tool_choice" in kwargs:
                params["tool_choice"] = kwargs["tool_choice"]
        
        # Add any additional parameters
        for key, value in kwargs.items():
            if key not in params and key not in ["tool_choice", "system"]:
                params[key] = value
        
        stream = await client.messages.create(**params)
        async for chunk in stream:
            yield chunk
    
    async def count_tokens(self, text: str, model: str) -> int:
        """Count tokens for Anthropic models."""
        # Use approximation
        return len(text) // 4
    
    async def validate_connection(self) -> bool:
        """Validate async Anthropic client connection."""
        try:
            client = await self._get_client()
            # Try a minimal request to validate connection
            await client.messages.create(
                model="claude-3-haiku-20240307",
                messages=[{"role": "user", "content": "Hi"}],
                max_tokens=1
            )
            return True
        except Exception as e:
            logger.error(f"Anthropic connection validation failed: {e}")
            return False


class ClaudeCodeClientWrapper(AnthropicClientWrapper):
    """Claude Code specific client wrapper."""
    
    def __init__(self, config: AdapterConfig):
        """Initialize Claude Code client with specific configuration."""
        # Update config for Claude Code endpoint if needed
        if not config.base_url:
            config.base_url = "https://api.anthropic.com"  # Or Claude Code specific URL
        
        super().__init__(config)
    
    def chat_completion(
        self,
        messages: List[Dict[str, Any]],
        model: str,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        tools: Optional[List[Dict[str, Any]]] = None,
        response_format: Optional[Dict[str, Any]] = None,
        system: Optional[str] = None,
        **kwargs
    ) -> Any:
        """Execute Claude Code specific chat completion."""
        # Add Claude Code specific parameters
        kwargs["metadata"] = kwargs.get("metadata", {})
        kwargs["metadata"]["source"] = "claude_code"
        
        # Claude Code might have specific tool handling
        if tools:
            # Process computer use tools specially
            computer_use_tools = [t for t in tools if t.get("type") == "computer_20241022"]
            other_tools = [t for t in tools if t.get("type") != "computer_20241022"]
            
            if computer_use_tools:
                kwargs["computer_use"] = True
                tools = other_tools + computer_use_tools
        
        return super().chat_completion(
            messages=messages,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
            tools=tools,
            response_format=response_format,
            system=system,
            **kwargs
        )