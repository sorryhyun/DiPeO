"""Ollama LLM adapter for local model execution."""

import asyncio
import logging
from collections.abc import AsyncIterator
from typing import Any

import ollama
from ollama import ResponseError

from dipeo.diagram_generated import ChatResult, LLMRequestOptions, TokenUsage

from ..drivers.base import BaseLLMAdapter

logger = logging.getLogger(__name__)


class OllamaAdapter(BaseLLMAdapter):
    """Adapter for Ollama local LLM models."""
    
    # Class-level cache for model availability to avoid repeated checks
    _model_availability_cache: dict[str, bool] = {}
    _cache_lock: asyncio.Lock | None = None
    
    def __init__(self, model_name: str, api_key: str | None = None, base_url: str | None = None):
        """Initialize Ollama adapter.
        
        Args:
            model_name: Name of the Ollama model to use
            api_key: Not used for Ollama, kept for interface compatibility
            base_url: Ollama server URL (default: http://localhost:11434)
        """
        # Ollama doesn't need an API key, use empty string
        super().__init__(model_name, api_key or "", base_url or "http://localhost:11434")
        self.max_retries = 3
        self.retry_delay = 1.0
    
    def _initialize_client(self) -> ollama.Client:
        """Initialize Ollama client with configured host."""
        return ollama.Client(host=self.base_url)
    
    def supports_tools(self) -> bool:
        """Ollama doesn't support function calling yet."""
        return False
    
    def supports_response_api(self) -> bool:
        """Ollama doesn't have a separate response API."""
        return False
    
    async def _ensure_model_available(self, model: str) -> bool:
        """Check if model is available locally, pull if not.
        
        Args:
            model: Model name to check
            
        Returns:
            True if model is available or successfully pulled
        """
        # Check class-level cache first
        cache_key = f"{self.base_url}:{model}"
        if cache_key in OllamaAdapter._model_availability_cache:
            logger.debug(f"Model {model} availability cached: True")
            return OllamaAdapter._model_availability_cache[cache_key]
        
        # Use lock to prevent concurrent checks for the same model
        if OllamaAdapter._cache_lock is None:
            OllamaAdapter._cache_lock = asyncio.Lock()
        
        async with OllamaAdapter._cache_lock:
            # Double-check cache after acquiring lock
            if cache_key in OllamaAdapter._model_availability_cache:
                logger.debug(f"Model {model} availability cached (after lock): True")
                return OllamaAdapter._model_availability_cache[cache_key]
            
            try:
                # Check if model exists
                models_list = await asyncio.to_thread(self.client.list)
                available_models = [m.get("name", "").split(":")[0] for m in models_list.get("models", [])]
                
                # Also check with full model name (including tag)
                full_model_names = [m.get("name", "") for m in models_list.get("models", [])]
                
                # Check both base name and full name
                model_base = model.split(":")[0]
                if model_base in available_models or model in full_model_names:
                    logger.debug(f"Model {model} already available locally")
                    OllamaAdapter._model_availability_cache[cache_key] = True
                    return True
                
                # Try to pull the model
                logger.info(f"Model {model} not found locally, attempting to pull...")
                await asyncio.to_thread(self.client.pull, model)
                logger.info(f"Successfully pulled model {model}")
                OllamaAdapter._model_availability_cache[cache_key] = True
                return True
                
            except Exception as e:
                logger.error(f"Failed to ensure model {model} is available: {e}")
                return False
    
    def _make_api_call(self, messages: list[dict[str, str]], **kwargs) -> ChatResult:
        """Make synchronous API call to Ollama."""
        return asyncio.run(self.chat_async(messages, **kwargs))
    
    async def chat_async(self, messages: list[dict[str, str]], **kwargs) -> ChatResult:
        """Async chat method for Ollama."""
        if messages is None:
            messages = []
        
        # Handle options from LLMRequestOptions
        options = kwargs.get('options')
        if isinstance(options, LLMRequestOptions):
            if options.temperature is not None:
                kwargs['temperature'] = options.temperature
            if options.max_tokens is not None:
                kwargs['num_predict'] = options.max_tokens  # Ollama uses num_predict
            if options.top_p is not None:
                kwargs['top_p'] = options.top_p
        
        # Extract system prompt and messages
        system_prompt, processed_messages = self._extract_system_and_messages(messages)
        
        # Ensure model is available
        await self._ensure_model_available(self.model_name)
        
        # Convert messages to Ollama format
        ollama_messages = []
        
        # Add system message if present
        if system_prompt:
            ollama_messages.append({"role": "system", "content": system_prompt})
        
        # Add other messages
        for msg in processed_messages:
            ollama_messages.append({
                "role": msg["role"],
                "content": msg["content"]
            })
        
        # Prepare Ollama-specific parameters
        ollama_params = {
            "model": self.model_name,
            "messages": ollama_messages,
            "stream": False,  # We'll handle streaming separately
        }
        
        # Add optional parameters if provided
        if "temperature" in kwargs:
            ollama_params["options"] = ollama_params.get("options", {})
            ollama_params["options"]["temperature"] = kwargs["temperature"]
        if "num_predict" in kwargs:
            ollama_params["options"] = ollama_params.get("options", {})
            ollama_params["options"]["num_predict"] = kwargs["num_predict"]
        if "top_p" in kwargs:
            ollama_params["options"] = ollama_params.get("options", {})
            ollama_params["options"]["top_p"] = kwargs["top_p"]
        
        # Make API call with retry logic
        last_exception = None
        for attempt in range(self.max_retries):
            try:
                # Use Ollama's chat method
                response = await asyncio.to_thread(
                    self.client.chat,
                    **ollama_params
                )
                
                # Extract response text
                text = response.get("message", {}).get("content", "")
                
                # Ollama provides token counts in some cases
                token_usage = None
                if "prompt_eval_count" in response and "eval_count" in response:
                    token_usage = TokenUsage(
                        input=response.get("prompt_eval_count", 0),
                        output=response.get("eval_count", 0),
                        total=response.get("prompt_eval_count", 0) + response.get("eval_count", 0)
                    )
                logger.debug(f"Output text: {text}")
                return ChatResult(
                    text=text,
                    token_usage=token_usage,
                    raw_response=response,
                    tool_outputs=None  # Ollama doesn't support tools yet
                )
                
            except ResponseError as e:
                last_exception = e
                if e.status_code == 404:
                    # Model not found, try to pull it
                    logger.warning(f"Model {self.model_name} not found, attempting to pull...")
                    if await self._ensure_model_available(self.model_name):
                        continue  # Retry after pulling
                    
                logger.error(f"Ollama API error (attempt {attempt + 1}/{self.max_retries}): {e}")
                
                if attempt < self.max_retries - 1:
                    delay = self.retry_delay * (2 ** attempt)
                    await asyncio.sleep(delay)
                    continue
                    
            except Exception as e:
                last_exception = e
                logger.error(f"Unexpected error calling Ollama (attempt {attempt + 1}/{self.max_retries}): {e}")
                
                if attempt < self.max_retries - 1:
                    delay = self.retry_delay * (2 ** attempt)
                    await asyncio.sleep(delay)
                    continue
        
        # If all retries failed, return empty result
        logger.error(f"All retry attempts exhausted for Ollama API")
        return ChatResult(
            text=f"Failed to get response from Ollama: {last_exception}",
            raw_response=None
        )
    
    async def stream_chat(self, messages: list[dict[str, str]], **kwargs) -> AsyncIterator[str]:
        """Stream chat responses from Ollama."""
        if messages is None:
            messages = []
        
        # Extract system prompt and messages
        system_prompt, processed_messages = self._extract_system_and_messages(messages)
        
        # Ensure model is available
        await self._ensure_model_available(self.model_name)
        
        # Convert messages to Ollama format
        ollama_messages = []
        
        if system_prompt:
            ollama_messages.append({"role": "system", "content": system_prompt})
        
        for msg in processed_messages:
            ollama_messages.append({
                "role": msg["role"],
                "content": msg["content"]
            })
        
        try:
            # Use Ollama's streaming chat
            stream = await asyncio.to_thread(
                self.client.chat,
                model=self.model_name,
                messages=ollama_messages,
                stream=True
            )
            
            # Yield chunks as they come
            for chunk in stream:
                if "message" in chunk and "content" in chunk["message"]:
                    yield chunk["message"]["content"]
                    
        except Exception as e:
            logger.error(f"Error streaming from Ollama: {e}")
            yield f"Error: {e}"
    
    async def get_available_models(self) -> list[str]:
        """Get list of available Ollama models."""
        try:
            # Get list of models from Ollama
            response = await asyncio.to_thread(self.client.list)
            
            models = []
            for model_info in response.get("models", []):
                # Extract model name (without tag)
                model_name = model_info.get("name", "")
                if model_name:
                    # Include both full name and base name
                    models.append(model_name)
                    base_name = model_name.split(":")[0]
                    if base_name not in models:
                        models.append(base_name)
            
            # Sort models alphabetically
            models.sort()
            
            return models if models else ["No models available - run 'ollama pull <model>'"]
            
        except Exception as e:
            logger.warning(f"Failed to fetch Ollama models: {e}")
            return ["Error: Ollama service not available"]