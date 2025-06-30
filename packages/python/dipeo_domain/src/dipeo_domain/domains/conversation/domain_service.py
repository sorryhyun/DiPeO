"""Domain service for conversation management that encapsulates LLM interactions."""

from typing import TYPE_CHECKING, Any

from dipeo_domain.models import (
    DomainDiagram,
    DomainNode,
    DomainPerson,
    NodeOutput,
    TokenUsage,
)

if TYPE_CHECKING:
    from dipeo_core import SupportsAPIKey, SupportsLLM, SupportsMemory


class ConversationDomainService:
    """High-level domain service that manages conversations with LLMs."""

    def __init__(
        self,
        llm_service: "SupportsLLM",
        api_key_service: "SupportsAPIKey",
        conversation_service: "SupportsMemory",
    ):
        """Initialize with required infrastructure services."""
        self._llm = llm_service
        self._api_keys = api_key_service
        self._conversations = conversation_service

    async def execute_person_job(
        self,
        node: DomainNode,
        execution_id: str,
        exec_count: int,
        inputs: dict[str, Any],
        diagram: DomainDiagram,
    ) -> NodeOutput:
        """Execute a person job node with full conversation management."""
        data = node.data or {}

        # Extract node configuration
        person_id: str | None = data.get("personId") or data.get("person")
        first_only_prompt: str = data.get("firstOnlyPrompt", "")
        default_prompt: str = data.get("defaultPrompt", "")
        is_judge: bool = "judge" in data.get("label", "").lower()

        if not person_id:
            return NodeOutput(
                value={"default": ""}, metadata={"error": "No personId specified"}
            )

        # Get person configuration
        person_obj = self.find_person_by_id(diagram.persons, person_id)
        person_config = self.get_person_config(person_obj)

        # Handle forgetting mode from person's memory config
        memory_config = (
            getattr(person_obj, "memory_config", None) if person_obj else None
        )
        if memory_config:
            forget_mode = getattr(memory_config, "forget_mode", None)
            if forget_mode == "on_every_turn" and exec_count > 1:
                self._conversations.forget_own_messages_for_person(
                    person_id, execution_id
                )

        # Handle conversation inputs
        self._handle_conversation_inputs(
            inputs=inputs,
            person_id=person_id,
            execution_id=execution_id,
            node_id=node.id,
        )

        # Prepare prompt
        prompt = self._prepare_prompt(
            exec_count, first_only_prompt, default_prompt, inputs
        )

        # Handle judge aggregation
        if is_judge:
            judge_context = self._prepare_judge_context(
                node, diagram, execution_id, inputs
            )
            if judge_context:
                prompt = judge_context + (
                    prompt
                    or "Based on the above arguments, judge which panel is more reasonable."
                )

        # Add prompt as user message if present
        if prompt:
            self._conversations.add_message_to_conversation(
                person_id=person_id,
                execution_id=execution_id,
                role="user",
                content=prompt,
                current_person_id="user",
                node_id=node.id,
            )

        # Get conversation history
        conversation = self._conversations.get_conversation_history(person_id)

        # Build messages list with system prompt
        messages = []
        if person_config.get("system_prompt"):
            messages.append(
                {"role": "system", "content": person_config["system_prompt"]}
            )
        messages.extend(conversation)

        # Prepare LLM parameters
        llm_params = self._extract_llm_params(person_config)

        # Call LLM with conversation
        chat_result = await self._llm.complete(
            messages=messages,
            model=person_config["model"],
            api_key_id=person_config["api_key_id"],
            **llm_params,
        )

        response_text: str = chat_result.text
        token_usage: TokenUsage | None = chat_result.token_usage

        # Add response to memory
        self._conversations.add_message_to_conversation(
            person_id=person_id,
            execution_id=execution_id,
            role="assistant",
            content=response_text,
            current_person_id=person_id,
            node_id=node.id,
        )

        # Prepare output values
        output_values: dict[str, Any] = {"default": response_text}

        # Check if we need to output conversation state
        if self._should_output_conversation(node, diagram):
            output_values["conversation"] = (
                self._conversations.get_conversation_history(person_id)
            )

        # Return node output with all metadata
        return NodeOutput(
            value=output_values,
            metadata={
                "model": person_config["model"],
                "tokens_used": token_usage.total if token_usage else 0,
                "tokenUsage": {
                    "input": token_usage.input if token_usage else 0,
                    "output": token_usage.output if token_usage else 0,
                    "total": token_usage.total if token_usage else 0,
                    "cached": token_usage.cached if token_usage else 0,
                },
                "token_usage": token_usage,
            },
        )

    def get_person_config(self, person: DomainPerson | None) -> dict[str, Any]:
        """Extract LLM configuration from a person object."""
        if not person:
            return self._default_person_config()

        # Check if person has the new llmConfig structure
        llm_config = getattr(person, "llm_config", None) or getattr(
            person, "llmConfig", None
        )
        if llm_config:
            return self._extract_llm_config(llm_config)

        # Fallback to legacy fields
        return self._extract_legacy_config(person)

    def find_person_by_id(
        self, persons: list[DomainPerson], person_id: str
    ) -> DomainPerson | None:
        """Find a person by ID in a list of persons."""
        return next((p for p in persons if p.id == person_id), None)

    def _prepare_prompt(
        self,
        exec_count: int,
        first_only_prompt: str,
        default_prompt: str,
        inputs: dict[str, Any],
    ) -> str:
        """Prepare the prompt based on execution count and templates."""
        if exec_count == 1 and first_only_prompt:
            # Convert {{var}} to {var} for Python format()
            prompt_template = first_only_prompt.replace("{{", "{").replace("}}", "}")
            return prompt_template.format(**inputs)
        return default_prompt

    def _handle_conversation_inputs(
        self,
        inputs: dict[str, Any],
        person_id: str,
        execution_id: str,
        node_id: str,
    ) -> None:
        """Handle conversation inputs from upstream nodes."""
        if "conversation" not in inputs:
            return

        upstream_conv = inputs["conversation"]
        if not isinstance(upstream_conv, list) or not upstream_conv:
            return

        # Check if we're in a conversation loop
        our_messages_count = sum(
            1
            for msg in upstream_conv
            if msg.get("personId") == person_id and msg.get("role") == "assistant"
        )

        if our_messages_count > 0:
            # In a loop - extract last exchange from other persons
            last_other_msg = self._find_last_other_message(upstream_conv, person_id)
            if last_other_msg:
                self._conversations.add_message_to_conversation(
                    person_id=person_id,
                    execution_id=execution_id,
                    role="user",
                    content=last_other_msg.get("content", ""),
                    current_person_id=last_other_msg.get("personId", "unknown"),
                    node_id=node_id,
                )
        else:
            # Not in a loop - format upstream conversation as context
            context = self._format_upstream_context(upstream_conv)
            if context:
                self._conversations.add_message_to_conversation(
                    person_id=person_id,
                    execution_id=execution_id,
                    role="user",
                    content=context,
                    current_person_id="user",
                    node_id=node_id,
                )

    def _prepare_judge_context(
        self,
        node: DomainNode,
        diagram: DomainDiagram,
        execution_id: str,
        inputs: dict[str, Any],
    ) -> str:
        """Prepare debate context for judge nodes."""
        # First check if conversation data is available in inputs
        if "conversation" in inputs:
            context = self._format_conversation_from_inputs(
                inputs["conversation"], diagram
            )
            if context:
                return context

        # Fallback to memory-based approach
        return self._format_conversation_from_memory(node, diagram)

    def _should_output_conversation(
        self, node: DomainNode, diagram: DomainDiagram
    ) -> bool:
        """Check if node should output conversation state."""
        for edge in diagram.arrows:
            if edge.source.startswith(node.id + ":"):
                edge_data = (
                    edge.data if edge.data and isinstance(edge.data, dict) else {}
                )
                if edge_data.get("contentType") == "conversation_state":
                    return True
        return False

    def _default_person_config(self) -> dict[str, Any]:
        """Get default person configuration."""
        return {
            "service": "openai",
            "api_key_id": None,
            "model": "gpt-4.1-nano",
            "system_prompt": "",
            "temperature": None,
            "max_tokens": None,
            "top_p": None,
            "frequency_penalty": None,
            "presence_penalty": None,
        }

    def _extract_llm_config(self, llm_config: Any) -> dict[str, Any]:
        """Extract configuration from llm_config object."""
        return {
            "service": getattr(llm_config, "service", "openai"),
            "api_key_id": getattr(llm_config, "api_key_id", None)
            or getattr(llm_config, "apiKeyId", None),
            "model": getattr(llm_config, "model", "gpt-4.1-nano"),
            "system_prompt": getattr(llm_config, "system_prompt", None)
            or getattr(llm_config, "systemPrompt", ""),
            "temperature": getattr(llm_config, "temperature", None),
            "max_tokens": getattr(llm_config, "max_tokens", None)
            or getattr(llm_config, "maxTokens", None),
            "top_p": getattr(llm_config, "top_p", None)
            or getattr(llm_config, "topP", None),
            "frequency_penalty": getattr(llm_config, "frequency_penalty", None)
            or getattr(llm_config, "frequencyPenalty", None),
            "presence_penalty": getattr(llm_config, "presence_penalty", None)
            or getattr(llm_config, "presencePenalty", None),
        }

    def _extract_llm_params(self, person_config: dict[str, Any]) -> dict[str, Any]:
        """Extract LLM parameters from person config."""
        params = {}

        # Add parameters if specified
        for key in [
            "temperature",
            "max_tokens",
            "top_p",
            "frequency_penalty",
            "presence_penalty",
        ]:
            if person_config.get(key) is not None:
                params[key] = person_config[key]

        return params

    def _find_last_other_message(
        self, conversation: list[dict[str, Any]], person_id: str
    ) -> dict[str, Any] | None:
        """Find the last message from another person."""
        for msg in reversed(conversation):
            if msg.get("personId") != person_id and msg.get("role") == "assistant":
                return msg
        return None

    def _format_upstream_context(self, conversation: list[dict[str, Any]]) -> str:
        """Format upstream conversation as context."""
        last_exchange = []
        for msg in reversed(conversation):
            if msg.get("role") in ["user", "assistant"]:
                last_exchange.append(msg)
                if len(last_exchange) == 2:
                    break

        if not last_exchange:
            return ""

        context_parts = []
        for msg in reversed(last_exchange):
            role = "Input" if msg.get("role") == "user" else "Response"
            context_parts.append(f"{role}: {msg.get('content', '')}")

        return "\n".join(context_parts)

    def _format_conversation_from_inputs(
        self, conv_data: Any, diagram: DomainDiagram
    ) -> str:
        """Format conversation data from inputs for judge context."""
        if not isinstance(conv_data, list):
            return ""

        # Group messages by personId
        person_conversations = {}
        for msg in conv_data:
            person_id = msg.get("personId", "unknown")
            if person_id not in person_conversations:
                person_conversations[person_id] = []
            person_conversations[person_id].append(msg)

        # Format conversations by person
        debate_context_parts = []
        for person_id, messages in person_conversations.items():
            # Find the label for this person
            label = self._find_person_label(person_id, diagram)

            # Don't include judge panels in the context
            if "judge" not in label.lower():
                debate_context_parts.append(f"\n{label}:\n")
                # Show all non-system messages
                for msg in messages:
                    if msg.get("role") != "system":
                        role = "Input" if msg.get("role") == "user" else "Response"
                        content = msg.get("content", "")
                        debate_context_parts.append(f"{role}: {content}\n")

        if debate_context_parts:
            return (
                "Here are the arguments from different panels:\n"
                + "".join(debate_context_parts)
                + "\n\n"
            )
        return ""

    def _format_conversation_from_memory(
        self, node: DomainNode, diagram: DomainDiagram
    ) -> str:
        """Format conversation from memory for judge context."""
        debate_context_parts = []

        for other_node in diagram.nodes:
            if other_node.type != "person_job" or other_node.id == node.id:
                continue

            if not other_node.data:
                continue
            other_person_id = other_node.data.get("personId") or other_node.data.get(
                "person"
            )
            if not other_person_id:
                continue

            # Get conversation for the other person
            other_conv = self._conversations.get_conversation_history(other_person_id)

            # Filter out system messages
            debate_messages = [m for m in other_conv if m.get("role") != "system"]
            if not debate_messages:
                continue

            label = (
                other_node.data.get("label", other_node.id)
                if other_node.data
                else other_node.id
            )
            debate_context_parts.append(f"\n{label}:\n")

            for msg in debate_messages:
                role = "Input" if msg.get("role") == "user" else "Response"
                content = msg.get("content", "")
                debate_context_parts.append(f"{role}: {content}\n")

        if debate_context_parts:
            return (
                "Here are the arguments from different panels:\n"
                + "".join(debate_context_parts)
                + "\n\n"
            )
        return ""

    def _find_person_label(self, person_id: str, diagram: DomainDiagram) -> str:
        """Find the label for a person from the diagram nodes."""
        for node in diagram.nodes:
            if node.type == "person_job":
                data = node.data or {}
                node_person_id = data.get("person") or data.get("personId")
                if node_person_id == person_id:
                    return data.get("label", person_id)
        return person_id
