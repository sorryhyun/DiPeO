
import logging
from typing import Any, Dict, List, Tuple, Optional
from datetime import datetime
from collections import Counter

from apps.server.src.services.memory_service import MemoryService
from apps.server.src.services.llm_service import LLMService
from .resolve_utils import render_prompt

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
    
    context["skipped_max_iter"] = False

    forget_mode = data.get("memoryForget") or data.get("memory", "none")
    if forget_mode == "all":
        memory_service.forget_for_person(person_id)
    elif forget_mode == "current_execution":
        memory_service.forget_for_person(person_id, execution_id)

    conversation_history = memory_service.get_conversation_history(person_id)

    first_prompt = data.get("firstOnlyPrompt") or data.get("first_prompt")
    default_prompt = data.get("defaultPrompt") or data.get("prompt")
    template = (
        first_prompt if iteration == 1 and first_prompt else default_prompt
    )

    logger.debug(f"[PersonJob {person_id}] Iteration: {iteration}, vars_map: {vars_map}")

    if data.get("contextCleaningRule") == "on_every_turn":
        preamble_parts = []
    else:
        preamble_parts: list[str] = []
        for e in incoming_arrows:
            if e.get("data", {}).get("contentType") in {"file", "whole"}:
                src_value = context.get(arrow_src_fn(e))
                if src_value is not None:
                    # Handle PersonJob output
                    if isinstance(src_value, dict) and src_value.get('_type') == 'personjob_output':
                        preamble_parts.append(str(src_value.get('text', '')))
                    else:
                        preamble_parts.append(str(src_value))

    body = render_prompt(template, vars_map)

    messages = []
    if conversation_history:
        messages.extend(conversation_history)
    if body.strip():
        messages.append({"role": "user", "content": body})

    prompt = "\n\n".join(preamble_parts + [body]) if preamble_parts else body
    logger.debug(f"[PersonJob {person_id}] Prompt: {prompt}")
    logger.debug(f"[PersonJob {person_id}] Conversation history: {len(conversation_history)} messages")

    model_name = person.get("modelName") or person.get("model")
    service = person.get("service")
    api_key_id = person.get("apiKeyId")

    if not service and model_name:
        if "gpt" in model_name.lower():
            service = "chatgpt"
            if not api_key_id:
                api_key_id = await _find_default_api_key(service)

    if model_name == "gpt-4.1-nano":
        model_name = "gpt-4.1-nano-2025-04-14"

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

    result_text, cost = await llm_service.call_llm(
        service,
        api_key_id,
        model_name,
        messages if conversation_history else prompt,
        person.get("systemPrompt") or person.get("system", ""),
    )

    token_count = len(result_text.split()) * 1.3

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

    # Return a structured output that includes the text and metadata
    output = {
        "text": result_text,
        "person_id": person_id,
        "conversation_history": memory_service.get_conversation_history(person_id),
        "_type": "personjob_output"
    }
    
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