"""Server-Sent Events (SSE) endpoints for monitoring stream."""

import asyncio
import json
import logging

from dipeo.application.execution.observers import MonitoringStreamObserver
from fastapi import APIRouter, Request, Response
from sse_starlette.sse import EventSourceResponse

logger = logging.getLogger(__name__)

_streaming_observers: dict[str, MonitoringStreamObserver] = {}
_observers_lock = asyncio.Lock()

router = APIRouter(prefix="/sse")


async def get_or_create_observer(execution_id: str) -> MonitoringStreamObserver:
    """Get existing observer or create a new one."""
    async with _observers_lock:
        if execution_id not in _streaming_observers:
            _streaming_observers[execution_id] = MonitoringStreamObserver()
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
    observer = await get_or_create_observer(execution_id)

    async def event_generator():
        """Generate SSE events from observer."""
        try:
            async for event in observer.subscribe(execution_id):
                if await request.is_disconnected():
                    break
                yield event

        except Exception as e:
            logger.error(f"Error in SSE stream for {execution_id}: {e}")
            yield {"data": json.dumps({"error": str(e)})}
        finally:
            pass  # Suppress verbose SSE connection logs

    return EventSourceResponse(
        event_generator(),
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Credentials": "true",
        },
    )


def register_observer_for_execution(
    execution_id: str, observer: MonitoringStreamObserver
):
    """Register an observer for a specific execution.

    This is called by the execution use case when using monitoring stream.
    """

    async def _register():
        async with _observers_lock:
            _streaming_observers[execution_id] = observer

    try:
        loop = asyncio.get_running_loop()
        loop.create_task(_register())
    except RuntimeError:
        asyncio.run(_register())


__all__ = ["register_observer_for_execution", "router"]
