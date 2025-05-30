"""Streaming diagram executor with real-time updates."""

import asyncio
import traceback
from datetime import datetime
from typing import Dict, Optional, Callable, Any

from ..utils.converter import DiagramMigrator
from ..run_graph import DiagramExecutor
from ..services.memory_service import MemoryService
from .stream_manager import stream_manager
from ...config import CONVERSATION_LOG_DIR


class StreamingDiagramExecutor:
    """Handles diagram execution with streaming updates."""
    
    def __init__(
        self,
        diagram: Dict[str, Any],
        memory_service: MemoryService,
        broadcast_to_websocket: bool = False
    ):
        self.diagram = DiagramMigrator.migrate(diagram)
        self.memory_service = memory_service
        self.broadcast_to_websocket = broadcast_to_websocket
        self.execution_id: Optional[str] = None
        self.stream_context = None
        self.completed = False
        self.error: Optional[Exception] = None
        
    async def status_callback(self, update: Dict[str, Any]) -> None:
        """Callback for publishing status updates."""
        if self.execution_id:
            await stream_manager.publish_update(self.execution_id, update)
    
    async def execute(self) -> None:
        """Execute the diagram with streaming updates."""
        try:
            # Create the diagram executor
            executor = DiagramExecutor(
                diagram=self.diagram,
                memory_service=self.memory_service,
                status_callback=self.status_callback
            )
            self.execution_id = executor.execution_id
            
            # Create stream context
            output_format = 'both' if self.broadcast_to_websocket else 'sse'
            self.stream_context = await stream_manager.create_stream(
                self.execution_id, output_format
            )
            
            # Broadcast execution start if needed
            if self.broadcast_to_websocket:
                await stream_manager.publish_update(self.execution_id, {
                    "type": "execution_started",
                    "execution_id": self.execution_id,
                    "diagram": self.diagram,
                    "timestamp": datetime.now().isoformat()
                })
            
            # Run the diagram
            context, total_cost = await executor.run()
            
            # Save conversation log
            log_path = await self.memory_service.save_conversation_log(
                execution_id=executor.execution_id,
                log_dir=CONVERSATION_LOG_DIR
            )
            
            # Send completion update
            await stream_manager.publish_update(self.execution_id, {
                "type": "execution_complete",
                "context": context,
                "total_cost": total_cost,
                "memory_stats": executor.get_memory_stats(),
                "conversation_log": log_path
            })
            
            # Clear execution memory
            self.memory_service.clear_execution_memory(executor.execution_id)
            self.completed = True
            
        except Exception as e:
            self.error = e
            if self.execution_id:
                await stream_manager.publish_update(self.execution_id, {
                    "type": "execution_error",
                    "error": str(e),
                    "traceback": traceback.format_exc()
                })
            self.completed = True
            
        finally:
            # Clean up stream resources
            if self.execution_id:
                await stream_manager.cleanup_stream(self.execution_id)
    
    def get_stream_queue(self):
        """Get the SSE queue for this execution."""
        if self.execution_id:
            return stream_manager.get_stream_queue(self.execution_id)
        return None
    
    async def wait_for_stream_ready(self, timeout: float = 5.0) -> bool:
        """Wait for the stream to be ready."""
        start_time = asyncio.get_event_loop().time()
        while self.execution_id is None or self.get_stream_queue() is None:
            if asyncio.get_event_loop().time() - start_time > timeout:
                return False
            await asyncio.sleep(0.01)
        return True