"""Unified SSE endpoints using MessageRouter as the event source."""

import json
import logging

from fastapi import APIRouter, Request, Response
from sse_starlette.sse import EventSourceResponse

from dipeo.application.registry import ServiceRegistry, ServiceKey
from dipeo.core.ports import MessageRouterPort
from dipeo.infrastructure.adapters.messaging.sse_adapter import SSEMessageRouterAdapter

logger = logging.getLogger(__name__)

# Service key for message router
MESSAGE_ROUTER = ServiceKey[MessageRouterPort]("message_router")

router = APIRouter(prefix="/sse")


@router.get("/executions/{execution_id}")
async def stream_execution(
    execution_id: str,
    request: Request,
    response: Response,
):
    """Stream execution updates via Server-Sent Events.
    
    This unified endpoint uses MessageRouter as the single source of truth
    for all execution events, regardless of whether they originated from
    CLI or Web executions.
    """
    # Get the application container from request state
    from dipeo_server.app_context import get_container
    container = get_container()
    
    # Get message router from registry
    message_router = container.registry.get(MESSAGE_ROUTER)
    if not message_router:
        logger.error("MessageRouter not available for SSE streaming")
        return Response(
            content="MessageRouter not available",
            status_code=503,
        )
    
    # Create SSE adapter for this stream
    sse_adapter = SSEMessageRouterAdapter(message_router)
    
    async def event_generator():
        """Generate SSE events from MessageRouter via adapter."""
        try:
            async for event in sse_adapter.subscribe(execution_id):
                if await request.is_disconnected():
                    break
                yield event
                
        except Exception as e:
            logger.error(f"Error in SSE stream for {execution_id}: {e}")
            yield {"data": json.dumps({"error": str(e)})}
    
    return EventSourceResponse(
        event_generator(),
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Credentials": "true",
        },
    )


__all__ = ["router"]