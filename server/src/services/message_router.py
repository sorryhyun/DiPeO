import asyncio
import json
import os
from typing import Dict, Callable, Optional, Any
import redis.asyncio as redis
from redis.asyncio.client import PubSub
import logging

logger = logging.getLogger(__name__)


class MessageRouter:
    """Routes messages between workers using Redis streams and pub/sub"""
    
    def __init__(self, redis_url: Optional[str] = None):
        self.redis_url = redis_url or os.getenv('REDIS_URL', 'redis://localhost:6379/0')
        self.worker_id = f"worker_{os.getpid()}"
        self.redis_client: Optional[redis.Redis] = None
        self.pubsub: Optional[PubSub] = None
        self.local_handlers: Dict[str, Callable] = {}
        self._consumer_task: Optional[asyncio.Task] = None
        self._initialized = False
        
    async def initialize(self):
        """Initialize Redis connections and start message consumer"""
        if self._initialized:
            return
            
        try:
            self.redis_client = await redis.from_url(
                self.redis_url,
                encoding="utf-8",
                decode_responses=True
            )
            
            # Test connection
            await self.redis_client.ping()
            
            # Create pubsub connection for worker-specific channels
            self.pubsub = self.redis_client.pubsub()
            await self.pubsub.subscribe(f"worker:{self.worker_id}")
            
            # Register this worker
            await self._register_worker()
            
            # Start consuming messages
            self._consumer_task = asyncio.create_task(self._consume_messages())
            
            self._initialized = True
            logger.info(f"MessageRouter initialized for {self.worker_id}")
            
        except (redis.ConnectionError, redis.RedisError) as e:
            logger.error(f"Failed to initialize Redis: {e}")
            self.redis_client = None
            self.pubsub = None
            
    async def cleanup(self):
        """Clean up Redis connections and stop consumer"""
        if self._consumer_task:
            self._consumer_task.cancel()
            try:
                await self._consumer_task
            except asyncio.CancelledError:
                pass
                
        if self.pubsub:
            await self.pubsub.unsubscribe()
            await self.pubsub.close()
            
        if self.redis_client:
            await self._unregister_worker()
            await self.redis_client.close()
            
        self._initialized = False
        
    async def register_connection(self, connection_id: str, handler: Callable):
        """Register a WebSocket connection on this worker"""
        if not self.redis_client:
            # Fallback to local-only mode
            self.local_handlers[connection_id] = handler
            return
            
        # Store connection metadata in Redis
        await self.redis_client.hset(
            f"conn:{connection_id}",
            mapping={
                "worker_id": self.worker_id,
                "timestamp": str(asyncio.get_event_loop().time())
            }
        )
        
        # Set expiration (1 hour)
        await self.redis_client.expire(f"conn:{connection_id}", 3600)
        
        # Store local handler
        self.local_handlers[connection_id] = handler
        
        logger.debug(f"Registered connection {connection_id} on {self.worker_id}")
        
    async def unregister_connection(self, connection_id: str):
        """Unregister a WebSocket connection"""
        # Remove local handler
        self.local_handlers.pop(connection_id, None)
        
        if self.redis_client:
            # Remove from Redis
            await self.redis_client.delete(f"conn:{connection_id}")
            
        logger.debug(f"Unregistered connection {connection_id}")
        
    async def route_to_connection(self, connection_id: str, message: dict) -> bool:
        """Route a message to a specific connection, regardless of which worker owns it"""
        # Check if connection is local
        if connection_id in self.local_handlers:
            await self._local_deliver(connection_id, message)
            return True
            
        if not self.redis_client:
            logger.warning(f"Cannot route to {connection_id}: Redis not available")
            return False
            
        # Find which worker owns this connection
        conn_info = await self.redis_client.hgetall(f"conn:{connection_id}")
        if not conn_info:
            logger.warning(f"Connection {connection_id} not found in registry")
            return False
            
        target_worker = conn_info.get("worker_id")
        if target_worker == self.worker_id:
            # This shouldn't happen, but handle it
            await self._local_deliver(connection_id, message)
            return True
            
        # Route through Redis pub/sub
        channel = f"worker:{target_worker}"
        payload = json.dumps({
            "connection_id": connection_id,
            "message": message
        })
        
        await self.redis_client.publish(channel, payload)
        logger.debug(f"Routed message to {connection_id} via {target_worker}")
        return True
        
    async def broadcast_to_execution(self, execution_id: str, message: dict):
        """Broadcast a message to all connections subscribed to an execution"""
        if not self.redis_client:
            # In local mode, broadcast to all local connections
            # This is a simplified implementation
            for handler in self.local_handlers.values():
                try:
                    await handler(message)
                except Exception as e:
                    logger.error(f"Error broadcasting message: {e}")
            return
            
        # Get all connections subscribed to this execution
        # This requires maintaining a subscription registry
        subscription_key = f"exec_subs:{execution_id}"
        connection_ids = await self.redis_client.smembers(subscription_key)
        
        # Route to each connection
        tasks = []
        for conn_id in connection_ids:
            tasks.append(self.route_to_connection(conn_id, message))
            
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
            
    async def subscribe_connection_to_execution(self, connection_id: str, execution_id: str):
        """Subscribe a connection to execution updates"""
        if self.redis_client:
            await self.redis_client.sadd(f"exec_subs:{execution_id}", connection_id)
            # Set expiration
            await self.redis_client.expire(f"exec_subs:{execution_id}", 3600)
            
    async def unsubscribe_connection_from_execution(self, connection_id: str, execution_id: str):
        """Unsubscribe a connection from execution updates"""
        if self.redis_client:
            await self.redis_client.srem(f"exec_subs:{execution_id}", connection_id)
            
    async def _local_deliver(self, connection_id: str, message: dict):
        """Deliver a message to a local connection"""
        handler = self.local_handlers.get(connection_id)
        if handler:
            try:
                await handler(message)
            except Exception as e:
                logger.error(f"Error delivering message to {connection_id}: {e}")
                # Remove dead connection
                await self.unregister_connection(connection_id)
        else:
            logger.warning(f"No local handler for {connection_id}")
            
    async def _consume_messages(self):
        """Consume messages from Redis pub/sub"""
        if not self.pubsub:
            return
            
        try:
            async for message in self.pubsub.listen():
                if message["type"] == "message":
                    try:
                        data = json.loads(message["data"])
                        connection_id = data["connection_id"]
                        msg = data["message"]
                        
                        await self._local_deliver(connection_id, msg)
                        
                    except (json.JSONDecodeError, KeyError) as e:
                        logger.error(f"Invalid message format: {e}")
                        
        except asyncio.CancelledError:
            raise
        except Exception as e:
            logger.error(f"Error in message consumer: {e}")
            
    async def _register_worker(self):
        """Register this worker in Redis"""
        if self.redis_client:
            await self.redis_client.sadd("active_workers", self.worker_id)
            await self.redis_client.hset(
                f"worker:{self.worker_id}",
                mapping={
                    "pid": str(os.getpid()),
                    "started": str(asyncio.get_event_loop().time())
                }
            )
            
    async def _unregister_worker(self):
        """Unregister this worker from Redis"""
        if self.redis_client:
            await self.redis_client.srem("active_workers", self.worker_id)
            await self.redis_client.delete(f"worker:{self.worker_id}")
            
            # Clean up any connections owned by this worker
            cursor = 0
            while True:
                cursor, keys = await self.redis_client.scan(
                    cursor, 
                    match="conn:*",
                    count=100
                )
                
                for key in keys:
                    conn_info = await self.redis_client.hgetall(key)
                    if conn_info.get("worker_id") == self.worker_id:
                        await self.redis_client.delete(key)
                        
                if cursor == 0:
                    break


# Global instance (will be initialized per worker)
message_router = MessageRouter()