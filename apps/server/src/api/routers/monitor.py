from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse
import asyncio
import json
from typing import AsyncGenerator
from ...streaming.stream_manager import stream_manager

router = APIRouter(prefix="/api", tags=["monitor"])


@router.get("/monitor/stream")
async def monitor_stream(request: Request):
    """SSE endpoint for monitoring all diagram executions."""

    async def event_generator() -> AsyncGenerator[str, None]:
        monitor_id = f"monitor-{id(request)}"

        # Add this monitor to stream manager
        queue = await stream_manager.add_monitor(monitor_id)

        try:
            # Send initial connection
            yield f"data: {json.dumps({'type': 'monitor_connected', 'monitor_id': monitor_id})}\n\n"

            while True:
                # Check if client disconnected
                if await request.is_disconnected():
                    break

                try:
                    # Get update with timeout for heartbeat
                    update = await asyncio.wait_for(queue.get(), timeout=30.0)
                    yield f"data: {json.dumps(update)}\n\n"
                except asyncio.TimeoutError:
                    # Send heartbeat
                    yield ": heartbeat\n\n"

        finally:
            # Cleanup
            await stream_manager.remove_monitor(monitor_id)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )