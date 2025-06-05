from fastapi import APIRouter, Depends, Query
from typing import Optional
from datetime import datetime

from ...services.memory_service import MemoryService
from ...utils.dependencies import get_memory_service
from ...engine.errors import handle_api_errors

router = APIRouter(prefix="/api/conversations", tags=["conversations"])


@router.get("/")
@handle_api_errors
async def get_conversations(
    personId: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    search: Optional[str] = Query(None),
    executionId: Optional[str] = Query(None),
    showForgotten: bool = Query(False),
    startTime: Optional[str] = Query(None),
    endTime: Optional[str] = Query(None),
    since: Optional[str] = Query(None),
    memory_service: MemoryService = Depends(get_memory_service)
):
    """Get conversation data with pagination and filtering."""
    persons_data = {}

    if personId:
        person_ids = [personId]
    else:
        person_ids = memory_service.get_all_participants_in_conversation()

    for pid in person_ids:
        person_memory = memory_service.get_or_create_person_memory(pid)

        filtered_messages = []
        for msg in person_memory.messages:
            if not showForgotten and msg.id in person_memory.forgotten_message_ids:
                continue

            if search and search.lower() not in msg.content.lower():
                continue

            if executionId and msg.execution_id != executionId:
                continue

            if startTime:
                start_dt = datetime.fromisoformat(startTime)
                if msg.timestamp < start_dt:
                    continue

            if endTime:
                end_dt = datetime.fromisoformat(endTime)
                if msg.timestamp > end_dt:
                    continue

            if since:
                since_dt = datetime.fromisoformat(since)
                if msg.timestamp <= since_dt:
                    continue

            filtered_messages.append(msg)

        filtered_messages.sort(key=lambda m: m.timestamp)

        paginated_messages = filtered_messages[offset:offset + limit]

        formatted_messages = []
        for msg in paginated_messages:
            formatted_msg = msg.to_dict()

            if hasattr(msg, 'node_id'):
                formatted_msg['node_id'] = msg.node_id
                formatted_msg['node_label'] = msg.node_label

            if hasattr(msg, 'token_count'):
                formatted_msg['token_count'] = msg.token_count
            if hasattr(msg, 'input_tokens'):
                formatted_msg['input_tokens'] = msg.input_tokens
            if hasattr(msg, 'output_tokens'):
                formatted_msg['output_tokens'] = msg.output_tokens
            if hasattr(msg, 'cached_tokens'):
                formatted_msg['cached_tokens'] = msg.cached_tokens

            formatted_messages.append(formatted_msg)

        persons_data[pid] = {
            "person_id": pid,
            "messages": formatted_messages,
            "total_messages": len(person_memory.messages),
            "visible_messages": len([m for m in person_memory.messages
                                     if m.id not in person_memory.forgotten_message_ids]),
            "forgotten_messages": len(person_memory.forgotten_message_ids),
            "has_more": len(filtered_messages) > offset + limit
        }

    return {"persons": persons_data}


@router.delete("/")
@handle_api_errors
async def clear_conversations(
    memory_service: MemoryService = Depends(get_memory_service)
):
    """Clear all conversation memory."""
    memory_service.clear_all_memory()
    return {"success": True, "message": "All conversations cleared"}