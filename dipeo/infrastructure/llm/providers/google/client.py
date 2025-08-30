"""Google AI client wrapper."""

import asyncio
import logging
import os
from typing import Any, AsyncIterator, Dict, Iterator, List, Optional

from google import genai
from google.genai import types

from dipeo.config.llm import DEFAULT_TEMPERATURE
from ...core.client import AsyncBaseClientWrapper, BaseClientWrapper
from ...core.types import AdapterConfig

logger = logging.getLogger(__name__)


class GoogleClientWrapper(BaseClientWrapper):
    """Synchronous Google AI client wrapper."""
    
    def _create_client(self) -> genai.Client:
        """Create Google AI client instance."""
        api_key = self.config.api_key or os.getenv("GOOGLE_API_KEY")
        
        if not api_key:
            raise ValueError("Google API key not provided")
        
        return genai.Client(api_key=api_key)
    
    def chat_completion(
        self,
        messages: List[Dict[str, Any]],
        model: str,
        temperature: float = DEFAULT_TEMPERATURE,
        max_tokens: Optional[int] = None,
        tools: Optional[List[Dict[str, Any]]] = None,
        response_format: Optional[Dict[str, Any]] = None,
        system: Optional[str] = None,
        **kwargs
    ) -> Any:
        """Execute chat completion request."""
        client = self._get_client()
        
        # Convert messages to Gemini format
        gemini_messages = []
        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            
            # Convert role names
            if role == "assistant":
                gemini_messages.append({"role": "model", "parts": [{"text": content}]})
            else:  # user role
                gemini_messages.append({"role": "user", "parts": [{"text": content}]})
        
        # Create model with system instruction
        model_obj = client.GenerativeModel(
            model_name=model,
            system_instruction=system,
        )
        
        # Build generation config
        config_params = {
            "temperature": temperature,
        }
        if max_tokens:
            config_params["max_output_tokens"] = max_tokens
        
        # Add tools if provided
        if tools:
            config_params["tools"] = tools
            config_params["tool_config"] = types.ToolConfig(
                function_calling_config=types.FunctionCallingConfig(mode="AUTO")
            )
        
        generation_config = client.GenerationConfig(**config_params)
        
        # Make the API call
        response = model_obj.generate_content(
            contents=gemini_messages,
            generation_config=generation_config,
            safety_settings=kwargs.get("gemini_safety_settings"),
        )
        
        return response
    
    def stream_chat_completion(
        self,
        messages: List[Dict[str, Any]],
        model: str,
        temperature: float = DEFAULT_TEMPERATURE,
        max_tokens: Optional[int] = None,
        tools: Optional[List[Dict[str, Any]]] = None,
        system: Optional[str] = None,
        **kwargs
    ) -> Iterator[Any]:
        """Stream chat completion response."""
        client = self._get_client()
        
        # Convert messages to Gemini format
        gemini_messages = []
        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            
            if role == "assistant":
                gemini_messages.append({"role": "model", "parts": [{"text": content}]})
            else:
                gemini_messages.append({"role": "user", "parts": [{"text": content}]})
        
        # Create model
        model_obj = client.GenerativeModel(
            model_name=model,
            system_instruction=system,
        )
        
        # Build generation config
        config_params = {
            "temperature": temperature,
        }
        if max_tokens:
            config_params["max_output_tokens"] = max_tokens
        if tools:
            config_params["tools"] = tools
            config_params["tool_config"] = types.ToolConfig(
                function_calling_config=types.FunctionCallingConfig(mode="AUTO")
            )
        
        generation_config = client.GenerationConfig(**config_params)
        
        # Stream the response
        response_stream = model_obj.generate_content_stream(
            contents=gemini_messages,
            generation_config=generation_config,
            safety_settings=kwargs.get("gemini_safety_settings"),
        )
        
        for chunk in response_stream:
            yield chunk
    
    def count_tokens(self, text: str, model: str) -> int:
        """Count tokens for Google models."""
        # Rough approximation for Gemini models
        return len(text) // 4
    
    def validate_connection(self) -> bool:
        """Validate Google client connection."""
        try:
            client = self._get_client()
            # Try to list models to validate connection
            model = client.GenerativeModel(model_name="gemini-1.5-flash")
            model.generate_content(
                contents=[{"role": "user", "parts": [{"text": "Hi"}]}],
                generation_config=client.GenerationConfig(max_output_tokens=1)
            )
            return True
        except Exception as e:
            logger.error(f"Google connection validation failed: {e}")
            return False


class AsyncGoogleClientWrapper(AsyncBaseClientWrapper):
    """Asynchronous Google AI client wrapper."""
    
    async def _create_client(self) -> genai.Client:
        """Create async Google AI client instance."""
        api_key = self.config.api_key or os.getenv("GOOGLE_API_KEY")
        
        if not api_key:
            raise ValueError("Google API key not provided")
        
        return genai.Client(api_key=api_key)
    
    async def chat_completion(
        self,
        messages: List[Dict[str, Any]],
        model: str,
        temperature: float = DEFAULT_TEMPERATURE,
        max_tokens: Optional[int] = None,
        tools: Optional[List[Dict[str, Any]]] = None,
        response_format: Optional[Dict[str, Any]] = None,
        system: Optional[str] = None,
        **kwargs
    ) -> Any:
        """Execute async chat completion request."""
        client = await self._get_client()
        
        # Convert messages to Gemini format
        gemini_messages = []
        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            
            if role == "assistant":
                gemini_messages.append({"role": "model", "parts": [{"text": content}]})
            else:
                gemini_messages.append({"role": "user", "parts": [{"text": content}]})
        
        # Create model
        model_obj = client.GenerativeModel(
            model_name=model,
            system_instruction=system,
        )
        
        # Build generation config
        config_params = {
            "temperature": temperature,
        }
        if max_tokens:
            config_params["max_output_tokens"] = max_tokens
        if tools:
            config_params["tools"] = tools
            config_params["tool_config"] = types.ToolConfig(
                function_calling_config=types.FunctionCallingConfig(mode="AUTO")
            )
        
        generation_config = client.GenerationConfig(**config_params)
        
        # Make async API call
        response = await model_obj.agenerate_content(
            contents=gemini_messages,
            generation_config=generation_config,
            safety_settings=kwargs.get("gemini_safety_settings"),
        )
        
        return response
    
    async def stream_chat_completion(
        self,
        messages: List[Dict[str, Any]],
        model: str,
        temperature: float = DEFAULT_TEMPERATURE,
        max_tokens: Optional[int] = None,
        tools: Optional[List[Dict[str, Any]]] = None,
        system: Optional[str] = None,
        **kwargs
    ) -> AsyncIterator[Any]:
        """Stream async chat completion response."""
        client = await self._get_client()
        
        # Convert messages to Gemini format
        gemini_messages = []
        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            
            if role == "assistant":
                gemini_messages.append({"role": "model", "parts": [{"text": content}]})
            else:
                gemini_messages.append({"role": "user", "parts": [{"text": content}]})
        
        # Create model
        model_obj = client.GenerativeModel(
            model_name=model,
            system_instruction=system,
        )
        
        # Build generation config
        config_params = {
            "temperature": temperature,
        }
        if max_tokens:
            config_params["max_output_tokens"] = max_tokens
        if tools:
            config_params["tools"] = tools
            config_params["tool_config"] = types.ToolConfig(
                function_calling_config=types.FunctionCallingConfig(mode="AUTO")
            )
        
        generation_config = client.GenerationConfig(**config_params)
        
        # Stream async response
        response_stream = model_obj.agenerate_content_stream(
            contents=gemini_messages,
            generation_config=generation_config,
            safety_settings=kwargs.get("gemini_safety_settings"),
        )
        
        async for chunk in response_stream:
            yield chunk
    
    async def count_tokens(self, text: str, model: str) -> int:
        """Count tokens for Google models."""
        return len(text) // 4
    
    async def validate_connection(self) -> bool:
        """Validate async Google client connection."""
        try:
            client = await self._get_client()
            model = client.GenerativeModel(model_name="gemini-1.5-flash")
            await model.agenerate_content(
                contents=[{"role": "user", "parts": [{"text": "Hi"}]}],
                generation_config=client.GenerationConfig(max_output_tokens=1)
            )
            return True
        except Exception as e:
            logger.error(f"Google connection validation failed: {e}")
            return False