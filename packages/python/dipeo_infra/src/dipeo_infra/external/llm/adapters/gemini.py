import logging
from typing import Any

import google.genai as genai
from dipeo_domain import ChatResult, TokenUsage

from ..base import BaseAdapter

logger = logging.getLogger(__name__)


class GeminiAdapter(BaseAdapter):
    """Adapter for Google Gemini models via the genai API."""

    def __init__(self, model_name: str, api_key: str, base_url: str | None = None):
        # Gemini doesn't use base_url, but we accept it for consistency
        super().__init__(model_name, api_key, base_url)

    def _initialize_client(self) -> Any:
        """Initialize the Gemini client."""
        # Configure the API key globally for google-generativeai
        genai.configure(api_key=self.api_key)
        # Return None as genai uses state configuration
        return None

    def _make_api_call(self, messages: list[dict[str, str]], **kwargs) -> ChatResult:
        """Make API call to Gemini and return ChatResult."""
        # Extract system prompt from messages
        system_prompt = ""
        gemini_messages = []

        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")

            if role == "system":
                system_prompt = content
            elif role == "user":
                gemini_messages.append({"role": "user", "parts": [{"text": content}]})
            elif role == "assistant":
                gemini_messages.append({"role": "model", "parts": [{"text": content}]})

        # Get the model with system instruction
        model = genai.GenerativeModel(
            model_name=self.model_name,
            system_instruction=system_prompt,
        )

        # Extract allowed parameters
        allowed_params = ["max_tokens", "temperature"]
        api_params = {
            k: v for k, v in kwargs.items() if k in allowed_params and v is not None
        }

        generation_config = genai.GenerationConfig(
            max_output_tokens=api_params.get("max_tokens"),
            temperature=api_params.get("temperature"),
        )

        # Make the API call
        response = model.generate_content(
            contents=gemini_messages,
            generation_config=generation_config,
            safety_settings=kwargs.get("gemini_safety_settings"),
        )

        # Extract text
        text = response.text if hasattr(response, "text") else ""

        # Extract usage
        prompt_tokens = None
        completion_tokens = None

        usage_obj = getattr(response, "usage_metadata", None)
        if usage_obj:
            prompt_tokens = getattr(usage_obj, "prompt_token_count", None)
            completion_tokens = getattr(usage_obj, "candidates_token_count", None)

        # Create TokenUsage if we have usage data
        token_usage = None
        if prompt_tokens is not None or completion_tokens is not None:
            token_usage = TokenUsage(
                input=prompt_tokens or 0,
                output=completion_tokens or 0,
                total=(prompt_tokens or 0) + (completion_tokens or 0)
                if prompt_tokens is not None and completion_tokens is not None
                else None,
            )

        return ChatResult(
            text=text,
            tokenUsage=token_usage,
            rawResponse=response,
        )
