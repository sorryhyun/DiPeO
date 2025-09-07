"""Ollama client wrapper for local model execution."""

import asyncio
import logging
from collections.abc import AsyncIterator, Iterator
from typing import Any

import ollama

from dipeo.config.llm import DEFAULT_TEMPERATURE

from ...core.client import AsyncBaseClientWrapper, BaseClientWrapper
from ...core.types import AdapterConfig

logger = logging.getLogger(__name__)


class OllamaClientWrapper(BaseClientWrapper):
    """Synchronous Ollama client wrapper."""

    # Class-level cache for model availability
    _model_availability_cache: dict[str, bool] = {}
    _cache_lock: asyncio.Lock | None = None

    def __init__(self, config: AdapterConfig):
        """Initialize Ollama client wrapper."""
        # Ollama doesn't need an API key
        if not config.api_key:
            config.api_key = ""
        # Default Ollama server URL
        if not config.base_url:
            config.base_url = "http://localhost:11434"
        super().__init__(config)

    def _create_client(self) -> ollama.Client:
        """Create Ollama client instance."""
        return ollama.Client(host=self.config.base_url)

    def _ensure_model_available(self, model: str) -> bool:
        """Check if model is available locally, pull if not."""
        cache_key = f"{self.config.base_url}:{model}"

        # Check cache first
        if cache_key in OllamaClientWrapper._model_availability_cache:
            logger.debug(f"Model {model} availability cached: True")
            return OllamaClientWrapper._model_availability_cache[cache_key]

        try:
            client = self._get_client()

            # Check if model exists
            models_list = client.list()
            available_models = [
                m.get("name", "").split(":")[0] for m in models_list.get("models", [])
            ]
            full_model_names = [m.get("name", "") for m in models_list.get("models", [])]

            # Check both base name and full name
            model_base = model.split(":")[0]
            if model_base in available_models or model in full_model_names:
                logger.debug(f"Model {model} already available locally")
                OllamaClientWrapper._model_availability_cache[cache_key] = True
                return True

            # Try to pull the model
            logger.info(f"Model {model} not found locally, attempting to pull...")
            client.pull(model)
            logger.info(f"Successfully pulled model {model}")
            OllamaClientWrapper._model_availability_cache[cache_key] = True
            return True

        except Exception as e:
            logger.error(f"Failed to ensure model {model} is available: {e}")
            return False

    def chat_completion(
        self,
        messages: list[dict[str, Any]],
        model: str,
        temperature: float = DEFAULT_TEMPERATURE,
        max_tokens: int | None = None,
        tools: list[dict[str, Any]] | None = None,
        response_format: dict[str, Any] | None = None,
        system: str | None = None,
        **kwargs,
    ) -> Any:
        """Execute chat completion request."""
        # Ensure model is available
        self._ensure_model_available(model)

        client = self._get_client()

        # Convert messages to Ollama format
        ollama_messages = []

        # Add system message if present
        if system:
            ollama_messages.append({"role": "system", "content": system})

        # Add other messages
        for msg in messages:
            ollama_messages.append(
                {"role": msg.get("role", "user"), "content": msg.get("content", "")}
            )

        # Prepare parameters
        params = {
            "model": model,
            "messages": ollama_messages,
            "stream": False,
        }

        # Add options
        options = {}
        if temperature is not None:
            options["temperature"] = temperature
        if max_tokens is not None:
            options["num_predict"] = max_tokens  # Ollama uses num_predict
        if "top_p" in kwargs:
            options["top_p"] = kwargs["top_p"]
        if "seed" in kwargs:
            options["seed"] = kwargs["seed"]

        if options:
            params["options"] = options

        # Make the API call
        response = client.chat(**params)

        return response

    def stream_chat_completion(
        self,
        messages: list[dict[str, Any]],
        model: str,
        temperature: float = DEFAULT_TEMPERATURE,
        max_tokens: int | None = None,
        tools: list[dict[str, Any]] | None = None,
        system: str | None = None,
        **kwargs,
    ) -> Iterator[Any]:
        """Stream chat completion response."""
        # Ensure model is available
        self._ensure_model_available(model)

        client = self._get_client()

        # Convert messages to Ollama format
        ollama_messages = []

        if system:
            ollama_messages.append({"role": "system", "content": system})

        for msg in messages:
            ollama_messages.append(
                {"role": msg.get("role", "user"), "content": msg.get("content", "")}
            )

        # Prepare parameters
        params = {
            "model": model,
            "messages": ollama_messages,
            "stream": True,
        }

        # Add options
        options = {}
        if temperature is not None:
            options["temperature"] = temperature
        if max_tokens is not None:
            options["num_predict"] = max_tokens
        if "top_p" in kwargs:
            options["top_p"] = kwargs["top_p"]

        if options:
            params["options"] = options

        # Stream the response
        stream = client.chat(**params)
        yield from stream

    def count_tokens(self, text: str, model: str) -> int:
        """Count tokens (approximation for Ollama models)."""
        # Rough approximation
        return len(text) // 4

    def validate_connection(self) -> bool:
        """Validate Ollama client connection."""
        try:
            client = self._get_client()
            # Try to list models to validate connection
            client.list()
            return True
        except Exception as e:
            logger.error(f"Ollama connection validation failed: {e}")
            return False


class AsyncOllamaClientWrapper(AsyncBaseClientWrapper):
    """Asynchronous Ollama client wrapper."""

    # Class-level cache for model availability
    _model_availability_cache: dict[str, bool] = {}
    _cache_lock: asyncio.Lock | None = None

    def __init__(self, config: AdapterConfig):
        """Initialize async Ollama client wrapper."""
        # Ollama doesn't need an API key
        if not config.api_key:
            config.api_key = ""
        # Default Ollama server URL
        if not config.base_url:
            config.base_url = "http://localhost:11434"
        super().__init__(config)

    async def _create_client(self) -> ollama.Client:
        """Create async Ollama client instance."""
        return ollama.Client(host=self.config.base_url)

    async def _ensure_model_available(self, model: str) -> bool:
        """Check if model is available locally, pull if not."""
        cache_key = f"{self.config.base_url}:{model}"

        # Check cache first
        if cache_key in AsyncOllamaClientWrapper._model_availability_cache:
            logger.debug(f"Model {model} availability cached: True")
            return AsyncOllamaClientWrapper._model_availability_cache[cache_key]

        # Use lock to prevent concurrent checks
        if AsyncOllamaClientWrapper._cache_lock is None:
            AsyncOllamaClientWrapper._cache_lock = asyncio.Lock()

        async with AsyncOllamaClientWrapper._cache_lock:
            # Double-check cache after acquiring lock
            if cache_key in AsyncOllamaClientWrapper._model_availability_cache:
                return AsyncOllamaClientWrapper._model_availability_cache[cache_key]

            try:
                client = await self._get_client()

                # Check if model exists
                models_list = await asyncio.to_thread(client.list)
                available_models = [
                    m.get("name", "").split(":")[0] for m in models_list.get("models", [])
                ]
                full_model_names = [m.get("name", "") for m in models_list.get("models", [])]

                # Check both base name and full name
                model_base = model.split(":")[0]
                if model_base in available_models or model in full_model_names:
                    logger.debug(f"Model {model} already available locally")
                    AsyncOllamaClientWrapper._model_availability_cache[cache_key] = True
                    return True

                # Try to pull the model
                logger.info(f"Model {model} not found locally, attempting to pull...")
                await asyncio.to_thread(client.pull, model)
                logger.info(f"Successfully pulled model {model}")
                AsyncOllamaClientWrapper._model_availability_cache[cache_key] = True
                return True

            except Exception as e:
                logger.error(f"Failed to ensure model {model} is available: {e}")
                return False

    async def chat_completion(
        self,
        messages: list[dict[str, Any]],
        model: str,
        temperature: float = DEFAULT_TEMPERATURE,
        max_tokens: int | None = None,
        tools: list[dict[str, Any]] | None = None,
        response_format: dict[str, Any] | None = None,
        system: str | None = None,
        **kwargs,
    ) -> Any:
        """Execute async chat completion request."""
        # Ensure model is available
        await self._ensure_model_available(model)

        client = await self._get_client()

        # Convert messages to Ollama format
        ollama_messages = []

        if system:
            ollama_messages.append({"role": "system", "content": system})

        for msg in messages:
            ollama_messages.append(
                {"role": msg.get("role", "user"), "content": msg.get("content", "")}
            )

        # Prepare parameters
        params = {
            "model": model,
            "messages": ollama_messages,
            "stream": False,
        }

        # Add options
        options = {}
        if temperature is not None:
            options["temperature"] = temperature
        if max_tokens is not None:
            options["num_predict"] = max_tokens
        if "top_p" in kwargs:
            options["top_p"] = kwargs["top_p"]
        if "seed" in kwargs:
            options["seed"] = kwargs["seed"]

        if options:
            params["options"] = options

        # Make async API call
        response = await asyncio.to_thread(client.chat, **params)

        return response

    async def stream_chat_completion(
        self,
        messages: list[dict[str, Any]],
        model: str,
        temperature: float = DEFAULT_TEMPERATURE,
        max_tokens: int | None = None,
        tools: list[dict[str, Any]] | None = None,
        system: str | None = None,
        **kwargs,
    ) -> AsyncIterator[Any]:
        """Stream async chat completion response."""
        # Ensure model is available
        await self._ensure_model_available(model)

        client = await self._get_client()

        # Convert messages to Ollama format
        ollama_messages = []

        if system:
            ollama_messages.append({"role": "system", "content": system})

        for msg in messages:
            ollama_messages.append(
                {"role": msg.get("role", "user"), "content": msg.get("content", "")}
            )

        # Prepare parameters
        params = {
            "model": model,
            "messages": ollama_messages,
            "stream": True,
        }

        # Add options
        options = {}
        if temperature is not None:
            options["temperature"] = temperature
        if max_tokens is not None:
            options["num_predict"] = max_tokens
        if "top_p" in kwargs:
            options["top_p"] = kwargs["top_p"]

        if options:
            params["options"] = options

        # Stream async response
        def sync_stream():
            return client.chat(**params)

        stream = await asyncio.to_thread(sync_stream)
        for chunk in stream:
            yield chunk

    async def count_tokens(self, text: str, model: str) -> int:
        """Count tokens (approximation for Ollama models)."""
        return len(text) // 4

    async def validate_connection(self) -> bool:
        """Validate async Ollama client connection."""
        try:
            client = await self._get_client()
            # Try to list models to validate connection
            await asyncio.to_thread(client.list)
            return True
        except Exception as e:
            logger.error(f"Ollama connection validation failed: {e}")
            return False
