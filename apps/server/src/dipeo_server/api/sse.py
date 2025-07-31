"""Server-Sent Events (SSE) endpoints for direct streaming."""

import asyncio
import logging
from typing import Dict, Optional

from fastapi import APIRouter, Request, Response
from fastapi.responses import StreamingResponse
from sse_starlette.sse import EventSourceResponse

from dipeo.application.execution.observers import DirectStreamingObserver
from dipeo_server.app_context import get_container

logger = logging.getLogger(__name__)

# Global registry for active streaming observers
_streaming_observers: Dict[str, DirectStreamingObserver] = {}
_observers_lock = asyncio.Lock()

router = APIRouter(prefix="/sse")


async def get_or_create_observer(execution_id: str) -> DirectStreamingObserver:
    """Get existing observer or create a new one."""
    async with _observers_lock:
        if execution_id not in _streaming_observers:
            _streaming_observers[execution_id] = DirectStreamingObserver()
        return _streaming_observers[execution_id]


async def remove_observer(execution_id: str):
    """Remove observer when no longer needed."""
    async with _observers_lock:
        _streaming_observers.pop(execution_id, None)


@router.get("/executions/{execution_id}")
async def stream_execution(
    execution_id: str,
    request: Request,
    response: Response,
):
    """Stream execution updates via Server-Sent Events.

    This endpoint allows browsers to directly connect and receive
    real-time execution updates without going through WebSocket/message router.
    """
    logger.info(f"SSE connection established for execution {execution_id}")

    # Get or create observer for this execution
    observer = await get_or_create_observer(execution_id)

    async def event_generator():
        """Generate SSE events from observer."""
        try:
            # Subscribe to events
            async for event in observer.subscribe(execution_id):
                # Check if client disconnected
                if await request.is_disconnected():
                    break
                yield event

        except Exception as e:
            logger.error(f"Error in SSE stream for {execution_id}: {e}")
            yield f"event: error\ndata: {{'error': '{str(e)}'}}\n\n"
        finally:
            logger.info(f"SSE connection closed for execution {execution_id}")

    # Return SSE response
    return EventSourceResponse(
        event_generator(),
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",  # Disable Nginx buffering
        },
    )


def register_observer_for_execution(
    execution_id: str, observer: DirectStreamingObserver
):
    """Register an observer for a specific execution.

    This is called by the execution use case when using direct streaming.
    """

    async def _register():
        async with _observers_lock:
            _streaming_observers[execution_id] = observer

    # Run in event loop if needed
    try:
        loop = asyncio.get_running_loop()
        loop.create_task(_register())
    except RuntimeError:
        # No event loop, create one
        asyncio.run(_register())


# Export for use in execution
__all__ = ["router", "register_observer_for_execution"]
