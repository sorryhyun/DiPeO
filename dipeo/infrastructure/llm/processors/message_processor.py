"""Message processing for LLM providers."""

import logging
from typing import Any

from dipeo.diagram_generated import Message

from ..drivers.types import ProviderType

logger = logging.getLogger(__name__)


class MessageProcessor:
    """Processes messages for LLM providers."""

    def __init__(self, provider: ProviderType):
        """Initialize message processor for specific provider."""
        self.provider = provider

    def prepare_messages(
        self, messages: list[Message], system_prompt: str | None = None
    ) -> list[dict[str, Any]]:
        """Prepare messages for provider API format."""
        prepared = []

        # Handle system prompt
        if system_prompt:
            prepared.append(self._format_system_message(system_prompt))

        # Process each message
        for msg in messages:
            formatted = self._format_message(msg)
            if formatted:
                prepared.append(formatted)

        # Provider-specific post-processing
        if self.provider == ProviderType.OPENAI:
            prepared = self._postprocess_openai_messages(prepared)
        elif self.provider == ProviderType.ANTHROPIC:
            prepared = self._postprocess_anthropic_messages(prepared)
        elif self.provider == ProviderType.GOOGLE:
            prepared = self._postprocess_google_messages(prepared)
        elif self.provider == ProviderType.OLLAMA:
            prepared = self._postprocess_ollama_messages(prepared)

        return prepared

    def _format_message(self, message: Message | dict[str, Any]) -> dict[str, Any] | None:
        """Format a single message for provider API."""
        # Handle both Message objects and dictionaries
        if isinstance(message, dict):
            role = self._normalize_role(message.get("role", "user"))
            content = message.get("content", "")
        else:
            # Assume it's a Message object
            role = self._normalize_role(message.role)
            content = message.content

        # Basic message structure
        formatted = {"role": role, "content": content}

        # Add provider-specific fields
        if self.provider == ProviderType.OPENAI:
            formatted = self._add_openai_fields(formatted, message)
        elif self.provider == ProviderType.ANTHROPIC:
            formatted = self._add_anthropic_fields(formatted, message)
        elif self.provider == ProviderType.GOOGLE:
            formatted = self._add_google_fields(formatted, message)

        return formatted

    def _format_system_message(self, content: str) -> dict[str, Any]:
        """Format a system message."""
        return {"role": "system", "content": content}

    def _normalize_role(self, role: str) -> str:
        """Normalize message role for provider."""
        role = role.lower()

        # Standard roles
        if role in ["system", "user", "assistant", "developer"]:
            return role

        # Provider-specific mappings
        if self.provider == ProviderType.OPENAI:
            if role == "model":
                return "assistant"
            elif role == "tool":
                return "tool"
        elif self.provider == ProviderType.ANTHROPIC:
            if role == "model":
                return "assistant"
            elif role == "human":
                return "user"
        elif self.provider == ProviderType.GOOGLE and role == "assistant":
            return "model"

        # Default to user for unknown roles
        logger.warning(f"Unknown role '{role}' for {self.provider}, defaulting to 'user'")
        return "user"

    def _add_openai_fields(
        self, formatted: dict[str, Any], message: Message | dict[str, Any]
    ) -> dict[str, Any]:
        """Add OpenAI-specific fields to message."""
        # Add name if present
        if isinstance(message, dict):
            if message.get("name"):
                formatted["name"] = message["name"]
        elif hasattr(message, "name") and message.name:
            formatted["name"] = message.name

        # Add tool call ID for tool responses
        if formatted["role"] == "tool":
            if isinstance(message, dict) and "tool_call_id" in message:
                formatted["tool_call_id"] = message["tool_call_id"]
            elif hasattr(message, "tool_call_id"):
                formatted["tool_call_id"] = message.tool_call_id

        # Handle multimodal content
        images = None
        if isinstance(message, dict):
            images = message.get("images")
        elif hasattr(message, "images"):
            images = message.images

        if images:
            content = message.get("content", "") if isinstance(message, dict) else message.content
            formatted["content"] = [{"type": "text", "text": content}]
            for image in images:
                formatted["content"].append({"type": "image_url", "image_url": {"url": image}})

        return formatted

    def _add_anthropic_fields(
        self, formatted: dict[str, Any], message: Message | dict[str, Any]
    ) -> dict[str, Any]:
        """Add Anthropic-specific fields to message."""
        # Handle multimodal content
        images = None
        if isinstance(message, dict):
            images = message.get("images")
        elif hasattr(message, "images"):
            images = message.images

        if images:
            content = message.get("content", "") if isinstance(message, dict) else message.content
            formatted["content"] = [{"type": "text", "text": content}]
            for image in images:
                formatted["content"].append(
                    {
                        "type": "image",
                        "source": {"type": "base64", "media_type": "image/jpeg", "data": image},
                    }
                )

        return formatted

    def _add_google_fields(
        self, formatted: dict[str, Any], message: Message | dict[str, Any]
    ) -> dict[str, Any]:
        """Add Google-specific fields to message."""
        # Gemini uses 'parts' instead of 'content'
        formatted["parts"] = [{"text": formatted.pop("content")}]

        # Handle multimodal content
        images = None
        if isinstance(message, dict):
            images = message.get("images")
        elif hasattr(message, "images"):
            images = message.images

        if images:
            for image in images:
                formatted["parts"].append(
                    {"inline_data": {"mime_type": "image/jpeg", "data": image}}
                )

        return formatted

    def _postprocess_openai_messages(self, messages: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Post-process messages for OpenAI."""
        # Ensure system message is first
        system_msgs = [m for m in messages if m["role"] == "system"]
        other_msgs = [m for m in messages if m["role"] != "system"]

        if system_msgs:
            return system_msgs[:1] + other_msgs  # Only one system message allowed
        return messages

    def _postprocess_anthropic_messages(
        self, messages: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:
        """Post-process messages for Anthropic."""
        # Anthropic requires alternating user/assistant messages
        processed = []
        last_role = None

        for msg in messages:
            if msg["role"] == "system":
                # System messages handled separately in Anthropic
                continue

            # Ensure alternation
            if last_role == msg["role"] and msg["role"] in ["user", "assistant"]:
                # Merge with previous message
                processed[-1]["content"] += f"\n\n{msg['content']}"
            else:
                processed.append(msg)
                last_role = msg["role"]

        return processed

    def _postprocess_google_messages(self, messages: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Post-process messages for Google."""
        # Gemini doesn't use system role, merge into first user message
        processed = []
        system_content = None

        for msg in messages:
            if msg["role"] == "system":
                system_content = msg.get("parts", [{"text": msg.get("content", "")}])[0]["text"]
            else:
                if system_content and msg["role"] == "user" and not processed:
                    # Prepend system content to first user message
                    msg["parts"][0]["text"] = f"{system_content}\n\n{msg['parts'][0]['text']}"
                    system_content = None
                processed.append(msg)

        return processed

    def _postprocess_ollama_messages(self, messages: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Post-process messages for Ollama."""
        # Ollama is generally compatible with OpenAI format
        return messages

    def validate_messages(self, messages: list[dict[str, Any]]) -> bool:
        """Validate messages for provider requirements."""
        if not messages:
            logger.error("No messages to send")
            return False

        # Provider-specific validation
        if self.provider == ProviderType.ANTHROPIC:
            # Anthropic requires at least one user message
            if not any(m["role"] == "user" for m in messages):
                logger.error("Anthropic requires at least one user message")
                return False

        elif self.provider == ProviderType.GOOGLE:
            # Gemini requires non-empty content
            for msg in messages:
                if not msg.get("parts"):
                    logger.error(f"Google message missing parts: {msg}")
                    return False

        return True

    def extract_system_prompt(self, messages: list[Message]) -> str | None:
        """Extract system prompt from messages."""
        for msg in messages:
            # Handle both Message objects and dictionaries
            if isinstance(msg, dict):
                if msg.get("role") == "system":
                    return msg.get("content")
            elif hasattr(msg, "role") and msg.role == "system":
                return msg.content
        return None

    def sanitize_content(self, content: str) -> str:
        """Sanitize message content."""
        # Remove null characters
        content = content.replace("\x00", "")

        # Trim excessive whitespace
        lines = content.split("\n")
        lines = [line.rstrip() for line in lines]
        content = "\n".join(lines)

        # Limit consecutive newlines
        while "\n\n\n" in content:
            content = content.replace("\n\n\n", "\n\n")

        return content.strip()
