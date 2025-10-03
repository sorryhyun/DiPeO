"""Simplified LLM service that directly uses unified provider clients."""

import asyncio
import hashlib
import time
from typing import Any

from dipeo.config import VALID_LLM_SERVICES, get_settings, normalize_service_name
from dipeo.config.services import LLMServiceName
from dipeo.diagram_generated import ChatResult
from dipeo.domain.base import APIKeyError, LLMServiceError
from dipeo.domain.base.mixins import InitializationMixin, LoggingMixin
from dipeo.domain.integrations.ports import APIKeyPort
from dipeo.domain.integrations.ports import LLMService as LLMServicePort
from dipeo.infrastructure.common.utils import SingleFlightCache
from dipeo.infrastructure.llm.drivers.types import (
    AdapterConfig,
    DecisionOutput,
    LLMResponse,
    MemorySelectionOutput,
)


class LLMInfraService(LoggingMixin, InitializationMixin, LLMServicePort):
    """LLM service that directly manages provider clients."""

    def __init__(self, api_key_service: APIKeyPort):
        super().__init__()
        self.api_key_service = api_key_service
        self._client_pool: dict[str, dict[str, Any]] = {}
        self._client_pool_lock = asyncio.Lock()
        self._client_cache = SingleFlightCache()  # For deduplicating client creation
        self._settings = get_settings()

    async def initialize(self) -> None:
        pass

    def _get_api_key(self, api_key_id: str) -> str:
        try:
            api_key_data = self.api_key_service.get_api_key(api_key_id)
            return api_key_data["key"]
        except APIKeyError as e:
            raise LLMServiceError(
                service="api_key_service", message=f"Failed to get API key: {e}"
            ) from e

    def _create_cache_key(self, provider: str, model: str, api_key_id: str) -> str:
        key_string = f"{provider}:{model}:{api_key_id}"
        return hashlib.sha256(key_string.encode()).hexdigest()

    def _create_provider_client(
        self, provider: str, model: str, api_key: str, base_url: str | None = None
    ) -> Any:
        from dipeo.infrastructure.llm.drivers.types import ProviderType

        provider_type_map = {
            LLMServiceName.OPENAI.value: ProviderType.OPENAI,
            LLMServiceName.ANTHROPIC.value: ProviderType.ANTHROPIC,
            LLMServiceName.GOOGLE.value: ProviderType.GOOGLE,
            LLMServiceName.OLLAMA.value: ProviderType.OLLAMA,
            # Claude Code has its own provider type
            LLMServiceName.CLAUDE_CODE.value: ProviderType.CLAUDE_CODE,
            LLMServiceName.CLAUDE_CODE_CUSTOM.value: ProviderType.CLAUDE_CODE,
        }

        provider_type = provider_type_map.get(provider, ProviderType.OPENAI)

        config = AdapterConfig(
            provider_type=provider_type,
            model=model,
            api_key=api_key,
            base_url=base_url,
            timeout=self._settings.llm_timeout if hasattr(self._settings, "llm_timeout") else 300,
            max_retries=3,
            retry_delay=1.0,
            retry_backoff=2.0,
        )

        if provider == LLMServiceName.OPENAI.value:
            from dipeo.infrastructure.llm.providers.openai.unified_client import UnifiedOpenAIClient

            return UnifiedOpenAIClient(config)
        elif provider == LLMServiceName.ANTHROPIC.value:
            from dipeo.infrastructure.llm.providers.anthropic.unified_client import (
                UnifiedAnthropicClient,
            )

            return UnifiedAnthropicClient(config)
        elif provider == LLMServiceName.OLLAMA.value:
            from dipeo.infrastructure.llm.drivers.factory import create_adapter

            return create_adapter(provider, model, api_key, base_url=base_url, async_mode=True)
        elif (
            provider == LLMServiceName.GOOGLE.value
            or provider == LLMServiceName.CLAUDE_CODE.value
            or provider == LLMServiceName.CLAUDE_CODE_CUSTOM.value
        ):
            from dipeo.infrastructure.llm.drivers.factory import create_adapter

            return create_adapter(provider, model, api_key, async_mode=True)
        else:
            from dipeo.infrastructure.llm.drivers.factory import create_adapter

            return create_adapter(provider, model, api_key, base_url=base_url, async_mode=True)

    async def _get_client(self, service_name: str, model: str, api_key_id: str) -> Any:
        provider = normalize_service_name(service_name)

        if provider not in VALID_LLM_SERVICES:
            raise LLMServiceError(
                service=service_name, message=f"Unsupported LLM service: {service_name}"
            )

        cache_key = self._create_cache_key(provider, model, api_key_id)

        async with self._client_pool_lock:
            if cache_key in self._client_pool:
                entry = self._client_pool[cache_key]
                if time.time() - entry["created_at"] <= 3600:
                    return entry["client"]
                else:
                    del self._client_pool[cache_key]

        async def create_new_client():
            if provider == LLMServiceName.OLLAMA.value:
                raw_key = ""
                base_url = (
                    self._settings.ollama_host if hasattr(self._settings, "ollama_host") else None
                )
                client = self._create_provider_client(provider, model, raw_key, base_url)
            elif provider in [
                LLMServiceName.CLAUDE_CODE.value,
                LLMServiceName.CLAUDE_CODE_CUSTOM.value,
            ]:
                # Claude Code doesn't use API keys
                raw_key = ""
                client = self._create_provider_client(provider, model, raw_key)
            else:
                raw_key = self._get_api_key(api_key_id)
                client = self._create_provider_client(provider, model, raw_key)

            async with self._client_pool_lock:
                self._client_pool[cache_key] = {
                    "client": client,
                    "created_at": time.time(),
                }

            return client

        return await self._client_cache.get_or_create(
            cache_key, create_new_client, cache_result=False
        )

    def _convert_response_to_chat_result(self, response: LLMResponse) -> ChatResult:
        # Check for structured output first (from responses.parse())
        if response.structured_output is not None:
            if hasattr(response.structured_output, "model_dump_json"):
                content = response.structured_output.model_dump_json()
            elif hasattr(response.structured_output, "dict"):
                import json

                content = json.dumps(response.structured_output.dict())
                self.log_debug(f"Structured output converted via dict: {content[:200]}")
            else:
                content = str(response.structured_output)
                self.log_debug(f"Structured output converted via str: {content[:200]}")
        elif isinstance(response.content, str):
            content = response.content
        elif hasattr(response.content, "model_dump_json"):
            content = response.content.model_dump_json()
        elif hasattr(response.content, "dict"):
            import json

            content = json.dumps(response.content.dict())
        else:
            content = str(response.content)

        result = ChatResult(text=content)

        if response.usage:
            result.llm_usage = response.usage

        return result

    async def complete_memory_selection(
        self,
        candidate_messages: list[Any],
        task_preview: str,
        criteria: str,
        at_most: int | None,
        model: str,
        api_key_id: str,
        service_name: str,
        **kwargs,
    ) -> MemorySelectionOutput:
        """Direct memory selection without domain adapter."""
        from dipeo.config.llm import MEMORY_SELECTION_MAX_TOKENS
        from dipeo.config.memory import (
            MEMORY_CONTENT_SNIPPET_LENGTH,
            MEMORY_TASK_PREVIEW_MAX_LENGTH,
        )
        from dipeo.diagram_generated.enums import ExecutionPhase

        if not criteria or not criteria.strip():
            return MemorySelectionOutput([])

        # Build memory listing
        lines = []
        for msg in candidate_messages:
            if not getattr(msg, "id", None):
                continue

            content_snippet = (msg.content or "")[:MEMORY_CONTENT_SNIPPET_LENGTH].strip()
            snippet = content_snippet.replace("\n", " ")

            # Determine sender label
            if hasattr(msg, "from_person_id"):
                from dipeo.diagram_generated.domain_models import PersonID

                if msg.from_person_id == PersonID("system"):
                    sender_label = "system"
                else:
                    sender_label = str(msg.from_person_id)
            else:
                sender_label = "unknown"

            lines.append(f"- {msg.id} ({sender_label}): {snippet}")

        listing = "\n".join(lines)
        preview = (task_preview or "")[:MEMORY_TASK_PREVIEW_MAX_LENGTH]

        constraint_text = ""
        if at_most and at_most > 0:
            constraint_text = f"\nCONSTRAINT: Select at most {int(at_most)} messages that best match the criteria.\n"

        user_prompt = (
            "CANDIDATE MESSAGES (id (sender): snippet):\n"
            f"{listing}\n\n===\n\n"
            f"TASK PREVIEW:\n===\n\n{preview}\n\n===\n\n"
            f"CRITERIA:\n{criteria}\n\n"
            f"{constraint_text}"
            "IMPORTANT: Exclude messages that duplicate content already in the task preview.\n"
            "Return a JSON array of message IDs only."
        )

        # Use phase-aware complete method
        messages = [{"role": "user", "content": user_prompt}]

        # Remove parameters that are not needed for the complete() method
        kwargs.pop("preprocessed", None)
        kwargs.pop("llm_service", None)
        kwargs.pop("person_id", None)

        # person_name is already in kwargs if provided, so we don't need to extract and re-add it

        import json

        result = await self.complete(
            messages=messages,
            model=model,
            api_key_id=api_key_id,
            service_name=service_name,
            execution_phase=ExecutionPhase.MEMORY_SELECTION,
            temperature=0,
            max_tokens=MEMORY_SELECTION_MAX_TOKENS,
            **kwargs,
        )

        # Parse MemorySelectionOutput from text response
        ids = []
        if result.text:
            try:
                # Try to parse as MemorySelectionOutput JSON if it's structured
                parsed = json.loads(result.text)
                if isinstance(parsed, dict) and "message_ids" in parsed:
                    ids = parsed["message_ids"]
                elif isinstance(parsed, list):
                    ids = parsed
                else:
                    self.log_warning(f"Unexpected memory selection format: {type(parsed)}")
                    ids = []
            except (json.JSONDecodeError, ValueError) as e:
                self.log_warning(f"Failed to parse memory selection JSON: {e}")
                ids = []
        else:
            self.log_warning("Memory selection result.text is empty")

        output = MemorySelectionOutput(message_ids=ids)
        self.log_info(
            f"Memory selection extracted {len(output.message_ids)} message IDs from candidates: {[msg.id for msg in candidate_messages[:3]]}"
        )
        return output

    async def complete_decision(
        self,
        prompt: str,
        context: dict[str, Any],
        model: str,
        api_key_id: str,
        service_name: str,
        **kwargs,
    ) -> DecisionOutput:
        """Direct decision evaluation without domain adapter."""
        import json
        import re

        from dipeo.config.llm import DECISION_EVALUATION_MAX_TOKENS
        from dipeo.diagram_generated.enums import ExecutionPhase

        if not prompt or not prompt.strip():
            return False, {"error": "Empty prompt"}

        # Build complete prompt with context
        complete_prompt = prompt
        if context:
            # Extract content to evaluate from context
            content_to_evaluate = None

            if "default" in context:
                content_to_evaluate = context["default"]
            elif "generated_output" in context:
                content_to_evaluate = context["generated_output"]
            else:
                # Filter out execution context keys
                context_keys = {
                    "current_index",
                    "last_index",
                    "iteration_count",
                    "loop_index",
                    "execution_count",
                    "node_execution_count",
                }
                filtered = {
                    k: v
                    for k, v in context.items()
                    if not k.startswith("branch[")
                    and not k.endswith("_last_increment_at")
                    and k not in context_keys
                }
                content_to_evaluate = filtered if filtered else context

            # Add content to prompt
            if content_to_evaluate is not None:
                if isinstance(content_to_evaluate, str):
                    complete_prompt = f"{prompt}\n\n--- Content to Evaluate ---\n{content_to_evaluate}\n--- End of Content ---"
                else:
                    try:
                        content_json = json.dumps(content_to_evaluate, indent=2)
                        complete_prompt = f"{prompt}\n\n--- Content to Evaluate ---\n{content_json}\n--- End of Content ---"
                    except (TypeError, ValueError):
                        complete_prompt = f"{prompt}\n\n--- Content to Evaluate ---\n{content_to_evaluate!s}\n--- End of Content ---"

        # Use phase-aware complete method
        messages = [{"role": "user", "content": complete_prompt}]

        # Remove any unexpected parameters
        for key in list(kwargs.keys()):
            kwargs.pop(key, None)

        result = await self.complete(
            messages=messages,
            model=model,
            api_key_id=api_key_id,
            service_name=service_name,
            execution_phase=ExecutionPhase.DECISION_EVALUATION,
            temperature=0,
            max_tokens=DECISION_EVALUATION_MAX_TOKENS,
            **kwargs,
        )

        # Parse DecisionOutput from text response
        response_text = result.text if hasattr(result, "text") else ""
        decision = self._parse_text_decision(response_text)

        output = DecisionOutput(decision=decision)
        self.log_debug(f"Decision evaluation result: {output.decision}")
        return output

    def _parse_text_decision(self, response_text: str) -> bool:
        """Parse a binary decision from text response."""
        import json
        import re

        if not response_text:
            return False

        response_stripped = response_text.strip()

        # Try to parse as JSON first
        if response_stripped.startswith("{") and response_stripped.endswith("}"):
            try:
                json_data = json.loads(response_stripped)
                if "decision" in json_data:
                    return bool(json_data["decision"])
            except (json.JSONDecodeError, ValueError):
                pass

        # Clean and check for keywords
        response_lower = response_text.lower().strip()
        response_lower = re.sub(r"[*_`#\[\]()]", "", response_lower)

        # Check start of response
        if response_lower.startswith("yes"):
            return True
        if response_lower.startswith("no"):
            return False

        # Keyword matching
        affirmative_keywords = [
            "yes",
            "true",
            "valid",
            "approved",
            "approve",
            "accept",
            "accepted",
            "correct",
            "pass",
            "passed",
            "good",
            "ok",
            "okay",
            "proceed",
            "continue",
            "affirmative",
            "positive",
            "success",
            "successful",
        ]

        negative_keywords = [
            "no",
            "false",
            "invalid",
            "rejected",
            "reject",
            "deny",
            "denied",
            "incorrect",
            "fail",
            "failed",
            "bad",
            "not ok",
            "not okay",
            "stop",
            "halt",
            "negative",
            "unsuccessful",
            "error",
            "wrong",
        ]

        affirmative_count = sum(1 for keyword in affirmative_keywords if keyword in response_lower)
        negative_count = sum(1 for keyword in negative_keywords if keyword in response_lower)

        if affirmative_count > negative_count:
            return True
        elif negative_count > affirmative_count:
            return False

        self.log_warning(f"Ambiguous decision response: {response_text[:100]}...")
        return False

    async def complete(
        self,
        messages: list[dict[str, str]],
        model: str,
        api_key_id: str,
        service_name: str | None = None,
        **kwargs,
    ) -> ChatResult:
        try:
            if messages is None:
                messages = []

            execution_phase = kwargs.pop("execution_phase", None)

            # Use the explicit service parameter if provided, otherwise infer from model
            if service_name:
                if hasattr(service_name, "value"):
                    service_name = service_name.value
                service_name = normalize_service_name(str(service_name))

            client = await self._get_client(service_name, model, api_key_id)

            # Filter out provider-specific parameters
            # person_name is only used by Claude Code for memory selection
            claude_code_specific = {"person_name"}

            client_kwargs = {k: v for k, v in kwargs.items() if k not in claude_code_specific}

            # Add person_name back only for Claude Code
            if service_name == "claude-code" and "person_name" in kwargs:
                client_kwargs["person_name"] = kwargs["person_name"]

            if execution_phase:
                client_kwargs["execution_phase"] = execution_phase
            else:
                from dipeo.diagram_generated.enums import ExecutionPhase

                client_kwargs["execution_phase"] = ExecutionPhase.DIRECT_EXECUTION

            response = await client.async_chat(messages=messages, **client_kwargs)
            if hasattr(self, "logger") and response:
                # Enhanced logging to properly display LLM responses
                if isinstance(response, LLMResponse):
                    if response.content:
                        response_text = str(response.content)[:500]  # Increased from 50 to 500
                    else:
                        response_text = f"<empty content> (structured_output: {response.structured_output is not None})"
                elif hasattr(response, "content"):
                    content = getattr(response, "content", None)
                    if content:
                        response_text = str(content)[:500]
                    else:
                        response_text = "<empty content attribute>"
                elif hasattr(response, "text"):
                    text = getattr(response, "text", None)
                    if text:
                        response_text = str(text)[:500]
                    else:
                        response_text = "<empty text attribute>"
                else:
                    response_text = (
                        f"<unexpected type: {type(response).__name__}> {str(response)[:500]}"
                    )

                self.log_debug(f"LLM response: {response_text}")

            if isinstance(response, LLMResponse):
                return self._convert_response_to_chat_result(response)
            elif isinstance(response, ChatResult):
                return response
            else:
                if hasattr(response, "content"):
                    content = response.content
                elif hasattr(response, "text"):
                    content = response.text
                else:
                    content = str(response)

                result = ChatResult(content=content)

                if hasattr(response, "prompt_tokens"):
                    result.prompt_tokens = response.prompt_tokens
                if hasattr(response, "completion_tokens"):
                    result.completion_tokens = response.completion_tokens
                if hasattr(response, "total_tokens"):
                    result.total_tokens = response.total_tokens

                return result

        except Exception as e:
            if hasattr(self, "logger"):
                self.log_error(f"Error in LLM completion: {e}")
            raise LLMServiceError(service=service_name, message=str(e)) from e

    async def validate_api_key(self, api_key_id: str, service: str | None = None) -> bool:
        """Validate an API key is functional."""
        try:
            # Get the actual API key
            api_key = await self.api_key_service.get_api_key(api_key_id)
            if not api_key:
                return False

            # If service not specified, try a simple test with OpenAI
            if not service:
                service = LLMServiceName.OPENAI.value

            # Try to create a client and test with a simple message
            client = await self._get_client(service, "gpt-4o-mini", api_key_id)
            test_response = await client.async_chat(
                messages=[{"role": "user", "content": "test"}], max_output_tokens=1
            )
            return test_response is not None
        except Exception:
            return False
