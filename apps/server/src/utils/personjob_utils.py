
import logging
from typing import Any, Dict, List, Tuple, Optional
from datetime import datetime
from collections import Counter

from ..services.memory_service import MemoryService
from ..services.llm_service import LLMService
from .resolve_utils import render_prompt
from .output_processor import OutputProcessor

logger = logging.getLogger(__name__)


async def execute_personjob(
        node: dict,
        person: dict,
        vars_map: Dict[str, Any],
        incoming_arrows: List[dict],
        counts: Counter,
        context: Dict[str, Any],
        memory_service: MemoryService,
        llm_service: LLMService,
        execution_id: str,
        arrow_src_fn,  # Function to get edge source
        send_status_update_fn,  # Callback for status updates
        get_all_person_ids_fn  # Function to get all person IDs
) -> Tuple[Any, float]:
    """Execute person job node."""
    data = node.get("data", {})
    person_id = data.get("personId") or data.get("agent")
    iteration = counts[node["id"]]

    # Handle memory forget mode (separate from context cleaning)
    forget_mode = data.get("memoryForget") or data.get("memory", "none")
    if forget_mode == "all":
        memory_service.forget_for_person(person_id)
    elif forget_mode == "current_execution":
        memory_service.forget_for_person(person_id, execution_id)

    # Handle context cleaning rule
    if data.get("contextCleaningRule") == "on_every_turn":
        # Clear this person's own conversation history on every turn
        memory_service.forget_for_person(person_id, execution_id)
        own_conversation_history = []
    else:
        # Preserve own conversation history
        own_conversation_history = memory_service.get_conversation_history(person_id)

    # Process incoming arrows to extract conversation states and other inputs
    incoming_conversation = []
    preamble_parts = []

    for e in incoming_arrows:
        src_id = arrow_src_fn(e)
        if not src_id:
            continue

        src_value = context.get(src_id)
        if src_value is None:
            continue

        content_type = e.get("data", {}).get("contentType", "raw_text")

        if content_type == "conversation_state":
            # Extract conversation history from incoming arrow
            if OutputProcessor.is_personjob_output(src_value):
                incoming_conversation.extend(OutputProcessor.extract_conversation_history(src_value))
            elif isinstance(src_value, list) and all(
                    isinstance(msg, dict) and 'role' in msg and 'content' in msg for msg in src_value):
                incoming_conversation.extend(src_value)
            else:
                # Fallback: treat as a user message
                incoming_conversation.append({"role": "user", "content": str(src_value)})

        elif content_type in {"file", "whole"}:
            # Add file/whole content to preamble
            extracted_value = OutputProcessor.extract_value(src_value)
            preamble_parts.append(str(extracted_value))

    # Choose the appropriate prompt template
    first_prompt = data.get("firstOnlyPrompt") or data.get("first_prompt")
    default_prompt = data.get("defaultPrompt") or data.get("prompt")
    template = (
        first_prompt if iteration == 1 and first_prompt else default_prompt
    )

    logger.debug(f"[PersonJob {person_id}] Iteration: {iteration}, vars_map: {vars_map}")

    # Render the prompt with variables
    body = render_prompt(template, vars_map)

    # Build the complete message list
    messages = []

    # 1. Start with incoming conversation state (from other nodes)
    if incoming_conversation:
        messages.extend(incoming_conversation)

    # 2. Add own conversation history (if not cleaned)
    elif own_conversation_history:  # Only if no incoming conversation
        messages.extend(own_conversation_history)

    # 3. Add preamble content if any
    if preamble_parts and body.strip():
        # Combine preamble with body
        full_prompt = "\n\n".join(preamble_parts + [body])
        messages.append({"role": "user", "content": full_prompt})
    elif body.strip():
        # Just the body
        messages.append({"role": "user", "content": body})

    # If no messages and no body, create a default message
    if not messages and not body.strip():
        messages.append({"role": "user", "content": "Continue the conversation."})

    # Prepare for LLM call
    prompt = body if not preamble_parts else "\n\n".join(preamble_parts + [body])

    logger.debug(f"[PersonJob {person_id}] Prompt: {prompt}")
    logger.debug(f"[PersonJob {person_id}] Total messages: {len(messages)}")
    logger.debug(f"[PersonJob {person_id}] Incoming conversation: {len(incoming_conversation)} messages")
    logger.debug(f"[PersonJob {person_id}] Own history: {len(own_conversation_history)} messages")

    # Get model configuration
    model_name = person.get("modelName") or person.get("model")
    service = person.get("service")
    api_key_id = person.get("apiKeyId")
    # temperature = person.get("temperature", 0.7)

    # Auto-detect service if not specified
    if not service and model_name:
        if "gpt" in model_name.lower():
            service = "chatgpt"
            if not api_key_id:
                api_key_id = await _find_default_api_key(service)

    # Handle specific model naming
    if model_name == "gpt-4.1-nano":
        model_name = "gpt-4.1-nano-2025-04-14"

    # Add user message to memory (if there was actual user content)
    if body.strip():
        memory_service.add_message_to_conversation(
            content=body,
            sender_person_id=person_id,
            execution_id=execution_id,
            participant_person_ids=get_all_person_ids_fn(),
            role="user",
            node_id=node["id"],
            node_label=node.get("data", {}).get("label", "PersonJob"),
            token_count=int(len(body.split()) * 1.3),
            cost=0.0
        )

    # Call the LLM
    result = await llm_service.call_llm(
        messages=messages,
        service=service,
        model=model_name,
        # temperature=temperature,
        api_key_id=api_key_id,
        system_prompt=person.get("systemPrompt") or person.get("system", ""),
    )

    result_text = result.get("response", "")
    cost = result.get("cost", 0.0)
    token_count = len(result_text.split()) * 1.3

    # Add assistant response to memory
    memory_service.add_message_to_conversation(
        content=result_text,
        sender_person_id=person_id,
        execution_id=execution_id,
        participant_person_ids=get_all_person_ids_fn(),
        role="assistant",
        node_id=node["id"],
        node_label=node.get("data", {}).get("label", "PersonJob"),
        token_count=int(token_count),
        cost=cost
    )

    # Send status update
    await send_status_update_fn(
        "message_added", node["id"],
        message={
            "content": result_text,
            "sender_person_id": person_id,
            "timestamp": datetime.now().isoformat(),
            "node_id": node["id"],
            "node_label": node.get("data", {}).get("label"),
            "cost": cost,
            "token_count": int(token_count)
        }
    )

    # Build the complete conversation history for output
    # This includes both incoming conversation and the new exchange
    output_conversation = []
    if incoming_conversation:
        output_conversation.extend(incoming_conversation)
    if body.strip():
        output_conversation.append({"role": "user", "content": body})
    output_conversation.append({"role": "assistant", "content": result_text})

    # Return a structured output that includes the text and complete conversation
    output = OutputProcessor.create_personjob_output(
        text=result_text,
        conversation_history=output_conversation,  # Pass the full conversation
        cost=cost or 0.0,
        model=model_name
    )
    output["person_id"] = person_id

    return output, cost or 0.0


async def _find_default_api_key(service: str) -> Optional[str]:
    """Find default API key for service."""
    from ..services.api_key_service import APIKeyService
    api_key_service = APIKeyService()
    keys = api_key_service.list_api_keys()
    for key in keys:
        if key["service"] == service:
            return key["id"]
    return None