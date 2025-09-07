"""OpenAI client wrapper."""

import logging
import os
from collections.abc import AsyncIterator, Iterator
from typing import Any

from openai import AsyncOpenAI, OpenAI
from pydantic import BaseModel

from dipeo.config.llm import DEFAULT_TEMPERATURE

from ...core.client import AsyncBaseClientWrapper, BaseClientWrapper

logger = logging.getLogger(__name__)


class OpenAIClientWrapper(BaseClientWrapper):
    """Synchronous OpenAI client wrapper."""

    def _create_client(self) -> OpenAI:
        """Create OpenAI client instance."""
        api_key = self.config.api_key or os.getenv("OPENAI_API_KEY")

        if not api_key:
            raise ValueError("OpenAI API key not provided")

        return OpenAI(
            api_key=api_key,
            base_url=self.config.base_url,
            timeout=self.config.timeout,
            max_retries=0,  # We handle retries at adapter level
        )

    def chat_completion(
        self,
        messages: list[dict[str, Any]],
        model: str,
        temperature: float = DEFAULT_TEMPERATURE,
        max_tokens: int | None = None,
        tools: list[dict[str, Any]] | None = None,
        response_format: BaseModel | None = None,
        **kwargs,
    ) -> Any:
        """Execute chat completion request."""
        client = self._get_client()

        # Build request parameters for new responses API
        params = {
            "model": model,
            "input": messages,  # New API uses 'input' instead of 'messages'
        }

        # Add optional parameters if provided
        # Note: temperature is not supported in the new responses API
        # if temperature is not None:
        #     params["temperature"] = temperature

        # Max tokens might use a different name in the new API
        if max_tokens is not None:
            params["max_output_tokens"] = max_tokens  # New API parameter name

        # Tools/function calling support
        if tools is not None:
            params["tools"] = tools  # Tools format might be the same

        # Check for text_format in kwargs (from PersonJob handler)
        text_format = kwargs.pop("text_format", None)

        # Determine if we should use structured output
        structured_model = response_format or text_format

        # Include any additional kwargs (but not response_format or text_format)
        kwargs_without_formats = {
            k: v for k, v in kwargs.items() if k not in ["response_format", "text_format"]
        }
        params.update(kwargs_without_formats)

        # Handle structured output based on type
        if (
            structured_model is not None
            and isinstance(structured_model, type)
            and issubclass(structured_model, BaseModel)
        ):
            # Pydantic model - use parse() directly with text_format parameter
            params["text_format"] = structured_model
            return client.responses.parse(**params)
        else:
            # Regular output or non-Pydantic format
            return client.responses.create(**params)

    def stream_chat_completion(
        self,
        messages: list[dict[str, Any]],
        model: str,
        temperature: float = DEFAULT_TEMPERATURE,
        max_tokens: int | None = None,
        tools: list[dict[str, Any]] | None = None,
        **kwargs,
    ) -> Iterator[Any]:
        """Stream chat completion response."""
        client = self._get_client()

        params = {
            "model": model,
            "input": messages,  # New API uses 'input' instead of 'messages'
            "stream": True,
        }

        # Add optional parameters if provided
        # Note: temperature is not supported in the new responses API
        # if temperature is not None:
        #     params["temperature"] = temperature

        if max_tokens is not None:
            params["max_output_tokens"] = max_tokens

        if tools is not None:
            params["tools"] = tools

        # Include any additional kwargs
        params.update(kwargs)

        return client.responses.create(**params)

    def count_tokens(self, text: str, model: str) -> int:
        """Count tokens using tiktoken."""
        try:
            import tiktoken

            # Get the appropriate encoding for the model
            if (
                model.startswith("gpt-4")
                or model.startswith("gpt-5")
                or model.startswith("o3")
                or model.startswith("gpt-3.5")
            ):
                encoding = tiktoken.get_encoding("cl100k_base")
            else:
                encoding = tiktoken.get_encoding("cl100k_base")

            tokens = encoding.encode(text)
            return len(tokens)
        except Exception as e:
            logger.warning(f"Error counting tokens: {e}, using estimation")
            return len(text) // 4  # Rough estimate

    def validate_connection(self) -> bool:
        """Validate OpenAI client connection."""
        try:
            client = self._get_client()
            # Try to list models as a connection test
            client.models.list()
            return True
        except Exception as e:
            logger.error(f"OpenAI connection validation failed: {e}")
            return False


class AsyncOpenAIClientWrapper(AsyncBaseClientWrapper):
    """Asynchronous OpenAI client wrapper."""

    async def _create_client(self) -> AsyncOpenAI:
        """Create async OpenAI client instance."""
        api_key = self.config.api_key or os.getenv("OPENAI_API_KEY")

        if not api_key:
            raise ValueError("OpenAI API key not provided")

        return AsyncOpenAI(
            api_key=api_key,
            base_url=self.config.base_url,
            timeout=self.config.timeout,
            max_retries=0,  # We handle retries at adapter level
        )

    async def chat_completion(
        self,
        messages: list[dict[str, Any]],
        model: str,
        temperature: float = DEFAULT_TEMPERATURE,
        max_tokens: int | None = None,
        tools: list[dict[str, Any]] | None = None,
        response_format: BaseModel | None = None,
        **kwargs,
    ) -> Any:
        """Execute async chat completion request."""
        client = await self._get_client()

        # Build request parameters for new responses API
        params = {
            "model": model,
            "input": messages,  # New API uses 'input' instead of 'messages'
        }

        # Add optional parameters if provided
        # Note: temperature is not supported in the new responses API
        # if temperature is not None:
        #     params["temperature"] = temperature

        if max_tokens is not None:
            params["max_output_tokens"] = max_tokens

        if tools is not None:
            params["tools"] = tools

        # Check for text_format in kwargs (from PersonJob handler)
        text_format = kwargs.pop("text_format", None)

        # Determine if we should use structured output
        structured_model = response_format or text_format

        # Include any additional kwargs (but not response_format or text_format)
        kwargs_without_formats = {
            k: v for k, v in kwargs.items() if k not in ["response_format", "text_format"]
        }
        params.update(kwargs_without_formats)

        # Handle structured output based on type
        if (
            structured_model is not None
            and isinstance(structured_model, type)
            and issubclass(structured_model, BaseModel)
        ):
            # Pydantic model - use parse() directly with text_format parameter
            params["text_format"] = structured_model
            return await client.responses.parse(**params)
        else:
            # Regular output or non-Pydantic format
            return await client.responses.create(**params)

    async def stream_chat_completion(
        self,
        messages: list[dict[str, Any]],
        model: str,
        temperature: float = DEFAULT_TEMPERATURE,
        max_tokens: int | None = None,
        tools: list[dict[str, Any]] | None = None,
        **kwargs,
    ) -> AsyncIterator[Any]:
        """Stream async chat completion response."""
        client = await self._get_client()

        params = {
            "model": model,
            "input": messages,  # New API uses 'input' instead of 'messages'
            "stream": True,
        }

        # Add optional parameters if provided
        # Note: temperature is not supported in the new responses API
        # if temperature is not None:
        #     params["temperature"] = temperature

        if max_tokens is not None:
            params["max_output_tokens"] = max_tokens

        if tools is not None:
            params["tools"] = tools

        # Include any additional kwargs
        params.update(kwargs)

        response = await client.responses.create(**params)
        async for chunk in response:
            yield chunk

    async def count_tokens(self, text: str, model: str) -> int:
        """Count tokens using tiktoken."""
        try:
            import tiktoken

            # Get the appropriate encoding for the model
            if (
                model.startswith("gpt-4")
                or model.startswith("gpt-5")
                or model.startswith("o3")
                or model.startswith("gpt-3.5")
            ):
                encoding = tiktoken.get_encoding("cl100k_base")
            else:
                encoding = tiktoken.get_encoding("cl100k_base")

            tokens = encoding.encode(text)
            return len(tokens)
        except Exception as e:
            logger.warning(f"Error counting tokens: {e}, using estimation")
            return len(text) // 4

    async def validate_connection(self) -> bool:
        """Validate async OpenAI client connection."""
        try:
            client = await self._get_client()
            # Try to list models as a connection test
            await client.models.list()
            return True
        except Exception as e:
            logger.error(f"OpenAI connection validation failed: {e}")
            return False
