"""
Monitor router for real-time execution monitoring via SSE.
"""

import asyncio
import json
import uuid
from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse
from typing import Set, Dict, Any
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/monitor", tags=["monitor"])

# Global sets to track active monitor connections
active_monitors: Set[str] = set()
monitor_queues: Dict[str, asyncio.Queue] = {}


async def broadcast_to_monitors(event_data: Dict[str, Any]):
    """Broadcast an event to all active monitor connections (SSE and WebSocket)."""
    # Try to broadcast to WebSocket clients as well
    try:
        from .websocket import get_connection_manager
        ws_manager = get_connection_manager()
        # Broadcast to all WebSocket clients
        await ws_manager.broadcast(event_data)
    except Exception as e:
        # If WebSocket module is not available or error occurs, continue with SSE only
        logger.debug(f"WebSocket broadcast skipped: {e}")
    
    if not active_monitors:
        return
    
    # Log the event data being broadcast for debugging
    logger.info(f"Broadcasting to {len(active_monitors)} SSE monitors. Event type: {event_data.get('type')}, node_id: {event_data.get('node_id')}")
    
    # Add monitor flag to distinguish from direct execution events
    event_data["from_monitor"] = True
    message = f"data: {json.dumps(event_data)}\n\n"
    
    # Send to all active monitors
    disconnected_monitors = set()
    for monitor_id in active_monitors.copy():
        try:
            queue = monitor_queues.get(monitor_id)
            if queue:
                await queue.put(message)
            else:
                disconnected_monitors.add(monitor_id)
        except Exception as e:
            logger.warning(f"Failed to send to monitor {monitor_id}: {e}")
            disconnected_monitors.add(monitor_id)
    
    # Clean up disconnected monitors
    for monitor_id in disconnected_monitors:
        active_monitors.discard(monitor_id)
        monitor_queues.pop(monitor_id, None)


async def monitor_event_generator(monitor_id: str):
    """Generate SSE events for a specific monitor connection."""
    queue = asyncio.Queue()
    monitor_queues[monitor_id] = queue
    active_monitors.add(monitor_id)
    
    try:
        # Send initial connection event
        yield f"data: {json.dumps({'type': 'monitor_connected', 'monitor_id': monitor_id})}\n\n"
        
        # Send heartbeat and queued events
        while True:
            try:
                # Wait for events with timeout for heartbeat
                message = await asyncio.wait_for(queue.get(), timeout=30.0)
                yield message
            except asyncio.TimeoutError:
                # Send heartbeat to keep connection alive
                yield f"data: {json.dumps({'type': 'heartbeat', 'timestamp': asyncio.get_event_loop().time()})}\n\n"
    except asyncio.CancelledError:
        logger.info(f"Monitor {monitor_id} connection cancelled")
    except Exception as e:
        logger.error(f"Monitor {monitor_id} error: {e}")
    finally:
        # Clean up on disconnection
        active_monitors.discard(monitor_id)
        monitor_queues.pop(monitor_id, None)
        logger.info(f"Monitor {monitor_id} disconnected")




@router.get("/status")
async def monitor_status():
    """Get current monitoring status."""
    return {
        "active_monitors": len(active_monitors),
        "monitor_ids": list(active_monitors)
    }


@router.post("/broadcast")
async def broadcast_event(event_data: dict):
    """
    Broadcast an event to all monitor connections.
    
    Used by CLI and external executions to notify browser monitors.
    """
    try:
        # Mark as external execution
        event_data["is_external"] = True
        await broadcast_to_monitors(event_data)
        return {
            "success": True,
            "broadcasted_to": len(active_monitors),
            "message": "Event broadcasted to all monitors"
        }
    except Exception as e:
        logger.error(f"Failed to broadcast event: {e}")
        return {
            "success": False,
            "error": str(e)
        }


# Export broadcast function for use by execution engine
__all__ = ["router", "broadcast_to_monitors"]