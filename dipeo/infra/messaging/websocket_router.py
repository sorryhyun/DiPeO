import asyncio
import logging
import threading
import time
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime

logger = logging.getLogger(__name__)

@dataclass
class ConnectionHealth:
    last_successful_send: float
    failed_attempts: int = 0
    total_messages: int = 0
    avg_latency: float = 0.0


class MessageRouter:
    def __init__(self):
        self.worker_id = "single-worker"
        self.local_handlers: dict[str, Callable] = {}
        self.execution_subscriptions: dict[str, set[str]] = {}
        self._initialized = False
        self.connection_health: dict[str, ConnectionHealth] = {}
        self._message_queue_size: dict[str, int] = {}
        self._queue_lock = threading.Lock()
        self.max_queue_size = 100

    async def initialize(self):
        if self._initialized:
            return

        self._initialized = True

    async def cleanup(self):
        self.local_handlers.clear()
        self.execution_subscriptions.clear()
        self._initialized = False

    async def register_connection(self, connection_id: str, handler: Callable):
        self.local_handlers[connection_id] = handler
        self.connection_health[connection_id] = ConnectionHealth(
            last_successful_send=time.time()
        )
        self._message_queue_size[connection_id] = 0

    async def unregister_connection(self, connection_id: str):
        self.local_handlers.pop(connection_id, None)
        self.connection_health.pop(connection_id, None)
        self._message_queue_size.pop(connection_id, None)

        for exec_id, connections in list(self.execution_subscriptions.items()):
            connections.discard(connection_id)
            if not connections:
                del self.execution_subscriptions[exec_id]

    async def route_to_connection(self, connection_id: str, message: dict) -> bool:
        handler = self.local_handlers.get(connection_id)
        if not handler:
            logger.warning(f"No handler for connection {connection_id}")
            return False
            
        # Check backpressure with thread-safe operations
        with self._queue_lock:
            queue_size = self._message_queue_size.get(connection_id, 0)
            if queue_size > self.max_queue_size:
                logger.warning(f"Connection {connection_id} queue full ({queue_size} messages), applying backpressure")
                return False
            self._message_queue_size[connection_id] = queue_size + 1
            
        start_time = time.time()
        try:
            await handler(message)
            
            # Update health metrics
            latency = time.time() - start_time
            health = self.connection_health.get(connection_id)
            if health:
                health.last_successful_send = time.time()
                health.total_messages += 1
                health.avg_latency = ((health.avg_latency * (health.total_messages - 1)) + latency) / health.total_messages
                health.failed_attempts = 0
            
            return True
        except Exception as e:
            logger.error(f"Error delivering message to {connection_id}: {e}")
            
            # Update failure metrics
            health = self.connection_health.get(connection_id)
            if health:
                health.failed_attempts += 1
                if health.failed_attempts > 3:
                    logger.error(f"Connection {connection_id} exceeded failure threshold, unregistering")
                    await self.unregister_connection(connection_id)
            
            return False
        finally:
            with self._queue_lock:
                self._message_queue_size[connection_id] = max(0, self._message_queue_size.get(connection_id, 1) - 1)

    async def broadcast_to_execution(self, execution_id: str, message: dict):
        start_time = time.time()
        
        # First, check if we need to publish to streaming_manager (for GraphQL subscriptions)
        # This is imported at runtime to avoid circular imports
        try:
            from dipeo_server.api.graphql.subscriptions import publish_execution_update

            await publish_execution_update(execution_id, message)
        except ImportError:
            # We're not in server context, just continue with WebSocket broadcasting
            pass
        except Exception as e:
            logger.error(f"Failed to publish to streaming manager: {e}")

        # Then broadcast to WebSocket connections
        connection_ids = self.execution_subscriptions.get(execution_id, set())

        if not connection_ids:
            # Silently return - no need to log this every time
            return

        # Use TaskGroup for better structured concurrency and error handling
        successful_broadcasts = 0
        failed_broadcasts = 0
        
        # Check Python version for TaskGroup support
        import sys
        if sys.version_info >= (3, 11):
            # Use TaskGroup for Python 3.11+
            try:
                async def track_broadcast(connection_id: str, msg: dict):
                    broadcast_result = await self._broadcast_with_metrics(connection_id, msg)
                    return connection_id, broadcast_result
                
                results = []
                async with asyncio.TaskGroup() as tg:
                    for conn_id in list(connection_ids):
                        task = tg.create_task(track_broadcast(conn_id, message))
                        results.append(task)
                
                # Count successes after all tasks complete
                for task in results:
                    try:
                        conn_id, success = task.result()
                        if success:
                            successful_broadcasts += 1
                        else:
                            failed_broadcasts += 1
                    except Exception as e:
                        logger.error(f"Broadcast error: {e}")
                        failed_broadcasts += 1
                        
            except Exception as e:
                # Handle any TaskGroup errors
                logger.error(f"TaskGroup error during broadcast: {e}")
                failed_broadcasts = len(connection_ids)
        else:
            # Fallback for Python < 3.11
            tasks = []
            for conn_id in list(connection_ids):
                tasks.append(self._broadcast_with_metrics(conn_id, message))
            
            if tasks:
                results = await asyncio.gather(*tasks, return_exceptions=True)
                for result in results:
                    if isinstance(result, Exception):
                        logger.error(f"Failed to broadcast to connection: {result}")
                        failed_broadcasts += 1
                    elif result:
                        successful_broadcasts += 1
        
        # Log performance metrics
        broadcast_time = time.time() - start_time
        if broadcast_time > 0.1:  # Log slow broadcasts
            logger.warning(
                f"Slow broadcast to execution {execution_id}: "
                f"{broadcast_time:.2f}s for {len(connection_ids)} connections "
                f"(success: {successful_broadcasts}, failed: {failed_broadcasts})"
            )
    
    async def _broadcast_with_metrics(self, conn_id: str, message: dict) -> bool:
        """Helper method to broadcast with metrics tracking"""
        result = await self.route_to_connection(conn_id, message)
        return result

    async def subscribe_connection_to_execution(
        self, connection_id: str, execution_id: str
    ):
        if execution_id not in self.execution_subscriptions:
            self.execution_subscriptions[execution_id] = set()

        self.execution_subscriptions[execution_id].add(connection_id)

    async def unsubscribe_connection_from_execution(
        self, connection_id: str, execution_id: str
    ):
        if execution_id in self.execution_subscriptions:
            self.execution_subscriptions[execution_id].discard(connection_id)

            if not self.execution_subscriptions[execution_id]:
                del self.execution_subscriptions[execution_id]

    def get_stats(self) -> dict:
        now = time.time()
        unhealthy_connections = [
            conn_id for conn_id, health in self.connection_health.items()
            if now - health.last_successful_send > 60  # No successful send in 60s
        ]
        
        avg_queue_size = (
            sum(self._message_queue_size.values()) / len(self._message_queue_size)
            if self._message_queue_size else 0
        )
        
        return {
            "worker_id": self.worker_id,
            "active_connections": len(self.local_handlers),
            "active_executions": len(self.execution_subscriptions),
            "total_subscriptions": sum(
                len(conns) for conns in self.execution_subscriptions.values()
            ),
            "unhealthy_connections": len(unhealthy_connections),
            "avg_queue_size": round(avg_queue_size, 2),
            "connection_health": {
                conn_id: {
                    "last_send": datetime.fromtimestamp(health.last_successful_send).isoformat(),
                    "failed_attempts": health.failed_attempts,
                    "total_messages": health.total_messages,
                    "avg_latency_ms": round(health.avg_latency * 1000, 2)
                }
                for conn_id, health in self.connection_health.items()
            }
        }


message_router = MessageRouter()
