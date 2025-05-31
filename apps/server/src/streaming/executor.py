"""Streaming diagram executor with real-time updates."""

import asyncio
import os
import sys
import traceback
from datetime import datetime
from typing import Dict, Optional, Any

# Add server root to path for config import
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
from ...config import CONVERSATION_LOG_DIR

from ..execution.core.execution_engine import ExecutionEngine
from ..services.memory_service import MemoryService
from .stream_manager import stream_manager


class StreamingDiagramExecutor:
    """Handles diagram execution with streaming updates."""
    
    def __init__(
        self,
        diagram: Dict[str, Any],
        memory_service: MemoryService,
    ):
        self.diagram = diagram
        self.memory_service = memory_service
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
            # Validate diagram has start nodes before creating executor
            nodes = self.diagram.get("nodes", [])
            has_start_node = any(node.get("type") == "startNode" for node in nodes)
            if not has_start_node:
                raise ValueError("No start nodes found in diagram. Add at least one start node to begin execution.")
            
            # Create the V2 execution engine
            from ..services.llm_service import LLMService
            from ..services.api_key_service import APIKeyService
            
            api_key_service = APIKeyService()
            llm_service = LLMService(api_key_service)
            
            executor = ExecutionEngine(
                diagram=self.diagram,
                memory_service=self.memory_service,
                llm_service=llm_service,
                streaming_update_callback=self.status_callback
            )
            self.execution_id = executor.context.execution_id
            
            # Create stream context
            self.stream_context = await stream_manager.create_stream(
                self.execution_id, 'sse'
            )

            await stream_manager.publish_update(self.execution_id, {
                "type": "execution_started",
                "execution_id": self.execution_id,
                "diagram": self.diagram,
                "timestamp": datetime.now().isoformat()
            })

            # Run the diagram
            context, total_cost = await executor.execute()
            
            # Save conversation log
            log_path = await self.memory_service.save_conversation_log(
                execution_id=executor.context.execution_id,
                log_dir=CONVERSATION_LOG_DIR
            )
            
            # Send completion update
            await stream_manager.publish_update(self.execution_id, {
                "type": "execution_complete",
                "context": context,
                "total_cost": total_cost,
                "memory_stats": executor.get_execution_summary(),
                "conversation_log": log_path
            })
            
            # Clear execution memory
            self.memory_service.clear_execution_memory(executor.context.execution_id)
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