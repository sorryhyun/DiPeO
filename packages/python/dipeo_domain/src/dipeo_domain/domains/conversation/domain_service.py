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
        self.handle_conversation_inputs(
            inputs=inputs,
            person_id=person_id,
            execution_id=execution_id,
            node_id=node.id,
            node_label=data.get("label", node.id),
        )

        # Prepare prompt
        prompt = self.prepare_prompt(
            exec_count, first_only_prompt, default_prompt, inputs
        )

        # Handle judge aggregation
        if is_judge:
            judge_context = self.prepare_judge_context(
                node, diagram, execution_id, inputs
            )
            if judge_context:
                prompt = judge_context + (
                    prompt
                    or "Based on the above arguments, judge which panel is more reasonable."
                )

        # Add prompt as user message if present
        if prompt:
            self._conversations.add_message_to_conversation_with_tokens(
                sender_person_id="user",
                participant_person_ids=[person_id],
                content=prompt,
                execution_id=execution_id,
                node_id=node.id,
                node_label=data.get("label", node.id),
            )

        # Get updated conversation from memory service
        conversation = self._conversations.get_conversation_for_person(person_id)

        # Call LLM with conversation
        llm_params = {
            "service": person_config["service"],
            "api_key_id": person_config["api_key_id"],
            "model": person_config["model"],
            "messages": conversation,
        }

        # Add temperature if specified in person's memory config
        if person_config.get("temperature") is not None:
            llm_params["temperature"] = person_config["temperature"]

        llm_result = await self._llm.call_llm(**llm_params)

        response_text: str = llm_result.get("response", "")
        token_usage_obj = llm_result.get("token_usage")

        # Add response to memory
        self._conversations.add_message_to_conversation_with_tokens(
            sender_person_id=person_id,
            participant_person_ids=[person_id],
            content=response_text,
            execution_id=execution_id,
            node_id=node.id,
            node_label=data.get("label", node.id),
            input_tokens=getattr(token_usage_obj, "input", 0) if token_usage_obj else 0,
            output_tokens=getattr(token_usage_obj, "output", 0)
            if token_usage_obj
            else 0,
            cached_tokens=getattr(token_usage_obj, "cached", 0)
            if token_usage_obj and hasattr(token_usage_obj, "cached")
            else 0,
        )

        # Prepare output values
        output_values = {"default": response_text}

        # Check if we need to output conversation state
        for edge in diagram.arrows:
            if edge.source.startswith(node.id + ":"):
                edge_data = (
                    edge.data if edge.data and isinstance(edge.data, dict) else {}
                )
                if edge_data.get("contentType") == "conversation_state":
                    # Get full conversation history for output
                    conv_history = self._conversations.get_conversation_for_person(
                        person_id
                    )
                    output_values["conversation"] = conv_history
                    break

        # Prepare token usage metadata
        token_usage_metadata = {}
        token_usage_domain = None

        if token_usage_obj and hasattr(token_usage_obj, "__dict__"):
            token_usage_metadata = {
                "input": getattr(token_usage_obj, "input", 0),
                "output": getattr(token_usage_obj, "output", 0),
                "total": getattr(token_usage_obj, "total", 0),
            }
            if hasattr(token_usage_obj, "cached"):
                token_usage_metadata["cached"] = token_usage_obj.cached

            # Create domain token usage object
            token_usage_domain = TokenUsage(**token_usage_metadata)

        # Return node output with all metadata
        return NodeOutput(
            value=output_values,
            metadata={
                "model": person_config["model"],
                "tokens_used": token_usage_metadata.get("total", 0),
                "tokenUsage": token_usage_metadata,
                "token_usage": token_usage_domain,
            },
        )

    def get_person_config(self, person: DomainPerson | None) -> dict[str, Any]:
        """Extract LLM configuration from a person object."""
        if not person:
            return {
                "service": "openai",
                "api_key_id": None,
                "model": "gpt-4.1-nano",
                "system_prompt": "",
                "temperature": None,
            }

        # Extract memory config temperature if available
        memory_config = getattr(person, "memory_config", None)
        temperature = None
        if memory_config:
            temperature = getattr(memory_config, "temperature", None)

        return {
            "service": getattr(person, "service", "openai"),
            "api_key_id": getattr(person, "api_key_id", None)
            or getattr(person, "apiKeyId", None),
            "model": getattr(person, "model", "gpt-4.1-nano"),
            "system_prompt": getattr(person, "system_prompt", None)
            or getattr(person, "systemPrompt", ""),
            "temperature": temperature,
        }

    def find_person_by_id(
        self, persons: list[DomainPerson], person_id: str
    ) -> DomainPerson | None:
        """Find a person by ID in a list of persons."""
        return next((p for p in persons if p.id == person_id), None)

    def prepare_prompt(
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

    def handle_conversation_inputs(
        self,
        inputs: dict[str, Any],
        person_id: str,
        execution_id: str,
        node_id: str,
        node_label: str,
    ) -> None:
        """Handle conversation inputs from upstream nodes (multi-person conversation loops)."""
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
            last_other_msg = None
            for i in range(len(upstream_conv) - 1, -1, -1):
                msg = upstream_conv[i]
                if msg.get("personId") != person_id and msg.get("role") == "assistant":
                    last_other_msg = msg
                    break

            if last_other_msg:
                # Add as a message to memory service
                self._conversations.add_message_to_conversation_with_tokens(
                    sender_person_id=last_other_msg.get("personId", "unknown"),
                    participant_person_ids=[person_id],
                    content=last_other_msg.get("content", ""),
                    execution_id=execution_id,
                    node_id=node_id,
                    node_label=node_label,
                )
        else:
            # Not in a loop - format upstream conversation as context
            last_exchange = []
            for msg in reversed(upstream_conv):
                if msg.get("role") in ["user", "assistant"]:
                    last_exchange.append(msg)
                    if len(last_exchange) == 2:
                        break

            if last_exchange:
                context_parts = []
                for msg in reversed(last_exchange):
                    role = "Input" if msg.get("role") == "user" else "Response"
                    context_parts.append(f"{role}: {msg.get('content', '')}")

                upstream_text = "\n".join(context_parts)
                # Add as a user message
                self._conversations.add_message_to_conversation_with_tokens(
                    sender_person_id="user",
                    participant_person_ids=[person_id],
                    content=upstream_text,
                    execution_id=execution_id,
                    node_id=node_id,
                    node_label=node_label,
                )

    def prepare_judge_context(
        self,
        node: DomainNode,
        diagram: DomainDiagram,
        execution_id: str,
        inputs: dict[str, Any],
    ) -> str:
        """Prepare debate context for judge nodes by aggregating conversations from inputs or memory."""
        debate_context_parts = []

        # First check if conversation data is available in inputs (from edges)
        if "conversation" in inputs:
            conv_data = inputs["conversation"]
            if isinstance(conv_data, list):
                # Group messages by personId
                person_conversations = {}
                for msg in conv_data:
                    person_id = msg.get("personId", "unknown")
                    if person_id not in person_conversations:
                        person_conversations[person_id] = []
                    person_conversations[person_id].append(msg)

                # Format conversations by person
                for person_id, messages in person_conversations.items():
                    # Find the label for this person
                    label = person_id
                    for other_node in diagram.nodes:
                        if other_node.type == "person_job":
                            other_data = other_node.data or {}
                            other_person_id = other_data.get(
                                "person"
                            ) or other_data.get("personId")
                            if other_person_id == person_id:
                                label = other_data.get("label", person_id)
                                break

                    # Don't include judge panels in the context
                    if "judge" not in label.lower():
                        debate_context_parts.append(f"\n{label}:\n")
                        # Show all non-system messages
                        for msg in messages:
                            if msg.get("role") != "system":
                                role = (
                                    "Input" if msg.get("role") == "user" else "Response"
                                )
                                content = msg.get("content", "")
                                debate_context_parts.append(f"{role}: {content}\n")

                if debate_context_parts:
                    return (
                        "Here are the arguments from different panels:\n"
                        + "".join(debate_context_parts)
                        + "\n\n"
                    )

        # Fallback to memory-based approach if no conversation in inputs
        for other_node in diagram.nodes:
            if other_node.type != "person_job" or other_node.id == node.id:
                continue

            other_person_id = (
                other_node.data.get("personId") if other_node.data else None
            )
            if not other_person_id:
                continue

            # Get conversation for the other person
            other_conv = self._conversations.get_conversation_for_person(
                other_person_id
            )

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
