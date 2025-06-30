import logging
from typing import Any

import google.genai as genai

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

    def _build_messages(
        self,
        system_prompt: str,
        cacheable_prompt: str = "",
        user_prompt: str = "",
        citation_target: str = "",
        **kwargs,
    ) -> dict[str, Any]:
        """Build provider-specific message format."""
        # Use base class helper to build user message content
        user_content = self._build_user_message_content(
            cacheable_prompt, user_prompt, citation_target
        )

        message_content = [{"role": "user", "parts": [{"text": user_content}]}]

        # Handle prefill
        if kwargs.get("prefill"):
            prefill_text = self._safe_strip_prefill(kwargs["prefill"])
            message_content.append({"role": "model", "parts": [{"text": prefill_text}]})

        # Return both system prompt and messages for Gemini API
        return {"system_instruction": system_prompt, "contents": message_content}

    def _extract_text_from_response(self, response: Any, **kwargs) -> str:
        """Extract text content from provider-specific response."""
        return response.text if hasattr(response, "text") else ""

    def _extract_usage_from_response(self, response: Any) -> dict[str, int] | None:
        """Extract token usage from provider-specific response."""
        usage_obj = getattr(response, "usage_metadata", None)
        return self._extract_usage_safely(
            usage_obj,
            input_field="prompt_token_count",
            output_field="candidates_token_count"
        )

    def _make_api_call(self, messages: Any, **kwargs) -> Any:
        """Make the actual API call to the provider."""
        # Get the model with system instruction
        model = genai.GenerativeModel(
            model_name=self.model_name,
            system_instruction=messages["system_instruction"],
        )

        # Use base class helper to extract allowed parameters
        allowed_params = ["max_tokens", "temperature"]
        api_params = self._extract_api_params(kwargs, allowed_params)

        generation_config = genai.GenerationConfig(
            max_output_tokens=api_params.get("max_tokens"),
            temperature=api_params.get("temperature"),
        )

        return model.generate_content(
            contents=messages["contents"],
            generation_config=generation_config,
            safety_settings=kwargs.get("gemini_safety_settings"),
        )

    def list_models(self) -> list[str]:
        """List available Gemini models."""
        logger.info("[Gemini] Fetching available models from Gemini API")
        try:
            # List models using the state genai module
            models = genai.list_models()
            # Filter for generateContent models
            gemini_models = [
                model.name.replace("models/", "")
                for model in models
                if "gemini" in model.name.lower()
                and "generateContent" in model.supported_generation_methods
            ]
            logger.info(f"[Gemini] Found {len(gemini_models)} models")
            return sorted(gemini_models)
        except Exception as e:
            logger.error(f"[Gemini] Failed to fetch models from API: {e!s}")
            # Use base class fallback models
            return super().list_models()
