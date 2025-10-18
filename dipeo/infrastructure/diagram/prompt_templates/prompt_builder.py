import logging
import warnings
from typing import Any

from dipeo.config.base_logger import get_module_logger
from dipeo.domain.diagram.ports import TemplateProcessorPort

logger = get_module_logger(__name__)


class PromptBuilder:
    def __init__(self, template_processor: TemplateProcessorPort | None = None):
        self._processor = template_processor
        self._template_cache: dict[tuple, str] = {}

    def build(
        self,
        prompt: str,
        template_values: dict[str, Any],
        first_only_prompt: str | None = None,
        execution_count: int = 0,
    ) -> str:
        """Build a prompt with template substitution."""
        selected_prompt = self._select_prompt(prompt, first_only_prompt, execution_count)

        if selected_prompt is None:
            logger.warning("No prompt provided to PromptBuilder - returning empty string")
            return ""

        if self._processor:
            cache_key = self._make_cache_key(selected_prompt, template_values)

            if cache_key in self._template_cache:
                return self._template_cache[cache_key]

            result = self._processor.process(selected_prompt, template_values)
            if result.errors:
                logger.warning(f"Template processing errors: {result.errors}")
            if result.missing_keys:
                logger.warning(f"Template missing keys: {result.missing_keys}")

            self._template_cache[cache_key] = result.content

            if len(self._template_cache) > 1000:
                items_to_remove = len(self._template_cache) // 5
                for _ in range(items_to_remove):
                    self._template_cache.pop(next(iter(self._template_cache)))

            return result.content
        else:
            logger.warning("No template processor available!")
            return selected_prompt

    def _make_cache_key(self, template: str, values: dict[str, Any]) -> tuple:
        """Create a hashable cache key from template and values."""
        import json

        try:
            values_str = json.dumps(values, sort_keys=True, default=str)
            return (template, values_str)
        except (TypeError, ValueError):
            return (template, str(sorted(values.items())))

    def prepare_template_values(self, inputs: dict[str, Any]) -> dict[str, Any]:
        """Prepare template values from inputs."""
        template_values = {}

        # Special handling for 'default' and 'first' inputs - flatten their properties to root context
        for special_key in ["default", "first"]:
            if special_key in inputs:
                special_value = inputs[special_key]

                if isinstance(special_value, dict):
                    # Handle double/triple nesting: recursively unwrap if default contains only a 'default' key
                    while (
                        isinstance(special_value, dict)
                        and len(special_value) == 1
                        and "default" in special_value
                    ):
                        special_value = special_value["default"]

                    if isinstance(special_value, dict):
                        for prop_key, prop_value in special_value.items():
                            if prop_key not in template_values:
                                template_values[prop_key] = prop_value
                            else:
                                logger.debug(
                                    f"[PromptBuilder] Collision detected: '{prop_key}' already exists in template_values, skipping from {special_key}"
                                )

                template_values[special_key] = special_value

        for key, value in inputs.items():
            if key in ["default", "first"]:
                continue
            if isinstance(value, str | int | float | bool | type(None)):
                template_values[key] = value

            elif isinstance(value, dict):
                if "messages" in value:
                    messages = value.get("messages", [])
                    if messages:
                        messages_as_dicts = []
                        for msg in messages:
                            if hasattr(msg, "model_dump"):
                                messages_as_dicts.append(msg.model_dump())
                            elif isinstance(msg, dict):
                                messages_as_dicts.append(msg)
                            else:
                                messages_as_dicts.append(
                                    {
                                        "content": getattr(msg, "content", ""),
                                        "from_person_id": str(getattr(msg, "from_person_id", "")),
                                        "to_person_id": str(getattr(msg, "to_person_id", "")),
                                    }
                                )

                        if messages_as_dicts:
                            last_msg = messages_as_dicts[-1]
                            if "content" in last_msg:
                                template_values[f"{key}_last_message"] = last_msg["content"]
                            template_values[f"{key}_messages"] = messages_as_dicts
                    continue

                template_values[key] = value

            elif isinstance(value, list) and all(
                isinstance(v, str | int | float | bool) for v in value
            ):
                template_values[key] = value

        return template_values

    def should_use_first_only_prompt(
        self, first_only_prompt: str | None, execution_count: int
    ) -> bool:
        return bool(first_only_prompt and execution_count == 1)

    def _select_prompt(
        self,
        default_prompt: str,
        first_only_prompt: str | None,
        execution_count: int,
    ) -> str:
        if self.should_use_first_only_prompt(first_only_prompt, execution_count):
            return first_only_prompt
        return default_prompt

    def build_with_context(
        self,
        prompt: str,
        context: dict[str, Any],
        first_only_prompt: str | None = None,
        execution_count: int = 0,
    ) -> str:
        selected_prompt = self._select_prompt(prompt, first_only_prompt, execution_count)

        if selected_prompt is None:
            logger.warning("No prompt provided to build_with_context - returning empty string")
            return ""

        result = self._processor.process(selected_prompt, context)

        if result.errors:
            for error in result.errors:
                warnings.warn(f"Template processing error: {error}", UserWarning, stacklevel=2)

        if result.missing_keys:
            warnings.warn(
                f"Missing template keys: {', '.join(result.missing_keys)}",
                UserWarning,
                stacklevel=2,
            )

        return result.content

    def prepend_conversation_if_needed(
        self, prompt: str, conversation_context: dict[str, Any]
    ) -> str:
        """Prepend conversation context to prompt if appropriate."""
        if prompt is None:
            return prompt

        if "global_conversation" not in conversation_context:
            return prompt

        conversation_vars = ["global_conversation", "global_message_count", "person_conversations"]
        if any(f"{{{{{var}" in prompt or f"{{#{var}" in prompt for var in conversation_vars):
            return prompt

        global_conversation = conversation_context.get("global_conversation", [])
        if not global_conversation:
            return prompt

        try:
            from dipeo.config import get_settings

            settings = get_settings()
            context_limit = getattr(settings, "conversation_context_limit", 10)
        except Exception:
            context_limit = 10

        conversation_summary = []
        conversation_summary.append(
            f"[Previous conversation with {len(global_conversation)} messages]"
        )

        recent_messages = (
            global_conversation[-context_limit:]
            if len(global_conversation) > context_limit
            else global_conversation
        )

        for msg in recent_messages:
            from_person = msg.get("from", "unknown")
            content = msg.get("content", "")
            if content:
                conversation_summary.append(f"{from_person}: {content}")

        if len(global_conversation) > context_limit:
            conversation_summary.append(
                f"... ({len(global_conversation) - context_limit} earlier messages omitted)"
            )

        conversation_summary.append("")

        conversation_text = "\n".join(conversation_summary)
        return f"{conversation_text}\n{prompt}"
