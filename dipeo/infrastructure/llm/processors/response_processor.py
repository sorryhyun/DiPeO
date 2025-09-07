"""Response processing for LLM providers."""

import json
import logging
from typing import Any

from ..core.types import LLMResponse, ProviderType, TokenUsage

logger = logging.getLogger(__name__)


class ResponseProcessor:
    """Processes responses from LLM providers."""

    def __init__(self, provider: ProviderType):
        """Initialize response processor for specific provider."""
        self.provider = provider

    def process_response(self, raw_response: Any, model: str) -> LLMResponse:
        """Process raw provider response into unified format."""
        if self.provider == ProviderType.OPENAI:
            return self._process_openai_response(raw_response, model)
        elif self.provider == ProviderType.ANTHROPIC:
            return self._process_anthropic_response(raw_response, model)
        elif self.provider == ProviderType.GOOGLE:
            return self._process_google_response(raw_response, model)
        elif self.provider == ProviderType.OLLAMA:
            return self._process_ollama_response(raw_response, model)
        else:
            return self._process_generic_response(raw_response, model)

    def _process_openai_response(self, response: Any, model: str) -> LLMResponse:
        """Process OpenAI response."""
        content = ""
        usage = None
        metadata = {}
        structured_output = None

        # Handle responses.parse() output (structured output)
        if hasattr(response, "output_parsed"):
            # Structured output from parse() method
            structured_output = response.output_parsed
            # Convert to JSON string for content field if it's a Pydantic model or dict
            if structured_output:
                if hasattr(structured_output, "model_dump_json"):
                    # Pydantic v2 model
                    content = structured_output.model_dump_json()
                elif hasattr(structured_output, "json"):
                    # Pydantic v1 model
                    content = structured_output.json()
                elif isinstance(structured_output, dict):
                    # Plain dict
                    content = json.dumps(structured_output)
                else:
                    # Fallback for other types
                    content = (
                        json.dumps(structured_output)
                        if hasattr(json, "dumps")
                        else str(structured_output)
                    )
            else:
                content = ""

        # Handle new responses.create API format (based on actual response structure)
        elif hasattr(response, "output") and isinstance(response.output, list):
            # Extract content from output[0].content[0].text
            for message in response.output:
                if hasattr(message, "type") and message.type == "message":
                    if hasattr(message, "content") and isinstance(message.content, list):
                        text_parts = []
                        for content_block in message.content:
                            if (
                                hasattr(content_block, "type")
                                and content_block.type == "output_text"
                            ) and hasattr(content_block, "text"):
                                text_parts.append(content_block.text)
                        content = "".join(text_parts)

                    # Extract metadata from message
                    if hasattr(message, "id"):
                        metadata["message_id"] = message.id
                    if hasattr(message, "role"):
                        metadata["role"] = message.role
                    if hasattr(message, "status"):
                        metadata["message_status"] = message.status

        # Fallback to old chat.completions format
        elif hasattr(response, "choices") and response.choices:
            choice = response.choices[0]
            if hasattr(choice, "message"):
                content = choice.message.content or ""

                # Handle function calls
                if hasattr(choice.message, "tool_calls"):
                    metadata["tool_calls"] = choice.message.tool_calls

            # Extract finish reason
            if hasattr(choice, "finish_reason"):
                metadata["finish_reason"] = choice.finish_reason

        # Extract usage (new format)
        if hasattr(response, "usage"):
            # Try new format first
            if hasattr(response.usage, "input_tokens"):
                usage = TokenUsage(
                    input_tokens=response.usage.input_tokens,
                    output_tokens=response.usage.output_tokens,
                    total_tokens=response.usage.total_tokens,
                )
            # Fallback to old format
            elif hasattr(response.usage, "prompt_tokens"):
                usage = TokenUsage(
                    input_tokens=response.usage.prompt_tokens,
                    output_tokens=response.usage.completion_tokens,
                    total_tokens=response.usage.total_tokens,
                )

        # Extract model info
        if hasattr(response, "model"):
            metadata["actual_model"] = response.model

        # Extract response ID
        if hasattr(response, "id"):
            metadata["response_id"] = response.id

        # Extract status
        if hasattr(response, "status"):
            metadata["status"] = response.status

        # Extract temperature and other params
        if hasattr(response, "temperature"):
            metadata["temperature"] = response.temperature
        if hasattr(response, "max_output_tokens"):
            metadata["max_output_tokens"] = response.max_output_tokens

        return LLMResponse(
            content=content,
            model=model,
            provider=self.provider,
            usage=usage,
            raw_response=response,
            metadata=metadata,
            structured_output=structured_output,
        )

    def _process_anthropic_response(self, response: Any, model: str) -> LLMResponse:
        """Process Anthropic response."""
        content = ""
        usage = None
        metadata = {}
        tool_outputs = []

        # Extract content
        if hasattr(response, "content"):
            if isinstance(response.content, str):
                content = response.content
            elif isinstance(response.content, list):
                # Handle content blocks
                text_parts = []
                for block in response.content:
                    if hasattr(block, "type"):
                        if block.type == "text":
                            text_parts.append(block.text)
                        elif block.type == "tool_use":
                            tool_outputs.append(
                                {"id": block.id, "name": block.name, "input": block.input}
                            )
                content = "".join(text_parts)

        # Extract usage
        if hasattr(response, "usage"):
            usage = TokenUsage(
                input_tokens=response.usage.input_tokens, output_tokens=response.usage.output_tokens
            )

        # Extract metadata
        if hasattr(response, "id"):
            metadata["response_id"] = response.id

        if hasattr(response, "model"):
            metadata["actual_model"] = response.model

        if hasattr(response, "stop_reason"):
            metadata["stop_reason"] = response.stop_reason

        if tool_outputs:
            metadata["tool_calls"] = tool_outputs

        return LLMResponse(
            content=content,
            model=model,
            provider=self.provider,
            usage=usage,
            raw_response=response,
            metadata=metadata,
        )

    def _process_google_response(self, response: Any, model: str) -> LLMResponse:
        """Process Google/Gemini response."""
        content = ""
        usage = None
        metadata = {}

        # Extract content
        if hasattr(response, "text"):
            content = response.text
        elif hasattr(response, "candidates") and response.candidates:
            candidate = response.candidates[0]
            if hasattr(candidate, "content") and hasattr(candidate.content, "parts"):
                text_parts = []
                for part in candidate.content.parts:
                    if hasattr(part, "text"):
                        text_parts.append(part.text)
                    elif hasattr(part, "function_call"):
                        metadata.setdefault("function_calls", []).append(
                            {"name": part.function_call.name, "args": part.function_call.args}
                        )
                content = "".join(text_parts)

            # Extract finish reason
            if hasattr(candidate, "finish_reason"):
                metadata["finish_reason"] = candidate.finish_reason

            # Extract safety ratings
            if hasattr(candidate, "safety_ratings"):
                metadata["safety_ratings"] = candidate.safety_ratings

        # Extract usage (if available)
        if hasattr(response, "usage_metadata"):
            usage = TokenUsage(
                input_tokens=response.usage_metadata.prompt_token_count,
                output_tokens=response.usage_metadata.candidates_token_count,
                total_tokens=response.usage_metadata.total_token_count,
            )

        return LLMResponse(
            content=content,
            model=model,
            provider=self.provider,
            usage=usage,
            raw_response=response,
            metadata=metadata,
        )

    def _process_ollama_response(self, response: Any, model: str) -> LLMResponse:
        """Process Ollama response."""
        content = ""
        usage = None
        metadata = {}

        # Handle different response formats
        if isinstance(response, dict):
            content = response.get("response", response.get("message", {}).get("content", ""))

            # Extract usage if available
            if "eval_count" in response and "prompt_eval_count" in response:
                usage = TokenUsage(
                    input_tokens=response["prompt_eval_count"], output_tokens=response["eval_count"]
                )

            # Extract metadata
            if "model" in response:
                metadata["actual_model"] = response["model"]

            if "done_reason" in response:
                metadata["done_reason"] = response["done_reason"]

            if "total_duration" in response:
                metadata["total_duration_ns"] = response["total_duration"]

        elif isinstance(response, str):
            content = response

        elif hasattr(response, "message"):
            content = response.message.get("content", "")

        return LLMResponse(
            content=content,
            model=model,
            provider=self.provider,
            usage=usage,
            raw_response=response,
            metadata=metadata,
        )

    def _process_generic_response(self, response: Any, model: str) -> LLMResponse:
        """Process generic/unknown provider response."""
        content = ""

        # Try common patterns
        if isinstance(response, str):
            content = response
        elif isinstance(response, dict):
            content = response.get("content", response.get("text", response.get("response", "")))
        elif hasattr(response, "content"):
            content = response.content
        elif hasattr(response, "text"):
            content = response.text
        else:
            content = str(response)

        return LLMResponse(
            content=content, model=model, provider=self.provider, raw_response=response
        )

    def extract_error_message(self, error: Exception) -> str:
        """Extract meaningful error message from provider exception."""
        error_str = str(error)

        if self.provider == ProviderType.OPENAI:
            # OpenAI error format
            if "message" in error_str:
                try:
                    import re

                    match = re.search(r'"message":\s*"([^"]+)"', error_str)
                    if match:
                        return match.group(1)
                except:
                    pass

        elif self.provider == ProviderType.ANTHROPIC:
            # Anthropic error format
            if "error" in error_str.lower():
                return error_str

        # Default: return full error
        return error_str

    def is_rate_limit_error(self, error: Exception) -> bool:
        """Check if error is a rate limit error."""
        error_str = str(error).lower()

        rate_limit_indicators = [
            "rate limit",
            "rate_limit",
            "quota",
            "too many requests",
            "429",
            "resource_exhausted",
            "overloaded",
        ]

        return any(indicator in error_str for indicator in rate_limit_indicators)

    def is_auth_error(self, error: Exception) -> bool:
        """Check if error is an authentication error."""
        error_str = str(error).lower()

        auth_indicators = [
            "api key",
            "api_key",
            "unauthorized",
            "authentication",
            "401",
            "invalid key",
            "invalid_api_key",
            "permission denied",
        ]

        return any(indicator in error_str for indicator in auth_indicators)

    def extract_retry_after(self, error: Exception) -> float | None:
        """Extract retry-after value from rate limit error."""
        error_str = str(error)

        # Try to extract retry-after header value
        import re

        # Common patterns
        patterns = [
            r'retry[_-]?after["\s:]+(\d+(?:\.\d+)?)',
            r"wait\s+(\d+(?:\.\d+)?)\s+seconds?",
            r"try again in\s+(\d+(?:\.\d+)?)",
        ]

        for pattern in patterns:
            match = re.search(pattern, error_str, re.IGNORECASE)
            if match:
                try:
                    return float(match.group(1))
                except:
                    pass

        return None
