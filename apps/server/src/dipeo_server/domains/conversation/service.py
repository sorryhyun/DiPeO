import uuid
from collections import OrderedDict
from datetime import datetime
from typing import Any, Dict, List, Optional, TYPE_CHECKING

from dipeo_domain.models import DomainPerson, DomainNode, DomainDiagram

if TYPE_CHECKING:
    from dipeo_server.domains.llm.services import LLMService

from .conversation import PersonConversation, Message

class ConversationService:
    """Service for managing conversations between persons (LLM agents)."""

    def __init__(self, redis_url: Optional[str] = None, message_store=None):
        self.person_conversations: Dict[str, PersonConversation] = {}
        self.all_messages: OrderedDict[str, Message] = OrderedDict()
        self.execution_metadata: Dict[str, Dict[str, Any]] = {}
        self.message_store = message_store
        self._pending_persistence: Dict[str, List[Message]] = {}

        self.MAX_GLOBAL_MESSAGES = 10000

    def _store_message(self, message: Message) -> None:
        self.all_messages[message.id] = message

        while len(self.all_messages) > self.MAX_GLOBAL_MESSAGES:
            self.all_messages.popitem(last=False)

    def _get_message(self, message_id: str) -> Optional[Message]:
        return self.all_messages.get(message_id)

    def get_or_create_person_conversation(self, person_id: str) -> PersonConversation:
        if person_id not in self.person_conversations:
            self.person_conversations[person_id] = PersonConversation(person_id=person_id)
        return self.person_conversations[person_id]

    def add_message_to_conversation(
            self,
            content: str,
            sender_person_id: str,
            execution_id: str,
            participant_person_ids: List[str],
            role: str = "assistant",
            node_id: Optional[str] = None,
            node_label: Optional[str] = None,
            token_count: Optional[int] = None,
            input_tokens: Optional[int] = None,
            output_tokens: Optional[int] = None,
            cached_tokens: Optional[int] = None,
    ) -> Message:
        """Create and add message to conversation."""
        message = Message(
            id=str(uuid.uuid4()),
            role=role,
            content=content,
            timestamp=datetime.now(),
            sender_person_id=sender_person_id,
            execution_id=execution_id,
            node_id=node_id,
            node_label=node_label,
            token_count=token_count,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            cached_tokens=cached_tokens,
        )

        self._store_message(message)

        for person_id in participant_person_ids:
            person_conversation = self.get_or_create_person_conversation(person_id)
            person_conversation.add_message(message)

        # Queue for deferred persistence
        if execution_id not in self._pending_persistence:
            self._pending_persistence[execution_id] = []
        self._pending_persistence[execution_id].append(message)

        if execution_id not in self.execution_metadata:
            self.execution_metadata[execution_id] = {
                "start_time": datetime.now(),
                "message_count": 0,
                "total_tokens": 0,
                "input_tokens": 0,
                "output_tokens": 0,
                "cached_tokens": 0,
            }

        metadata = self.execution_metadata[execution_id]
        metadata["message_count"] += 1
        if token_count:
            metadata["total_tokens"] += token_count
        if input_tokens:
            metadata["input_tokens"] += input_tokens
        if output_tokens:
            metadata["output_tokens"] += output_tokens
        if cached_tokens:
            metadata["cached_tokens"] += cached_tokens

        return message

    def forget_for_person(
            self, person_id: str, execution_id: Optional[str] = None
    ) -> None:
        """Make a person forget messages."""
        person_conversation = self.get_or_create_person_conversation(person_id)

        if execution_id:
            person_conversation.forget_messages_from_execution(execution_id)
        else:
            for message in person_conversation.messages:
                person_conversation.forgotten_message_ids.add(message.id)

    def forget_own_messages_for_person(
            self, person_id: str, execution_id: Optional[str] = None
    ) -> None:
        """Make a person forget only their own messages."""
        person_conversation = self.get_or_create_person_conversation(person_id)

        if execution_id:
            person_conversation.forget_own_messages_from_execution(execution_id)
        else:
            person_conversation.forget_own_messages()

    def get_conversation_for_person(self, person_id: str) -> List[Dict[str, Any]]:
        """Get all visible messages for a person."""
        person_conversation = self.get_or_create_person_conversation(person_id)
        return person_conversation.get_visible_messages(person_id)

    def get_conversation_for_agent(self, person_id: str, execution_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get all visible messages for an agent - alias for get_conversation_for_person."""
        return self.get_conversation_for_person(person_id)

    def get_execution_metadata(self, execution_id: str) -> Optional[Dict[str, Any]]:
        """Get metadata for an execution."""
        return self.execution_metadata.get(execution_id)

    def cleanup_old_executions(self, max_age_hours: int = 24) -> int:
        """Clean up old execution metadata and return count of removed executions."""
        current_time = datetime.now()
        removed_count = 0

        execution_ids_to_remove = []
        for exec_id, metadata in self.execution_metadata.items():
            start_time = metadata.get("start_time")
            if (
                    start_time
                    and (current_time - start_time).total_seconds() > max_age_hours * 3600
            ):
                execution_ids_to_remove.append(exec_id)

        for exec_id in execution_ids_to_remove:
            del self.execution_metadata[exec_id]
            removed_count += 1

        return removed_count

    def get_conversation_stats(self) -> Dict[str, Any]:
        """Get statistics about conversation usage."""
        return {
            "total_messages": len(self.all_messages),
            "active_persons": len(self.person_conversations),
            "active_executions": len(self.execution_metadata),
            "person_message_counts": {
                person_id: len(conversation.messages)
                for person_id, conversation in self.person_conversations.items()
            },
        }

    def clear_all_conversations(self) -> None:
        """Clear all conversation history for all persons."""
        self.person_conversations.clear()
        self.all_messages.clear()
        self.execution_metadata.clear()
        self._pending_persistence.clear()

    async def persist_execution_conversations(self, execution_id: str) -> None:
        """Persist all pending conversations for an execution."""
        if execution_id in self._pending_persistence:
            messages = self._pending_persistence.pop(execution_id)
            if self.message_store and messages:
                # Group messages by node_id for batch storage
                messages_by_node: Dict[str, List[Message]] = {}
                for msg in messages:
                    if msg.node_id:
                        if msg.node_id not in messages_by_node:
                            messages_by_node[msg.node_id] = []
                        messages_by_node[msg.node_id].append(msg)

                # Store messages for each node
                for node_id, node_messages in messages_by_node.items():
                    conversation = [msg.to_dict() for msg in node_messages]
                    await self.message_store.store_message(
                        execution_id=execution_id,
                        node_id=node_id,
                        content={"conversation": conversation},
                        person_id=node_messages[0].sender_person_id,
                        token_count=sum(msg.token_count or 0 for msg in node_messages),
                    )

    # Person configuration methods (from PersonService)
    def get_person_config(self, person: Optional[DomainPerson]) -> Dict[str, Any]:
        """Extract LLM configuration from a person object."""
        if not person:
            return {
                "service": "openai",
                "api_key_id": None,
                "model": "gpt-4.1-nano",
                "system_prompt": ""
            }

        return {
            "service": getattr(person, "service", "openai"),
            "api_key_id": getattr(person, "api_key_id", None) or getattr(person, "apiKeyId", None),
            "model": getattr(person, "model", "gpt-4.1-nano"),
            "system_prompt": getattr(person, "system_prompt", None) or getattr(person, "systemPrompt", "")
        }

    def find_person_by_id(self, persons: List[DomainPerson], person_id: str) -> Optional[DomainPerson]:
        """Find a person by ID in a list of persons."""
        return next((p for p in persons if p.id == person_id), None)

    def prepare_prompt(
            self,
            exec_count: int,
            first_only_prompt: str,
            default_prompt: str,
            inputs: Dict[str, Any]
    ) -> str:
        """Prepare the prompt based on execution count and templates."""
        if exec_count == 1 and first_only_prompt:
            # Convert {{var}} to {var} for Python format()
            prompt_template = first_only_prompt.replace("{{", "{").replace("}}", "}")
            return prompt_template.format(**inputs)
        return default_prompt

    def handle_conversation_inputs(
            self,
            inputs: Dict[str, Any],
            person_id: str,
            execution_id: str,
            node_id: str,
            node_label: str
    ) -> None:
        """Handle conversation inputs from upstream nodes (multi-person conversation loops)."""
        if "conversation" not in inputs:
            return

        upstream_conv = inputs["conversation"]
        if not isinstance(upstream_conv, list) or not upstream_conv:
            return

        # Check if we're in a conversation loop
        our_messages_count = sum(
            1 for msg in upstream_conv
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
                self.add_message_to_conversation(
                    sender_person_id=last_other_msg.get('personId', 'unknown'),
                    participant_person_ids=[person_id],
                    content=last_other_msg.get('content', ''),
                    execution_id=execution_id,
                    node_id=node_id,
                    node_label=node_label
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
                self.add_message_to_conversation(
                    sender_person_id="user",
                    participant_person_ids=[person_id],
                    content=upstream_text,
                    execution_id=execution_id,
                    node_id=node_id,
                    node_label=node_label
                )

    def prepare_judge_context(
            self,
            node: DomainNode,
            diagram: DomainDiagram,
            execution_id: str
    ) -> str:
        """Prepare debate context for judge nodes by aggregating conversations from other person_job nodes."""
        debate_context_parts = []

        for other_node in diagram.nodes:
            if other_node.type != "person_job" or other_node.id == node.id:
                continue

            other_person_id = other_node.data.get("personId") if other_node.data else None
            if not other_person_id:
                continue

            # Get conversation for the other person
            other_conv = self.get_conversation_for_person(other_person_id)

            # Filter out system messages
            debate_messages = [m for m in other_conv if m.get("role") != "system"]
            if not debate_messages:
                continue

            label = other_node.data.get("label", other_node.id) if other_node.data else other_node.id
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

    async def execute_person_job(
            self,
            node: DomainNode,
            execution_id: str,
            exec_count: int,
            inputs: Dict[str, Any],
            diagram: DomainDiagram,
            llm_service: "LLMService"
    ) -> Dict[str, Any]:
        """Execute a person_job node - orchestrate the entire conversational flow."""
        data = node.data or {}

        # Extract node configuration
        person_id: Optional[str] = data.get("personId") or data.get("person")
        first_only_prompt: str = data.get("firstOnlyPrompt", "")
        default_prompt: str = data.get("defaultPrompt", "")
        forgetting_mode: Optional[str] = data.get("forgettingMode")
        is_judge: bool = "judge" in data.get("label", "").lower()

        if not person_id:
            return {
                "output_values": {},
                "metadata": {"error": "No personId specified"}
            }

        # Get person configuration
        person_obj = self.find_person_by_id(diagram.persons, person_id)
        person_config = self.get_person_config(person_obj)

        # Handle forgetting mode
        if forgetting_mode == "on_every_turn" and exec_count > 1:
            # Forget messages from previous turns
            self.forget_own_messages_for_person(person_id, execution_id)

        # Handle conversation inputs
        self.handle_conversation_inputs(
            inputs=inputs,
            person_id=person_id,
            execution_id=execution_id,
            node_id=node.id,
            node_label=data.get('label', node.id)
        )

        # Prepare prompt
        prompt = self.prepare_prompt(
            exec_count, first_only_prompt, default_prompt, inputs
        )

        # Handle judge aggregation
        if is_judge:
            judge_context = self.prepare_judge_context(node, diagram, execution_id)
            if judge_context:
                prompt = judge_context + (
                        prompt or "Based on the above arguments, judge which panel is more reasonable."
                )

        # Add prompt as user message if present
        if prompt:
            self.add_message_to_conversation(
                sender_person_id="user",
                participant_person_ids=[person_id],
                content=prompt,
                execution_id=execution_id,
                node_id=node.id,
                node_label=data.get('label', node.id)
            )

        # Get updated conversation from memory service
        conversation = self.get_conversation_for_person(person_id)

        # Call LLM with conversation
        llm_result = await llm_service.call_llm(
            service=person_config["service"],
            api_key_id=person_config["api_key_id"],
            model=person_config["model"],
            messages=conversation,
        )

        response_text: str = llm_result.get("response", "")
        token_usage_obj = llm_result.get("token_usage")

        # Add response to memory
        self.add_message_to_conversation(
            sender_person_id=person_id,
            participant_person_ids=[person_id],
            content=response_text,
            execution_id=execution_id,
            node_id=node.id,
            node_label=data.get('label', node.id),
            input_tokens=getattr(token_usage_obj, "input", 0) if token_usage_obj else 0,
            output_tokens=getattr(token_usage_obj, "output", 0) if token_usage_obj else 0,
            cached_tokens=getattr(token_usage_obj, "cached", 0) if token_usage_obj and hasattr(token_usage_obj,
                                                                                               "cached") else 0
        )

        # Prepare output values
        output_values = {"default": response_text}

        # Check if we need to output conversation state
        for edge in diagram.arrows:
            if edge.source.startswith(node.id + ":"):
                edge_data = edge.data if edge.data and isinstance(edge.data, dict) else {}
                if edge_data.get("contentType") == "conversation_state":
                    # Get full conversation history for output
                    conv_history = self.get_conversation_for_person(person_id)
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

            # Create domain token usage object for context
            from dipeo_domain import TokenUsage as DomainTokenUsage
            token_usage_domain = DomainTokenUsage(**token_usage_metadata)

        return {
            "output_values": output_values,
            "metadata": {
                "model": person_config["model"],
                "tokens_used": token_usage_metadata.get("total", 0),
                "tokenUsage": token_usage_metadata
            },
            "token_usage": token_usage_domain
        }